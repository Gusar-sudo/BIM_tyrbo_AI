# -*- coding: utf-8 -*-
# Чтение: какие панели со стеклом (пересчёт glass_calc) не попали в спецификацию schedule_name, и почему —
# тип, наименование, завод, стадия, группа, вариант конструкции. Аргументы: schedule_name
import json, collections
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
sch = [v for v in FilteredElementCollector(doc).OfClass(ViewSchedule) if v.Name == a["schedule_name"]][0]
inside = set(e.Id.Value for e in FilteredElementCollector(doc, sch.Id).WhereElementIsNotElementType())
miss = collections.Counter(); sample = {}
for p in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
    t = doc.GetElement(p.GetTypeId())
    if not getattr(t, "FamilyName", "").startswith("BIMLIB") or p.Id.Value in inside:
        continue
    n = t.LookupParameter(u"FT_Стекло_Уплотнитель_Линий"); w = p.LookupParameter(u"FT_Стекло_Ширина")
    if not n or not w or n.AsDouble() <= 0 or w.AsDouble() <= 0:
        continue
    def s(par):
        q = p.LookupParameter(par) or t.LookupParameter(par)
        return (q.AsString() if q and q.StorageType == StorageType.String else (q.AsValueString() if q else None))
    host = p.Host
    k = u"%s | наим=%s | завод=%s | стадия=%s | группа=%s | вариант=%s | стена=%s" % (
        t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), s(u"ADSK_Наименование"), s(u"ADSK_Завод-изготовитель"),
        p.get_Parameter(BuiltInParameter.PHASE_CREATED).AsValueString(), p.GroupId.Value != -1,
        p.DesignOption.Name if p.DesignOption else u"-", host.Name if host else u"-")
    miss[k] += 1; sample.setdefault(k, p.Id.Value)
__output__ = {"status": "completed_unverified", "summary": u"в спецификации %d элементов; панелей со стеклом вне неё: %d" % (len(inside), sum(miss.values())),
              "missing": [{"what": k, "n": v, "sample_id": sample[k]} for k, v in miss.most_common()],
              "schedule_phase": sch.get_Parameter(BuiltInParameter.VIEW_PHASE).AsValueString() if sch.get_Parameter(BuiltInParameter.VIEW_PHASE) else None}
