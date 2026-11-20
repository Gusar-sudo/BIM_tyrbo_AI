# -*- coding: utf-8 -*-
# Заменить собственный контур профиля (линии семейства профиля = 3D-тело импоста) на контуры из body_loops_from_fill.py.
# Координаты контуров — графики узла (вложенного семейства); переводятся трансформацией вложенного экземпляра.
# Работает с копией .rfa: rfa (источник), out_rfa (куда сохранить), loops_json, save (false — только отчёт).
import json, io, os
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
FT = 304.8
L = json.loads(io.open(args["loops_json"], encoding="utf-8").read())["loops"]
res = {"errors": []}
fdoc = app.OpenDocumentFile(args["rfa"])
try:
    own = [ce for ce in FilteredElementCollector(fdoc).OfClass(CurveElement) if ce.GetType().Name in ("DetailLine", "DetailArc", "DetailCurve", "DetailEllipse", "DetailNurbSpline")]
    res["own_before"] = len(own)
    view = fdoc.GetElement(own[0].OwnerViewId) if own else [v for v in FilteredElementCollector(fdoc).OfClass(View) if not v.IsTemplate and v.ViewType == ViewType.FloorPlan][0]
    fis = list(FilteredElementCollector(fdoc).OfClass(FamilyInstance))
    T = fis[0].GetTransform() if fis else Transform.Identity
    res["nested_transform"] = [round(T.Origin.X * FT, 3), round(T.Origin.Y * FT, 3), round(T.BasisX.X, 3), round(T.BasisY.Y, 3)]
    gs = own[0].LineStyle if own else None
    t = Transaction(fdoc, u"тело профиля по графике узла"); t.Start()
    for ce in own:
        fdoc.Delete(ce.Id)
    made = 0
    for lp in L:
        P = [T.OfPoint(XYZ(p[0] / FT, p[1] / FT, 0)) for p in lp["pts"]]
        for i in range(len(P)):
            a = P[i]; b = P[(i + 1) % len(P)]
            try:
                c = fdoc.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(a.X, a.Y, 0), XYZ(b.X, b.Y, 0)))
                if gs is not None:
                    try: c.LineStyle = gs
                    except Exception: pass
                made += 1
            except Exception as ex:
                res["errors"].append(u"%s: %.3f мм" % (str(ex)[:80], a.DistanceTo(b) * FT))
    res["lines_made"] = made
    t.Commit()
    if args.get("save") and not res["errors"]:
        o = SaveAsOptions(); o.OverwriteExistingFile = True
        fdoc.SaveAs(args["out_rfa"], o); res["saved"] = args["out_rfa"]
finally:
    fdoc.Close(False)
__output__ = {"status": "completed_unverified" if not res["errors"] else "partial", "summary": u"линий %s, ошибок %d; проект не изменён" % (res.get("lines_made"), len(res["errors"])), "result": res}
