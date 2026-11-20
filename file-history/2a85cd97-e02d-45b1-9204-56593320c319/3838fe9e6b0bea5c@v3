# -*- coding: utf-8 -*-
# Однослойная цельностеклянная (по аналогии с двухслойной цс): профили-копии.
# jobs: [{kind:"side", src (однослойный обычный профиль), seal_src (двухслойный цс-профиль той же стороны),
#          new, clip_x (край тела со стороны стекла, мм; знак = сторона стекла), facade_sign (-1: фасад по -Y профиля)}]
#        [{kind:"up008", src, new, facade_sign}]
# side: тело (собственные линии) обрезается по X до clip_x (как у цс: панель режется по краю тела, выступ стекла 0);
#       полости, пересекающие линию, — на 0,3 мм внутрь; во вложенную графику добавляется уплотнитель стекла из seal_src
#       (линии вне групп со стороны стекла и фасада), лента у стены остаётся.
# up008: из двух полосок тела остаётся одна — со стороны фасада.
# Сохраняет КОПИИ .rfa в out_dir; проект не меняется.
import json, io, os, math
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
DET = ("DetailLine", "DetailArc", "DetailNurbSpline", "DetailEllipse", "DetailCurve")
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


def own_lines(pd):
    return [c for c in FilteredElementCollector(pd).OfClass(CurveElement) if c.GetType().Name in DET]


def chain(segs, tol=0.05):
    loops = []; rest = list(segs)
    while rest:
        a, b = rest.pop(0); ch = [a, b]; grown = True
        while grown:
            grown = False
            for i, (p, q) in enumerate(rest):
                if math.hypot(p[0] - ch[-1][0], p[1] - ch[-1][1]) < tol:
                    ch.append(q); rest.pop(i); grown = True; break
                if math.hypot(q[0] - ch[-1][0], q[1] - ch[-1][1]) < tol:
                    ch.append(p); rest.pop(i); grown = True; break
        if len(ch) > 3 and math.hypot(ch[0][0] - ch[-1][0], ch[0][1] - ch[-1][1]) < tol:
            loops.append(ch[:-1])
    return loops


def area(L):
    return 0.5 * abs(sum(L[i][0] * L[(i + 1) % len(L)][1] - L[(i + 1) % len(L)][0] * L[i][1] for i in range(len(L))))


def clip(L, x0, side):
    """Сазерленд-Ходжмен по полуплоскости: side<0 — оставить x >= x0; side>0 — оставить x <= x0"""
    keep = (lambda p: p[0] >= x0) if side < 0 else (lambda p: p[0] <= x0)
    out = []
    n = len(L)
    for i in range(n):
        a = L[i]; b = L[(i + 1) % n]
        ia, ib = keep(a), keep(b)
        if ia:
            out.append(a)
        if ia != ib:
            t = (x0 - a[0]) / (b[0] - a[0]); out.append((x0, a[1] + t * (b[1] - a[1])))
    # убрать повторы и отрезки короче 0,8 мм
    res = []
    for p in out:
        if not res or math.hypot(p[0] - res[-1][0], p[1] - res[-1][1]) > 0.8:
            res.append(p)
    while len(res) > 2 and math.hypot(res[0][0] - res[-1][0], res[0][1] - res[-1][1]) < 0.8:
        res.pop()
    return res if len(res) >= 3 else None


