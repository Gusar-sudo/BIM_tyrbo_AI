# -*- coding: utf-8 -*-
# Убрать из графики узла остатки линий СБОКУ стойки за телом профиля (остатки снятой рейки):
# линии вложенного, у которых все точки за краем тела по X дальше tol_mm или касаются его, и |y| < y_max_mm (не нащельник).
# Сохраняет КОПИИ .rfa в out_dir; проект не меняется. Аргументы: families, out_dir, tol_mm (0.3), y_max_mm (28)
import json, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8; TOL = float(args.get("tol_mm", 0.3)); YM = float(args.get("y_max_mm", 28))
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
if not os.path.isdir(args["out_dir"]):
    os.makedirs(args["out_dir"])


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


rows = []
for fn in args["families"]:
    r = {"family": fn}
    pd = doc.EditFamily(fams[fn])
    try:
        xs = [q.X * FT for c in FilteredElementCollector(pd).OfClass(CurveElement) if c.GeometryCurve is not None for q in c.GeometryCurve.Tessellate()]
        x0, x1 = min(xs), max(xs)
        fi = list(FilteredElementCollector(pd).OfClass(FamilyInstance))[0]; T = fi.GetTotalTransform(); sg = -1 if fi.Mirrored else 1
        nd = pd.EditFamily(fi.Symbol.Family)
        try:
            kill = []
            for c in FilteredElementCollector(nd).OfClass(CurveElement):
                g = c.GeometryCurve
                if g is None or c.GroupId != ElementId.InvalidElementId:
                    continue
                ps = [T.OfPoint(q) for q in g.Tessellate()]
                px = [p.X * FT for p in ps]; py = [abs(sg * p.Y * FT) for p in ps]
                outside = min(px) >= x1 - TOL or max(px) <= x0 + TOL
                beyond = max(px) > x1 + TOL or min(px) < x0 - TOL
                if outside and beyond and max(py) < YM:
                    kill.append(c.Id)
            t = Transaction(nd, u"убрать остаток рейки"); t.Start()
            nd.Delete(List[ElementId](kill)); t.Commit()
            left = [c for c in FilteredElementCollector(nd).OfClass(CurveElement) if c.Id in kill]
            r.update(body_x=[round(x0, 1), round(x1, 1)], removed=len(kill), still_there=len(left))
            nd.LoadFamily(pd, LoadOpt())
        finally:
            nd.Close(False)
        o = SaveAsOptions(); o.OverwriteExistingFile = True
        r["rfa"] = os.path.join(args["out_dir"], fn + u".rfa"); pd.SaveAs(r["rfa"], o)
    finally:
        pd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified", "summary": u"копий %d; удалено линий %s; проект не менялся" % (len(rows), [x.get("removed") for x in rows]), "rows": rows}
