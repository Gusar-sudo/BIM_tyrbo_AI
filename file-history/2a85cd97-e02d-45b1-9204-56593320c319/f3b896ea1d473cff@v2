# -*- coding: utf-8 -*-
# Только чтение: линии графики узла, выходящие за тело профиля по X (остатки снятых реек и т.п.).
# Для каждого семейства профиля (фильтр по подстрокам name_has): габарит тела (собственные линии) и линии вложенного,
# у которых хотя бы одна точка дальше края тела по X больше tol_mm. Координаты — профиля, мм.
# Аргументы: name_has (список подстрок), tol_mm (0.5)
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8; TOL = float(args.get("tol_mm", 0.5))
keys = args.get("name_has", [u"ГКЛ", u"Комбинированный"])
fams = [f for f in FilteredElementCollector(doc).OfClass(Family) if f.Name.startswith(u"BIMLIB_Профиль_") and any(k in f.Name for k in keys)]
rows = []
for i, f in enumerate(fams):
    checkpoint(f.Name, i, len(fams))
    pd = doc.EditFamily(f)
    try:
        own = [c.GeometryCurve for c in FilteredElementCollector(pd).OfClass(CurveElement) if c.GeometryCurve is not None]
        xs = [q.X * FT for c in own for q in c.Tessellate()]
        x0, x1 = min(xs), max(xs)
        fis = list(FilteredElementCollector(pd).OfClass(FamilyInstance))
        if not fis:
            continue
        fi = fis[0]; T = fi.GetTotalTransform(); sg = -1 if fi.Mirrored else 1
        nd = pd.EditFamily(fi.Symbol.Family)
        try:
            bad = []
            for c in FilteredElementCollector(nd).OfClass(CurveElement):
                g = c.GeometryCurve
                if g is None:
                    continue
                ps = [T.OfPoint(q) for q in g.Tessellate()]
                px = [p.X * FT for p in ps]
                if max(px) > x1 + TOL or min(px) < x0 - TOL:
                    bad.append({"id": int(c.Id.Value), "x": [round(min(px), 1), round(max(px), 1)], "y": [round(min(sg * p.Y * FT for p in ps), 1), round(max(sg * p.Y * FT for p in ps), 1)],
                                "group": c.GroupId != ElementId.InvalidElementId, "kind": g.GetType().Name})
        finally:
            nd.Close(False)
        if bad:
            rows.append({"family": f.Name, "body_x": [round(x0, 1), round(x1, 1)], "n": len(bad), "curves": bad[:8]})
    finally:
        pd.Close(False)
__output__ = {"status": "completed_unverified", "summary": u"проверено %d профилей, с выступом графики за тело: %d; ничего не менялось" % (len(fams), len(rows)), "rows": rows}
