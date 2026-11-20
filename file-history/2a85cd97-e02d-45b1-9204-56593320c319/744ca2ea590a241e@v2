# -*- coding: utf-8 -*-
# Силуэт профиля (линии семейства профиля = 3D-тело): вырез под стекло по высоте (поперёк стены) расширить:
# концы линий с |y| = from_mm (±tol) и |x| >= x_min_mm переносятся на |y| = to_mm. Работает с копиями .rfa (проект не меняется).
# Аргументы: items [{rfa, from_mm, to_mm, x_min_mm?}], save (false — только отчёт), tol_mm.
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
FT = 304.8
TOL = float(args.get("tol_mm", 0.15))
SAVE = bool(args.get("save", False))
res = []
for it in args["items"]:
    Y0 = float(it["from_mm"]); Y1 = float(it["to_mm"]); XM = float(it.get("x_min_mm", 0))
    r = {"rfa": it["rfa"].split("\\")[-1], "moved": [], "before": [], "ok": False}
    fdoc = app.OpenDocumentFile(it["rfa"])
    try:
        own = [ce for ce in FilteredElementCollector(fdoc).OfClass(CurveElement) if ce.GetType().Name in ("DetailLine", "DetailCurve") and isinstance(ce.GeometryCurve, Line)]
        r["before"] = [[round(v * FT, 2) for v in (c.GeometryCurve.GetEndPoint(0).X, c.GeometryCurve.GetEndPoint(0).Y, c.GeometryCurve.GetEndPoint(1).X, c.GeometryCurve.GetEndPoint(1).Y)] for c in own]

        def mv(p):
            y = p.Y * FT
            if abs(abs(y) - Y0) <= TOL and abs(p.X * FT) >= XM - TOL:
                return XYZ(p.X, (Y1 if y > 0 else -Y1) / FT, p.Z), True
            return p, False
        t = Transaction(fdoc, u"силуэт: вырез под стекло по высоте"); t.Start()
        dead = []
        for ce in own:
            c = ce.GeometryCurve
            a, ma = mv(c.GetEndPoint(0)); b, mb = mv(c.GetEndPoint(1))
            if not (ma or mb):
                continue
            if a.DistanceTo(b) < 0.5 / FT:
                dead.append(ce.Id); continue
            ce.SetGeometryCurve(Line.CreateBound(a, b), True)
            r["moved"].append([round(v * FT, 2) for v in (a.X, a.Y, b.X, b.Y)])
        for i in dead:
            fdoc.Delete(i)
        r["deleted"] = len(dead)
        t.Commit()
        if SAVE:
            fdoc.Save()
        r["ok"] = True
    except Exception as ex:
        r["error"] = str(ex)[:300]
    finally:
        fdoc.Close(False)
    res.append(r)
__output__ = {"status": "completed_unverified", "summary": (u"сохранено" if SAVE else u"ОТЧЁТ без сохранения") + u": профилей %d, линий сдвинуто %d; проект не изменён" % (len(res), sum(len(x["moved"]) for x in res)), "results": res}
