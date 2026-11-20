# -*- coding: utf-8 -*-
# Чтение: собственные линии профиля (не вложенные): контуры и вершины. Модель не меняется. Аргументы: profiles
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
out = {}
for pn in args["profiles"]:
    pdoc = doc.EditFamily(fams[pn])
    try:
        rows = []
        for ce in FilteredElementCollector(pdoc).OfClass(CurveElement):
            c = ce.GeometryCurve
            if c is None:
                continue
            a = c.GetEndPoint(0); b = c.GetEndPoint(1)
            rows.append([ce.GetType().Name, c.GetType().Name, round(a.X * FT, 2), round(a.Y * FT, 2), round(b.X * FT, 2), round(b.Y * FT, 2),
                         ce.LineStyle.Name if hasattr(ce, "LineStyle") and ce.LineStyle else None])
        nested = [[fi.Symbol.Family.Name, fi.Symbol.Family.FamilyCategory.Name if fi.Symbol.Family.FamilyCategory else None] for fi in FilteredElementCollector(pdoc).OfClass(FamilyInstance)]
        out[pn.replace(u"BIMLIB_Профиль_", u"")] = {"curves": rows, "nested": nested, "cat": pdoc.OwnerFamily.FamilyCategory.Name}
    finally:
        pdoc.Close(False)
__output__ = {"status": "completed_unverified", "summary": "ok", "profiles": out}
