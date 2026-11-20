# -*- coding: utf-8 -*-
# Пересрез профилей цс у стены/у проёма: грань со стороны стекла сдвигается на shift_mm к стене (shift > 0 — срезать ещё),
# shift < 0 — удлинить: тогда контур берётся из source (обычный боковой профиль той же стойки) и режется по новой грани.
# Вложенная графика (уплотнитель стекла, лента) остаётся из цс-профиля. Сохраняет КОПИИ .rfa в out_dir (имена прежние).
# Аргументы: items [{name, shift_mm, side? ("max"|"min"|"both"), source?}], out_dir.
import json, io, os
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8; TOL = 1e-5
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))


def side_of(n):
    return "min" if (u"Левый" in n or u"Верхний" in n) else "max"


def own_curves(d):
    return [ce for ce in FilteredElementCollector(d).OfClass(CurveElement) if ce.GeometryCurve is not None and ce.GetType().Name in ("DetailLine", "DetailCurve")]


def chain(segs):
    segs = list(segs); loops = []
    while segs:
        a, b = segs.pop(0); pts = [a, b]; grown = True
        while grown and pts[-1].DistanceTo(pts[0]) > TOL:
            grown = False
            for i, (p, q) in enumerate(segs):
                if p.DistanceTo(pts[-1]) < TOL:
                    pts.append(q); segs.pop(i); grown = True; break
                if q.DistanceTo(pts[-1]) < TOL:
                    pts.append(p); segs.pop(i); grown = True; break
        if pts[-1].DistanceTo(pts[0]) > TOL:
            raise Exception(u"контур не замкнут")
        loops.append(pts[:-1])
    return loops


def clip(poly, xc, keep_le):
    ins = (lambda p: p.X <= xc + TOL) if keep_le else (lambda p: p.X >= xc - TOL)
    out = []
    for i in range(len(poly)):
        cur = poly[i]; prv = poly[i - 1]
        if ins(cur):
            if not ins(prv):
                t = (xc - prv.X) / (cur.X - prv.X); out.append(XYZ(xc, prv.Y + t * (cur.Y - prv.Y), 0))
            out.append(cur)
        elif ins(prv):
            t = (xc - prv.X) / (cur.X - prv.X); out.append(XYZ(xc, prv.Y + t * (cur.Y - prv.Y), 0))
    res = []
    for p in out:
        if not res or p.DistanceTo(res[-1]) > TOL:
            res.append(p)
    if len(res) > 1 and res[0].DistanceTo(res[-1]) < TOL:
        res.pop()
    k = 0
    while k < len(res) and len(res) > 2:
        a, b, c = res[k - 1], res[k], res[(k + 1) % len(res)]
        if abs((b.X - a.X) * (c.Y - a.Y) - (b.Y - a.Y) * (c.X - a.X)) < 1e-9:
            res.pop(k)
        else:
            k += 1
    return res


def loops_of(d):
    own = own_curves(d)
    if any(not isinstance(ce.GeometryCurve, Line) for ce in own):
        raise Exception(u"в контуре есть не прямые")
    segs = [(XYZ(ce.GeometryCurve.GetEndPoint(0).X, ce.GeometryCurve.GetEndPoint(0).Y, 0), XYZ(ce.GeometryCurve.GetEndPoint(1).X, ce.GeometryCurve.GetEndPoint(1).Y, 0)) for ce in own]
    return own, chain(segs)


area = lambda lp: (max(p.X for p in lp) - min(p.X for p in lp)) * (max(p.Y for p in lp) - min(p.Y for p in lp))
rows = []
for it in args["items"]:
    n = it["name"]; r = {"profile": n}
    side = it.get("side") or side_of(n); sh = float(it["shift_mm"]) / FT
    pd = doc.EditFamily(fams[n]); sd = None; t = None
    try:
        own, loops = loops_of(pd)
        xs = [p.X for lp in loops for p in lp]
        sides = ["max", "min"] if side == "both" else [side]
        faces = dict((s_, (max(xs) if s_ == "max" else min(xs))) for s_ in sides)
        cut = dict((s_, (faces[s_] - sh if s_ == "max" else faces[s_] + sh)) for s_ in sides)
        if sh < 0:
            if not it.get("source"):
                raise Exception(u"удлинение без source")
            sd = doc.EditFamily(fams[it["source"]]); _, loops = loops_of(sd)
        new = loops
        for s_ in sides:
            outer = max(new, key=area); xc = cut[s_]; G = 0.3 / FT
            new = [l for l in (clip(lp, xc if lp is outer else (xc - G if s_ == "max" else xc + G), s_ == "max") for lp in new) if len(l) >= 3]
        SHORT = doc.Application.ShortCurveTolerance * 1.5
        merged = []
        for lp in new:
            q = []
            for pt in lp:
                if not q or pt.DistanceTo(q[-1]) > SHORT:
                    q.append(pt)
            while len(q) > 2 and q[0].DistanceTo(q[-1]) <= SHORT:
                q.pop()
            if len(q) >= 3:
                merged.append(q)
        sp = own[0]; view = pd.GetElement(sp.OwnerViewId)
        t = Transaction(pd, u"FT: пересрез под зазор 3 мм"); t.Start()
        pd.Delete(List[ElementId]([ce.Id for ce in own]))
        for lp in merged:
            for i in range(len(lp)):
                ln = pd.FamilyCreate.NewDetailCurve(view, Line.CreateBound(lp[i], lp[(i + 1) % len(lp)]))
                try:
                    ln.LineStyle = sp.LineStyle
                except Exception:
                    pass
        t.Commit(); t = None
        xs2 = [p.X for lp in merged for p in lp]
        r.update(side=side, faces_before_mm=dict((k, round(v * FT, 2)) for k, v in faces.items()),
                 faces_after_mm={"max": round(max(xs2) * FT, 2), "min": round(min(xs2) * FT, 2)}, loops=len(merged), source=it.get("source"))
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        r["rfa"] = os.path.join(OUT, n + u".rfa"); pd.SaveAs(r["rfa"], so); r["ok"] = True
    except Exception:
        import traceback
        r["error"] = traceback.format_exc()[-400:]
    finally:
        if t is not None and t.HasStarted() and not t.HasEnded():
            t.RollBack()
        if sd is not None:
            sd.Close(False)
        pd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified" if all(x.get("ok") for x in rows) else "partial", "summary": u"профилей %d из %d; проект не менялся" % (sum(1 for x in rows if x.get("ok")), len(rows)), "rows": rows}
