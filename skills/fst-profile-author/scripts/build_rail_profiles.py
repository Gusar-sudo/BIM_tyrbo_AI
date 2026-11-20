# -*- coding: utf-8 -*-
# Профили «с накрывающей рейкой вместо стекла»: стойка над подвесным потолком (рейки с двух сторон) и край у стены
# над подвесным потолком (лента у стены + рейка). Сечение собирается из двух половин по оси x = 0 профиля:
#   половина keep — из профиля A (основа: закрытый боковой или «к стене» с лентой), сторона рейки — из профиля B
#   (закрытый боковой, у которого широкая накрывающая рейка FS.C-158 / FS.C-26 стоит на нужной стороне).
# Собственный контур: внешний контур = половина A (x со стороны keep) + половина B; внутренние контуры A,
#   не уходящие на сторону рейки, сохраняются. Вложенная графика (в семействе узла профиля A): удаляются
#   замкнутые контуры целиком на стороне рейки (витражная рейка), добавляются контуры рейки из B (пересчёт координат).
# Аргументы: items [{a, b, save_as, keep: "neg"|"pos"}], out_dir. Сохраняет КОПИИ .rfa в out_dir; проект не меняется.
import json, os, io
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
FT = 304.8
TOL = 1e-5
SIDE_MIN = 3.0 / FT        # контур «на стороне», если весь дальше 3 мм от оси
RAIL_MIN_H = 40.0 / FT     # рейка — высокий контур на стороне
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))


class _LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, a, b, src, c):
        src.Value = FamilySource.Family; c.Value = True; return True


def kp(p):
    return (round(p.X * FT, 2), round(p.Y * FT, 2))


