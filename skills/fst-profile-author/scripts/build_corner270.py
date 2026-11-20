# -*- coding: utf-8 -*-
# Профили прямоугольных столбов (FSC17 М2, FSC04 М3) под угол 270° из угловых 90° (14.11).
# 270° = стена B уходит на сторону главного фасада (стрелок разворота), в осях профиля — на +Y.
# Во вложенном 2D узла сам столб (FS.C-17 / FS.C-04) и рамка B поворачиваются на 180° вокруг оси стены A (0,0);
# боковые элементы (рамка A на −X и заглушка на +X) остаются: их пазы симметричны оси стены A.
# Силуэт (линии профиля = 3D-тело) — заново: полоса |y| <= k_mm остаётся, всё вне её поворачивается на 180°.
# Все линии силуэта прямые и вдоль осей: считается по сетке, близкие координаты (< 0,25 мм) склеиваются.
# Отражение вложенного учитывается (full_tr: GetTotalTransform не видит HandFlipped/FacingFlipped).
# Новое семейство: SaveAs в out_dir. Проект НЕ меняется.
# Аргументы: jobs [{src_family, new_name, k_mm}], out_dir, snap_mm (0.25), side_frac (0.7)
import json, math, os, io
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
SNAP = float(args.get("snap_mm", 0.25))
byname = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
DETAIL = ("DetailLine", "DetailArc", "DetailNurbSpline", "DetailEllipse", "DetailCurve")


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


def full_tr(inst):
    T_ = inst.GetTotalTransform(); M_ = Transform.Identity
    if inst.HandFlipped:
        M_.BasisX = XYZ(-1, 0, 0)
    if inst.FacingFlipped:
        M_.BasisY = XYZ(0, -1, 0)
    return T_.Multiply(M_)


def pts_of(el, d):
    out = []
    if isinstance(el, CurveElement):
        out += list(el.GeometryCurve.Tessellate())
    elif isinstance(el, FilledRegion):
        for lp in el.GetBoundaries():
            for c in lp:
                out += list(c.Tessellate())
    elif isinstance(el, Group):
        for mid in el.GetMemberIds():
            out += pts_of(d.GetElement(mid), d)
    elif isinstance(el, FamilyInstance):
        bb = el.get_BoundingBox(None)
        if bb:
            out += [bb.Min, bb.Max]
    return out


def clusters(vals, prio):
    # склеить значения ближе SNAP; представитель — исходное значение (prio), иначе первое
    vs = sorted(set(vals)); groups = []
    for v in vs:
        if groups and v - groups[-1][-1] < SNAP:
            groups[-1].append(v)
        else:
            groups.append([v])
    m = {}
    for g in groups:
        orig = [v for v in g if v in prio]
        rep = orig[0] if orig else g[0]
        for v in g:
            m[v] = rep
    return m


def new_silhouette(segs, K):
    # segs: [(x1,y1,x2,y2)] мм, только оси. Возвращает новые отрезки.
    xs0 = set(); ys0 = set()
    for x1, y1, x2, y2 in segs:
        xs0.update([round(x1, 3), round(x2, 3)]); ys0.update([round(y1, 3), round(y2, 3)])
    mx = clusters(list(xs0) + [-x for x in xs0], xs0)
    # приоритет — отметки НОВОЙ формы: внутри полосы исходные, вне — повёрнутые (дно паза B 32,29 у FSC17 не должно склеиться с 32,5)
    ynew = set([y for y in ys0 if abs(y) <= K + 1e-6] + [-y for y in ys0 if abs(y) >= K - 1e-6])
    my = clusters(list(ys0) + [-y for y in ys0] + [K, -K], ynew)
    S = [(mx[round(a, 3)], my[round(b, 3)], mx[round(c, 3)], my[round(d, 3)]) for a, b, c, d in segs]
    Kp = my[K]; Km = my[-K]
    def snapx(v): return mx.get(round(v, 3), v)
    def snapy(v): return my.get(round(v, 3), v)
    X = sorted(set(mx.values())); Y = sorted(set(my.values()))
    vert = [(a, min(b, d), max(b, d)) for a, b, c, d in S if abs(a - c) < 1e-6 and abs(b - d) > 1e-6]

    def inside(px, py):
        n = 0
        for x, y0, y1 in vert:
            if x > px and y0 < py < y1:
                n += 1
        return n % 2 == 1
    nx, ny = len(X) - 1, len(Y) - 1
    cell = [[False] * ny for _ in range(nx)]
    for i in range(nx):
        cx = (X[i] + X[i + 1]) / 2.0
        for j in range(ny):
            cy = (Y[j] + Y[j + 1]) / 2.0
            if Km < cy < Kp:
                cell[i][j] = inside(cx, cy)
            else:
                cell[i][j] = inside(-cx, -cy)   # поворот на 180° вокруг (0,0)

    def c(i, j):
        return 0 <= i < nx and 0 <= j < ny and cell[i][j]
    hs = {}; vs = {}
    for i in range(nx):
        for j in range(ny):
            if not cell[i][j]:
                continue
            if not c(i, j - 1): hs.setdefault(Y[j], []).append((X[i], X[i + 1]))
            if not c(i, j + 1): hs.setdefault(Y[j + 1], []).append((X[i], X[i + 1]))
            if not c(i - 1, j): vs.setdefault(X[i], []).append((Y[j], Y[j + 1]))
            if not c(i + 1, j): vs.setdefault(X[i + 1], []).append((Y[j], Y[j + 1]))

    def merge(iv):
        iv = sorted(iv); out = []
        for a, b in iv:
            if out and abs(out[-1][1] - a) < 1e-6:
                out[-1] = (out[-1][0], b)
            else:
                out.append((a, b))
        return out
    res = []
    for y, iv in hs.items():
        for a, b in merge(iv):
            res.append((a, y, b, y))
    for x, iv in vs.items():
        for a, b in merge(iv):
            res.append((x, a, x, b))
    return res


