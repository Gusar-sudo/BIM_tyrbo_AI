# -*- coding: utf-8 -*-
# Силуэт профиля импоста (линии в семействе профиля = контур 3D-тела): вырез под стекло углубить до зоны уплотнителя,
# чтобы тело импоста не перекрывало уплотнитель панели. Правило: концы линий с |y| = from_mm (±tol) переносятся на |y| = to_mm.
# Работает с .rfa-файлами (открыть -> правка -> сохранить на месте). Проект НЕ меняется.
# Аргументы: rfas, from_mm, to_mm, tol_mm
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
FT = 304.8
Y0 = float(args["from_mm"]); Y1 = float(args["to_mm"]); TOL = float(args.get("tol_mm", 0.15))


def mv(p):
    y = p.Y * FT
    if abs(abs(y) - Y0) <= TOL:
        return XYZ(p.X, (Y1 if y > 0 else -Y1) / FT, p.Z), True
    return p, False


res = []
rfas = list(args.get("rfas", []))
if args.get("list_file"):
    with open(args["list_file"], encoding="utf-8") as f:
        rfas += json.load(f)[args["list_key"]]
for path in rfas:
    r = {"rfa": path.split("\\")[-1], "moved_lines": 0, "ok": False}
    fdoc = app.OpenDocumentFile(path)
    try:
        lines = [ce for ce in FilteredElementCollector(fdoc).OfClass(CurveElement) if isinstance(ce.GeometryCurve, Line)]
        t = Transaction(fdoc, u"силуэт: вырез под уплотнитель"); t.Start()
        dead = []
        for ce in lines:
            c = ce.GeometryCurve
            a, ma = mv(c.GetEndPoint(0)); b, mb = mv(c.GetEndPoint(1))
            if not (ma or mb):
                continue
            if a.DistanceTo(b) < 0.5 / FT:
                dead.append(ce.Id); continue
            ce.SetGeometryCurve(Line.CreateBound(a, b), True)
            r["moved_lines"] += 1
        for i in dead:
            fdoc.Delete(i)
        r["deleted"] = len(dead)
        t.Commit()
        fdoc.Save()
        r["ok"] = True
    except Exception as ex:
        r["error"] = str(ex)[:200]
    finally:
        fdoc.Close(False)
    res.append(r)
__output__ = {"status": "completed_unverified", "summary": u"силуэтов изменено %d из %d; проект не изменён" % (sum(1 for x in res if x["ok"] and x["moved_lines"]), len(res)), "results": res}