rows = []
for job in args["jobs"]:
    r = {"new": job["new"], "ok": False}
    pd = doc.EditFamily(fams[job["src"]])
    try:
        view = [v for v in FilteredElementCollector(pd).OfClass(ViewPlan) if not v.IsTemplate][0]
        lines = own_lines(pd)
        segs = []
        for c in lines:
            g = c.GeometryCurve
            ps = [(q.X * FT, q.Y * FT) for q in g.Tessellate()]
            segs += [(ps[i], ps[i + 1]) for i in range(len(ps) - 1)]
        loops = chain(segs)
        if job["kind"] == "up008":
            fs = job.get("facade_sign", -1)
            keep = [L for L in loops if (sum(p[1] for p in L) / len(L)) * fs > 0]
            new_loops = keep
        else:
            x0 = float(job["clip_x"]); side = -1 if x0 < 0 else 1
            big = max(loops, key=area)
            new_loops = []
            for L in loops:
                xs = [p[0] for p in L]
                inside = (min(xs) >= x0) if side < 0 else (max(xs) <= x0)
                outside = (max(xs) <= x0) if side < 0 else (min(xs) >= x0)
                if inside:
                    new_loops.append(L)
                elif outside:
                    continue
                else:
                    c = clip(L, x0 if L is big else (x0 - side * 0.3), side)
                    if c:
                        new_loops.append(c)
        t = Transaction(pd, u"тело однослойной цс"); t.Start()
        pd.Delete(List[ElementId]([c.Id for c in lines]))
        n = 0
        for L in new_loops:
            for i in range(len(L)):
                a = L[i]; b = L[(i + 1) % len(L)]
                pd.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(a[0] / FT, a[1] / FT, 0), XYZ(b[0] / FT, b[1] / FT, 0))); n += 1
        t.Commit()
        r.update(loops_before=len(loops), loops_after=len(new_loops), lines=n)
        if job["kind"] == "side" and job.get("seal_src"):
            # уплотнитель стекла из двухслойного цс-профиля (вне групп, со стороны стекла и фасада), в координатах профиля
            # уплотнитель стекла (линии вне групп и заливки) из двухслойного цс-профиля — только со стороны стекла и фасада;
            # копируется между вложенными семействами CopyElements с пересчётом: вложенный(цс) -> профиль -> вложенный(новый)
            def full_tr(inst):
                # GetTotalTransform не учитывает отражение вложенного (HandFlipped/FacingFlipped) — урок 13.11; без этого
                # уплотнитель у зеркальных краёв переносился на грань без стекла (14.11)
                T_ = inst.GetTotalTransform(); M_ = Transform.Identity
                if inst.HandFlipped:
                    M_.BasisX = XYZ(-1, 0, 0)
                if inst.FacingFlipped:
                    M_.BasisY = XYZ(0, -1, 0)
                return T_.Multiply(M_)
            fi = list(FilteredElementCollector(pd).OfClass(FamilyInstance))[0]; Tinv = full_tr(fi).Inverse
            nd = pd.EditFamily(fi.Symbol.Family)
            sd = doc.EditFamily(fams[job["seal_src"]])
            try:
                sfi = list(FilteredElementCollector(sd).OfClass(FamilyInstance))[0]; ST = full_tr(sfi)
                r["flips"] = [bool(fi.HandFlipped), bool(fi.FacingFlipped), bool(sfi.HandFlipped), bool(sfi.FacingFlipped)]
                snd = sd.EditFamily(sfi.Symbol.Family)
                try:
                    def v_of(dd):
                        return [v for v in FilteredElementCollector(dd).OfClass(View) if not v.IsTemplate and v.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Detail, ViewType.DraftingView)][0]
                    fs = job.get("facade_sign", -1); gs = -1 if x0 < 0 else 1
                    ids = []
                    sketch = set()   # граничные линии заливок копируются вместе с заливкой, отдельно их брать нельзя
                    for fr in FilteredElementCollector(snd).OfClass(FilledRegion):
                        for x in fr.GetDependentElements(None):
                            sketch.add(x.Value)
                    for c in FilteredElementCollector(snd).OfClass(CurveElement):
                        if c.Id.Value in sketch:
                            continue
                        if c.GroupId != ElementId.InvalidElementId or c.GetType().Name not in DET or c.GeometryCurve is None:
                            continue
                        g = c.GeometryCurve.CreateTransformed(ST)
                        ps = [g.GetEndPoint(0), g.GetEndPoint(1)]
                        # seal_x_max: дальняя граница уплотнителя от оси профиля (18,4 — FSC21; у других систем — |clip_x| + 12)
                        if all(p.X * gs > 0 and abs(p.X * FT) < float(job.get("seal_x_max", 18.4)) and p.Y * fs > 0 for p in ps):
                            ids.append(c.Id)
                    for fr in FilteredElementCollector(snd).OfClass(FilledRegion):
                        bb = fr.get_BoundingBox(v_of(snd))
                        if bb:
                            c0 = ST.OfPoint((bb.Min + bb.Max) * 0.5)
                            if c0.X * gs > 0 and c0.Y * fs > 0:
                                ids.append(fr.Id)
                    t = Transaction(nd, u"уплотнитель стекла"); t.Start()
                    try:
                        got = ElementTransformUtils.CopyElements(v_of(snd), List[ElementId](ids), v_of(nd), Tinv.Multiply(ST), CopyPasteOptions())
                        t.Commit()
                    except Exception:
                        t.RollBack(); raise
                    r["seal_copied"] = [len(ids), got.Count]
                finally:
                    snd.Close(False)
            finally:
                sd.Close(False)
            try:
                nd.LoadFamily(pd, LoadOpt())
            finally:
                nd.Close(False)
        xs = [p[0] for L in new_loops for p in L]; ys = [p[1] for L in new_loops for p in L]
        r["bbox"] = [round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1)]
        o = SaveAsOptions(); o.OverwriteExistingFile = True
        r["rfa"] = os.path.join(OUT, job["new"] + u".rfa"); pd.SaveAs(r["rfa"], o)
        r["ok"] = True
    except Exception as ex:
        import traceback
        r["error"] = traceback.format_exc()[-300:]
    finally:
        pd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified" if all(x["ok"] for x in rows) else "partial", "summary": u"копий %d из %d; проект не менялся" % (sum(1 for x in rows if x["ok"]), len(rows)), "rows": rows}