def loops_by_curves(items):
    """items: [(ce, curve_in_profile_coords)] -> список групп (связные контуры)."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for ce, c in items:
        a, b = find(kp(c.GetEndPoint(0))), find(kp(c.GetEndPoint(1)))
        if a != b:
            parent[a] = b
    g = {}
    for ce, c in items:
        g.setdefault(find(kp(c.GetEndPoint(0))), []).append((ce, c))
    return list(g.values())


def bbox(group):
    pts = [q for _, c in group for q in c.Tessellate()]
    return min(p.X for p in pts), max(p.X for p in pts), min(p.Y for p in pts), max(p.Y for p in pts)


def on_side(bb, sgn):
    return bb[0] >= SIDE_MIN if sgn > 0 else bb[1] <= -SIDE_MIN


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


def clip(poly, keep_le):
    ins = (lambda p: p.X <= TOL) if keep_le else (lambda p: p.X >= -TOL)
    out = []
    for i in range(len(poly)):
        cur = poly[i]; prv = poly[i - 1]
        if ins(cur):
            if not ins(prv):
                t = (0 - prv.X) / (cur.X - prv.X); out.append(XYZ(0, prv.Y + t * (cur.Y - prv.Y), 0))
            out.append(cur)
        elif ins(prv):
            t = (0 - prv.X) / (cur.X - prv.X); out.append(XYZ(0, prv.Y + t * (cur.Y - prv.Y), 0))
    res = []
    for p in out:
        if not res or p.DistanceTo(res[-1]) > TOL:
            res.append(p)
    if len(res) > 1 and res[0].DistanceTo(res[-1]) < TOL:
        res.pop()
    return res


def half_chain(ring):
    """Кольцо половины (с отрезком по x=0) -> цепочка от верхней точки на оси к нижней через сторону."""
    on = [i for i, p in enumerate(ring) if abs(p.X) < 1e-4]
    if len(on) < 2:
        raise Exception(u"половина не касается оси")
    top = max(on, key=lambda i: ring[i].Y); bot = min(on, key=lambda i: ring[i].Y)
    n = len(ring)
    for step in (1, -1):
        seq = []; i = top
        while True:
            seq.append(ring[i])
            if i == bot:
                break
            i = (i + step) % n
        if any(abs(p.X) > 1e-4 for p in seq):   # путь через сторону, а не по оси
            return seq
    raise Exception(u"не найден путь по стороне")


def own_items(pd):
    return [(ce, ce.GeometryCurve) for ce in FilteredElementCollector(pd).OfClass(CurveElement) if ce.GeometryCurve is not None]


def outer_and_inner(pd):
    own = own_items(pd)
    if any(not isinstance(c, Line) for _, c in own):
        raise Exception(u"в собственном контуре не только прямые")
    loops = chain([(XYZ(c.GetEndPoint(0).X, c.GetEndPoint(0).Y, 0), XYZ(c.GetEndPoint(1).X, c.GetEndPoint(1).Y, 0)) for _, c in own])
    area = lambda lp: (max(p.X for p in lp) - min(p.X for p in lp)) * (max(p.Y for p in lp) - min(p.Y for p in lp))
    outer = max(loops, key=area)
    return own, outer, [l for l in loops if l is not outer]


def rail_curves(fam_name, sgn):
    """Кривые накрывающей рейки профиля B в координатах профиля (контур на стороне sgn, высотой >= 40 мм)."""
    pd = doc.EditFamily(fams[fam_name])
    try:
        out_own = outer_and_inner(pd)
        res = []
        for fi in FilteredElementCollector(pd).OfClass(FamilyInstance):
            T = fi.GetTransform(); nd = pd.EditFamily(fi.Symbol.Family)
            try:
                items = [(ce, ce.GeometryCurve.CreateTransformed(T)) for ce in FilteredElementCollector(nd).OfClass(CurveElement) if ce.GeometryCurve is not None]
                for g in loops_by_curves(items):
                    bb = bbox(g)
                    if on_side(bb, sgn) and bb[3] - bb[2] >= RAIL_MIN_H:
                        res.extend(c for _, c in g)
            finally:
                nd.Close(False)
        return res, out_own[1]
    finally:
        pd.Close(False)


report = []
for it in args["items"]:
    r = {"save_as": it["save_as"]}
    keep_neg = it.get("keep", "neg") == "neg"
    sgn = 1 if keep_neg else -1          # сторона рейки
    pd = None
    try:
        rails, b_outer = rail_curves(it["b"], sgn)
        if not rails:
            raise Exception(u"в профиле B нет рейки на нужной стороне")
        r["rail_segments"] = len(rails)
        pd = doc.EditFamily(fams[it["a"]])
        own, a_outer, a_inner = outer_and_inner(pd)
        # внешний контур из двух половин
        ca = half_chain(clip(a_outer, keep_neg)); cb = half_chain(clip(b_outer, not keep_neg))
        poly = ca + list(reversed(cb))
        SHORT = app.ShortCurveTolerance * 1.05   # стык половин по оси может дать отрезок короче допуска Revit — точки сливаем
        clean = []
        for p in poly:
            if not clean or p.DistanceTo(clean[-1]) > SHORT:
                clean.append(p)
        while len(clean) > 3 and clean[0].DistanceTo(clean[-1]) <= SHORT:
            clean.pop()
        keep_inner = [l for l in a_inner if not ((min(p.X for p in l) >= -TOL) if keep_neg else (max(p.X for p in l) <= TOL))]
        r["inner_kept"] = len(keep_inner); r["inner_dropped"] = len(a_inner) - len(keep_inner)
        sp = own[0][0]; view = pd.GetElement(sp.OwnerViewId) if sp.OwnerViewId != ElementId.InvalidElementId else pd.ActiveView
        t = Transaction(pd, u"FT: профиль с рейкой — контур"); t.Start()
        try:
            pd.Delete(List[ElementId]([ce.Id for ce, _ in own]))
            n = 0
            for lp in [clean] + keep_inner:
                for i in range(len(lp)):
                    a, b = lp[i], lp[(i + 1) % len(lp)]
                    if a.DistanceTo(b) < 1e-4:
                        continue
                    ln = pd.FamilyCreate.NewDetailCurve(view, Line.CreateBound(a, b))
                    try:
                        ln.LineStyle = sp.LineStyle
                    except Exception:
                        pass
                    n += 1
            r["own_segments"] = n
            t.Commit()
        except Exception:
            t.RollBack(); raise
        xs = [c.GetEndPoint(k).X * FT for _, c in own_items(pd) for k in (0, 1)]
        ys = [c.GetEndPoint(k).Y * FT for _, c in own_items(pd) for k in (0, 1)]
        r["own_after_mm"] = [round(min(xs), 2), round(max(xs), 2), round(min(ys), 2), round(max(ys), 2)]
        # вложенная графика
        fis = list(FilteredElementCollector(pd).OfClass(FamilyInstance))
        r["nested"] = []
        for fi in fis:
            T = fi.GetTransform(); Ti = T.Inverse; nd = pd.EditFamily(fi.Symbol.Family)
            nr = {"family": fi.Symbol.Family.Name}
            try:
                tn = Transaction(nd, u"FT: рейка вместо витражной"); tn.Start()
                try:
                    for g in list(FilteredElementCollector(nd).OfClass(Group)):
                        try:
                            g.UngroupMembers()
                        except Exception:
                            pass
                    items = [(ce, ce.GeometryCurve.CreateTransformed(T)) for ce in FilteredElementCollector(nd).OfClass(CurveElement) if ce.GeometryCurve is not None]
                    dele = []; style = None
                    for g in loops_by_curves(items):
                        if on_side(bbox(g), sgn):
                            dele.extend(ce.Id for ce, _ in g)
                            if style is None:
                                style = g[0][0].LineStyle
                    vw = nd.GetElement(items[0][0].OwnerViewId) if items[0][0].OwnerViewId != ElementId.InvalidElementId else nd.ActiveView
                    for d in list(FilteredElementCollector(nd).OfClass(Dimension)):
                        try:
                            nd.Delete(d.Id)
                        except Exception:
                            pass
                    if dele:
                        nd.Delete(List[ElementId](dele))
                    k = 0
                    for c in rails:
                        dc = nd.FamilyCreate.NewDetailCurve(vw, c.CreateTransformed(Ti))
                        if style is not None:
                            try:
                                dc.LineStyle = style
                            except Exception:
                                pass
                        k += 1
                    nr.update(deleted=len(dele), rail_added=k)
                    tn.Commit()
                except Exception:
                    tn.RollBack(); raise
                nd.LoadFamily(pd, _LO())
            finally:
                nd.Close(False)
            r["nested"].append(nr)
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        pth = os.path.join(OUT, it["save_as"] + ".rfa"); pd.SaveAs(pth, so); r["rfa"] = pth
    except Exception as ex:
        r["error"] = str(ex)
    finally:
        if pd is not None:
            pd.Close(False)
    report.append(r)
for f in os.listdir(OUT):   # резервные копии Revit
    if __import__("re").search(r"\.\d{4}\.rfa$", f.lower()):
        try:
            os.remove(os.path.join(OUT, f))
        except Exception:
            pass
bad = [x for x in report if x.get("error")]
__output__ = {"status": "completed_unverified" if not bad else "partial",
              "summary": u"профилей %d, ошибок %d; копии в %s, проект не менялся" % (len(report), len(bad), OUT), "result": report}
