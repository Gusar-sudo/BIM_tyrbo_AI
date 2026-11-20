# -*- coding: utf-8 -*-
# Подготовка (include): PREP(doc, pa) — задать параметры типов по имени типа (для проб в откатываемой группе).
# pa: {"set": [{"type_name", "category" (OST_...), "param", "value_mm"}]}. Ключи ответа совместимы с apply_wall_band.py.
from Autodesk.Revit.DB import *


def PREP(doc, pa=None):
    pa = pa or {}
    out = {"loaded": 0, "load_fail": [], "swapped": [], "swap_fail": []}
    t = Transaction(doc, u"FT: параметры типов"); t.Start()
    for s in pa["set"]:
        els = [e for e in FilteredElementCollector(doc).OfCategory(getattr(BuiltInCategory, s["category"])).WhereElementIsElementType()
               if Element.Name.GetValue(e) == s["type_name"]]
        if len(els) != 1:
            out["swap_fail"].append([s["type_name"], u"найдено %d" % len(els)]); continue
        p = els[0].LookupParameter(s["param"])
        if p is None or p.IsReadOnly or not p.Set(float(s["value_mm"]) / 304.8):
            out["swap_fail"].append([s["type_name"], s["param"], u"не записано"]); continue
        out["swapped"].append([s["type_name"], s["param"], round(p.AsDouble() * 304.8, 2)])
    t.Commit()
    return out