res = []
for job in args["jobs"]:
    r = {"src": job["src_family"], "new": job["new_name"], "ok": False}
    pdoc = doc.EditFamily(byname[job["src_family"]])
    try:
        fi = list(FilteredElementCollector(pdoc).OfClass(FamilyInstance))[0]
        T = full_tr(fi)
        r["flips"] = [bool(fi.HandFlipped), bool(fi.FacingFlipped)]
        nd = pdoc.EditFamily(fi.Symbol.Family)
        try:
            items = []
            for el in FilteredElementCollector(nd).WhereElementIsNotElementType():
                if el.GroupId != ElementId.InvalidElementId:
                    continue
                if not isinstance(el, (CurveElement, FilledRegion, Group, FamilyInstance)):
                    continue
                if isinstance(el, CurveElement) and el.GetType().Name not in DETAIL:
                    continue
                pp = [T.OfPoint(q) for q in pts_of(el, nd)]
                if not pp:
                    continue
                bx = (min(p.X for p in pp), min(p.Y for p in pp), max(p.X for p in pp), max(p.Y for p in pp))
                items.append((el, bx))
            post = max(items, key=lambda it: (it[1][2] - it[1][0]) * (it[1][3] - it[1][1]))
            hw = (post[1][2] - post[1][0]) / 2.0
            sf = float(args.get("side_frac", 0.7))
            keep = [it for it in items if it[0].Id != post[0].Id and (it[1][2] < -sf * hw or it[1][0] > sf * hw)]
            rot = [it for it in items if it not in keep]
            nm = lambda it: (it[0].Name if isinstance(it[0], Group) else it[0].GetType().Name)
            r["kept"] = [nm(it) for it in keep]; r["rotated"] = [nm(it) for it in rot]
            r["post_mm"] = [round(v * FT, 2) for v in post[1]]
            c0 = T.Inverse.OfPoint(XYZ.Zero)
            t = Transaction(nd, u"поворот 180°"); t.Start()
            ElementTransformUtils.RotateElements(nd, List[ElementId]([it[0].Id for it in rot]), Line.CreateBound(c0, c0 + XYZ.BasisZ), math.pi)
            t.Commit()
            after = []
            for it in rot:
                pp = [T.OfPoint(q) for q in pts_of(it[0], nd)]
                after.append([nm(it)] + [round(v * FT, 2) for v in (min(p.X for p in pp), min(p.Y for p in pp), max(p.X for p in pp), max(p.Y for p in pp))])
            r["rotated_after_mm"] = after
            nd.LoadFamily(pdoc, LoadOpt())
        finally:
            nd.Close(False)
        # силуэт
        own = [ce for ce in FilteredElementCollector(pdoc).OfClass(CurveElement) if ce.GetType().Name in DETAIL]
        segs = []
        for ce in own:
            cv = ce.GeometryCurve
            if not isinstance(cv, Line):
                raise Exception(u"в силуэте не только отрезки")
            a = cv.GetEndPoint(0); b = cv.GetEndPoint(1)
            if abs(a.X - b.X) > 1e-6 and abs(a.Y - b.Y) > 1e-6:
                raise Exception(u"в силуэте есть наклонный отрезок")
            segs.append((a.X * FT, a.Y * FT, b.X * FT, b.Y * FT))
        ns = new_silhouette(segs, float(job["k_mm"]))
        lens = [abs(x2 - x1) + abs(y2 - y1) for x1, y1, x2, y2 in ns]
        r["silhouette"] = {"lines_before": len(segs), "lines_after": len(ns), "min_len_mm": round(min(lens), 2),
                           "bbox_mm": [round(min(min(s[0], s[2]) for s in ns), 2), round(min(min(s[1], s[3]) for s in ns), 2),
                                       round(max(max(s[0], s[2]) for s in ns), 2), round(max(max(s[1], s[3]) for s in ns), 2)],
                           "lines_mm": [[round(v, 2) for v in s] for s in ns]}
        if min(lens) < 0.78:
            raise Exception(u"отрезок силуэта < 0,78 мм: %.2f" % min(lens))
        view = [v for v in FilteredElementCollector(pdoc).OfClass(ViewPlan) if not v.IsTemplate][0]
        gs = own[0].LineStyle.Id if own else None
        t = Transaction(pdoc, u"силуэт 270°"); t.Start()
        pdoc.Delete(List[ElementId]([ce.Id for ce in own]))
        for x1, y1, x2, y2 in ns:
            dc = pdoc.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(x1 / FT, y1 / FT, 0), XYZ(x2 / FT, y2 / FT, 0)))
            if gs is not None:
                try:
                    dc.LineStyle = pdoc.GetElement(gs)
                except Exception:
                    pass
        t.Commit()
        opts = SaveAsOptions(); opts.OverwriteExistingFile = True
        if not os.path.isdir(args["out_dir"]):
            os.makedirs(args["out_dir"])
        r["rfa"] = os.path.join(args["out_dir"], job["new_name"] + u".rfa")
        pdoc.SaveAs(r["rfa"], opts)
        r["ok"] = True
    except Exception as ex:
        r["error"] = str(ex)[:300]
    finally:
        pdoc.Close(False)
    res.append(r)
__output__ = {"status": "completed_unverified" if all(x["ok"] for x in res) else "partial",
              "summary": u"профилей 270°: %d из %d; проект не изменён" % (sum(1 for x in res if x["ok"]), len(res)), "results": res}
