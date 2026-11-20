# -*- coding: utf-8 -*-
# Загрузить семейство двухслойной панели с жалюзи в активный проект (замена) и проверить.
#  overwrite_values: True — значения параметров из семейства (единственный способ сбросить значение по умолчанию
#    экземплярной галочки для НОВЫХ панелей; значения типов проекта при этом заменяются значениями семейства — поэтому
#    скрипт сравнивает все параметры типов до/после и показывает расхождения).
#  dry_run: True — всё откатывается (группа транзакций), отчёт тот же.
# Проверка: число экземпляров и типов, FT_Жалюзи у существующих панелей (не должны измениться), предупреждения,
#   разница параметров типов (без параметров жалюзи), значение галочки у новой пробной панели.
# Аргументы: rfa, family, overwrite_values, dry_run, probe_wall_type (для пробной панели)
import json, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
OVR = bool(args.get("overwrite_values", False)); DRY = bool(args.get("dry_run", True))


class _LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = OVR
        return True

    def OnSharedFamilyFound(self, a, b, src, c):
        src.Value = FamilySource.Family; c.Value = OVR
        return True


def fam():
    return [f for f in FilteredElementCollector(doc).OfClass(Family) if f.Name == args["family"]][0]


def type_values():
    out = {}
    for sid in fam().GetFamilySymbolIds():
        s = doc.GetElement(sid); d = {}
        for p in s.Parameters:
            n = p.Definition.Name
            if u"Жалюзи" in n or u"жалюзи" in n:
                continue
            try:
                d[n] = p.AsString() if p.StorageType == StorageType.String else p.AsValueString()
            except Exception:
                d[n] = None
        out[s.Name] = d
    return out


def state():
    sids = list(fam().GetFamilySymbolIds())
    inst = [p for p in FilteredElementCollector(doc).OfClass(FamilyInstance) if p.Symbol.Id in sids]
    vals = dict((p.Id.Value, p.LookupParameter(u"FT_Жалюзи").AsInteger() if p.LookupParameter(u"FT_Жалюзи") else None) for p in inst)
    return {"types": len(sids), "instances": len(inst), "blinds_on": sum(1 for v in vals.values() if v == 1),
            "warnings": len(doc.GetWarnings())}, vals


s0, v0 = state(); t0 = type_values()
res = {"before": s0, "overwrite_values": OVR, "dry_run": DRY}
tg = TransactionGroup(doc, u"FT: жалюзи (вложенные ламели)"); tg.Start()
try:
    t = Transaction(doc, u"FT: жалюзи — загрузка семейства"); t.Start()
    res["loaded"] = doc.LoadFamily(args["rfa"], _LO(), clr.Reference[Family]())
    res["commit"] = str(t.Commit())
    s1, v1 = state(); t1 = type_values()
    res["after"] = s1
    res["instance_values_changed"] = [i for i in v0 if v0[i] != v1.get(i)]
    diff = []
    for tn in sorted(set(t0) | set(t1)):
        a, b = t0.get(tn), t1.get(tn)
        if a is None or b is None:
            diff.append([tn, u"тип исчез" if b is None else u"тип новый"]); continue
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                diff.append([tn, k, a.get(k), b.get(k)])
    res["type_param_diff"] = diff
    if args.get("probe_wall_type"):
        t = Transaction(doc, u"проба"); t.Start()
        wt = [w for w in FilteredElementCollector(doc).OfClass(WallType) if w.Name == args["probe_wall_type"]][0]
        lv = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
        P0 = XYZ(60000 / FT, 900000 / FT, lv.Elevation)
        w = Wall.Create(doc, Line.CreateBound(P0, P0 + XYZ.BasisX * (1000 / FT)), wt.Id, lv.Id, 2400 / FT, 0, False, False)
        doc.Regenerate()
        p = doc.GetElement(list(w.CurtainGrid.GetPanelIds())[0])
        res["new_panel_FT_Жалюзи"] = p.LookupParameter(u"FT_Жалюзи").AsInteger() if p.LookupParameter(u"FT_Жалюзи") else None
        t.RollBack()
finally:
    if DRY:
        tg.RollBack()
    else:
        tg.Assimilate()
ok = res.get("commit") == "Committed" and res["after"]["instances"] == s0["instances"] and res["after"]["types"] == s0["types"] \
    and not res["instance_values_changed"] and res["after"]["warnings"] <= s0["warnings"] and res.get("new_panel_FT_Жалюзи", 0) == 0
__output__ = {"status": "completed_unverified" if ok else "partial",
              "summary": u"%s: экз. %d→%d, типов %d→%d, значения экз. изменились: %d, разница типов: %d, новая панель FT_Жалюзи=%s, предупр. %d→%d" % (
                  u"ПРОБНО (откат)" if DRY else u"ПРИМЕНЕНО", s0["instances"], res["after"]["instances"], s0["types"], res["after"]["types"],
                  len(res["instance_values_changed"]), len(res["type_param_diff"]), res.get("new_panel_FT_Жалюзи"), s0["warnings"], res["after"]["warnings"]),
              "result": res}
