# -*- coding: utf-8 -*-
# Симметрия собственного контура профиля (3D-тело) относительно оси x=0: каждая вершина усредняется со своей
# зеркальной парой (ближайшая вершина к (-x, y) в пределах tol_mm); вершины без пары — в отчёт, не двигаются.
# outer_mm (опц.) — крайние вершины (|x| ≈ max) ставятся на ±outer_mm. Вложенная графика не меняется.
# Аргументы: items [{family, outer_mm?}], tol_mm (0.8), out_dir. Сохраняет КОПИИ .rfa; проект не меняется.
import json, os, math
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
TOL = float(args.get("tol_mm", 0.8))
rows = []
for it in args["items"]:
    n = it["family"]; r = {"family": n}
    pd = doc.EditFamily(fams[n]); t = None
    try:
        own = [c for c in FilteredElementCollector(pd).OfClass(CurveElement) if c.GeometryCurve is not None and c.GetType().Name in ("DetailLine", "DetailCurve")]
        if any(not isinstance(c.GeometryCurve, Line) for c in own):
            raise Exception(u"в контуре есть не прямые")
        key = lambda p: (round(p.X * FT, 4), round(p.Y * FT, 4))
        verts = {}
        for c in own:
            for p in (c.GeometryCurve.GetEndPoint(0), c.GeometryCurve.GetEndPoint(1)):
                verts[key(p)] = (p.X * FT, p.Y * FT)
        V = list(verts.values()); xmax = max(abs(v[0]) for v in V)
        new = {}; unpaired = []; shifts = []
        for v in V:
            x, y = v
            if abs(x) < 0.05:
                new[key(XYZ(x / FT, y / FT, 0))] = (0.0 if abs(x) < 0.05 else x, y); continue
            cand = [w for w in V if w[0] * x < 0 and abs(w[1] - y) < 0.3]
            best = min(cand, key=lambda w: math.hypot(w[0] + x, w[1] - y)) if cand else None
            if best is None or math.hypot(best[0] + x, best[1] - y) > TOL:
                unpaired.append([round(x, 2), round(y, 2)]); new[key(XYZ(x / FT, y / FT, 0))] = (x, y); continue
            nx = math.copysign((abs(x) + abs(best[0])) / 2.0, x); ny = (y + best[1]) / 2.0
            if it.get("outer_mm") and abs(abs(x) - xmax) < 0.05:
                nx = math.copysign(float(it["outer_mm"]), x)
            shifts.append(abs(nx - x)); new[key(XYZ(x / FT, y / FT, 0))] = (nx, ny)
        sp = own[0]; view = pd.GetElement(sp.OwnerViewId)
        lines = []
        for c in own:
            a = new[key(c.GeometryCurve.GetEndPoint(0))]; b = new[key(c.GeometryCurve.GetEndPoint(1))]
            if math.hypot(a[0] - b[0], a[1] - b[1]) > 0.01:
                lines.append((a, b))
        t = Transaction(pd, u"FT: симметрия контура"); t.Start()
        pd.Delete(List[ElementId]([c.Id for c in own]))
        for a, b in lines:
            ln = pd.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(a[0] / FT, a[1] / FT, 0), XYZ(b[0] / FT, b[1] / FT, 0)))
            try:
                ln.LineStyle = sp.LineStyle
            except Exception:
                pass
        t.Commit(); t = None
        r.update(vertices=len(V), unpaired=unpaired[:20], unpaired_count=len(unpaired), max_shift_mm=round(max(shifts), 3) if shifts else 0, lines=len(lines))
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        r["rfa"] = os.path.join(OUT, n + u".rfa"); pd.SaveAs(r["rfa"], so); r["ok"] = True
    except Exception:
        import traceback
        r["error"] = traceback.format_exc()[-400:]
    finally:
        if t is not None and t.HasStarted() and not t.HasEnded():
            t.RollBack()
        pd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified" if all(x.get("ok") for x in rows) else "partial", "summary": u"профилей %d из %d; проект не менялся" % (sum(1 for x in rows if x.get("ok")), len(rows)), "rows": rows}
