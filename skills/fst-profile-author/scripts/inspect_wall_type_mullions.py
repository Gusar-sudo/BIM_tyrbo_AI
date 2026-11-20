# -*- coding: utf-8 -*-
# Чтение: импосты/панели по умолчанию у типов витражей (имя содержит filter) и список типов импостов с подстрокой mfilter.
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
P = [("верх/низ гориз. граница 1", BuiltInParameter.AUTO_MULLION_BORDER1_HORIZ), ("гориз. граница 2", BuiltInParameter.AUTO_MULLION_BORDER2_HORIZ),
     ("верт. граница 1", BuiltInParameter.AUTO_MULLION_BORDER1_VERT), ("верт. граница 2", BuiltInParameter.AUTO_MULLION_BORDER2_VERT),
     ("внутр. гориз.", BuiltInParameter.AUTO_MULLION_INTERIOR_HORIZ), ("внутр. верт.", BuiltInParameter.AUTO_MULLION_INTERIOR_VERT),
     ("панель", BuiltInParameter.AUTO_PANEL_WALL), ("соединение", BuiltInParameter.AUTO_JOIN_CONDITION_WALL)]
out = {}
for wt in FilteredElementCollector(doc).OfClass(WallType):
    if wt.Kind != WallKind.Curtain or args["filter"] not in wt.Name:
        continue
    row = {}
    for lab, bip in P:
        p = wt.get_Parameter(bip)
        if p is None:
            continue
        if p.StorageType == StorageType.ElementId:
            e = doc.GetElement(p.AsElementId())
            row[lab] = e.Name if e else None
        else:
            row[lab] = p.AsValueString()
    out[wt.Name] = row
mts = sorted(m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() for m in FilteredElementCollector(doc).OfClass(MullionType)
             if args.get("mfilter", u"") in m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())
prof = {}
for m in FilteredElementCollector(doc).OfClass(MullionType):
    n = m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    if n in mts:
        pe = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
        prof[n] = pe.Family.Name if pe and hasattr(pe, "Family") else None
__output__ = {"status": "completed_unverified", "summary": "типов стен %d, импостов %d" % (len(out), len(mts)), "walls": out, "mullion_profiles": prof}
