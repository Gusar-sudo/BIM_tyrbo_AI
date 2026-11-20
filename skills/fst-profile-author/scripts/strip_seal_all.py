# -*- coding: utf-8 -*-
# Убрать нарисованный уплотнитель U5 (сплошные заливки <= max_mm во вложенных 2D) из ВСЕХ профилей импостов документа.
# Уплотнитель рисует панель по толщине стекла. EditFamily -> вложенные: удалить -> загрузить обратно -> SaveAs в out_dir.
# Проект НЕ меняется. Пишет args_out ({items:[{symbol_id, rfa}]}). Прогресс — checkpoint().
# Аргументы: out_dir, max_mm, prefix, args_out
import json, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MAX = float(args.get("max_mm", 12.0))
pref = args.get("prefix", u"BIMLIB_Профиль_")
if not os.path.isdir(args["out_dir"]):
    os.makedirs(args["out_dir"])


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


sids = set()
for mt in FilteredElementCollector(doc).OfClass(MullionType):
    p = mt.get_Parameter(BuiltInParameter.MULLION_PROFILE)
    if p and p.AsElementId() != ElementId.InvalidElementId:
        s = doc.GetElement(p.AsElementId())
        if s is not None and s.Family.Name.startswith(pref):
            sids.add(int(p.AsElementId().Value))
sids = sorted(sids)
items, errors, untouched = [], [], 0
for k, sid in enumerate(sids):
    sym = doc.GetElement(ElementId(sid))
    checkpoint(sym.Family.Name[:60], k, len(sids))
    pdoc = doc.EditFamily(sym.Family)
    removed = 0
    try:
        for fi in list(FilteredElementCollector(pdoc).OfClass(FamilyInstance)):
            ndoc = pdoc.EditFamily(fi.Symbol.Family)
            try:
                dele = List[ElementId]()
                for fr in FilteredElementCollector(ndoc).OfClass(FilledRegion):
                    ft = ndoc.GetElement(fr.GetTypeId())
                    fp = ndoc.GetElement(ft.ForegroundPatternId) if ft else None
                    if fp is None or not fp.GetFillPattern().IsSolidFill:
                        continue
                    xs, ys = [], []
                    for loop in fr.GetBoundaries():
                        for c in loop:
                            for pt in (c.GetEndPoint(0), c.GetEndPoint(1)):
                                xs.append(pt.X * FT); ys.append(pt.Y * FT)
                    if max(xs) - min(xs) <= MAX and max(ys) - min(ys) <= MAX:
                        dele.Add(fr.Id)
                if dele.Count > 0:
                    t = Transaction(ndoc, u"Убрать нарисованный уплотнитель"); t.Start(); ndoc.Delete(dele); t.Commit()
                    ndoc.LoadFamily(pdoc, LoadOpt())
                    removed += dele.Count
            finally:
                ndoc.Close(False)
        if removed:
            opts = SaveAsOptions(); opts.OverwriteExistingFile = True
            rfa = os.path.join(args["out_dir"], sym.Family.Name + u".rfa")
            pdoc.SaveAs(rfa, opts)
            items.append({"symbol_id": sid, "rfa": rfa, "removed": removed, "family": sym.Family.Name})
        else:
            untouched += 1
    except Exception as ex:
        errors.append([sym.Family.Name, str(ex)[:150]])
    finally:
        pdoc.Close(False)
with open(args["args_out"], "w", encoding="utf-8") as f:
    json.dump({"items": items}, f, ensure_ascii=False)
__output__ = {"status": "completed_unverified" if not errors else "partial",
              "summary": u"профилей всего %d, исправлено %d, без уплотнителя %d, ошибок %d; проект не изменён" % (len(sids), len(items), untouched, len(errors)),
              "removed_total": sum(i["removed"] for i in items), "errors": errors}
