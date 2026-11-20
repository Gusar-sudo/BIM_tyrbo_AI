# -*- coding: utf-8 -*-
# Профили универсальных столбов (FSC18 М2, FSC05 М3) под угол 135° из угловых «левых» 90°:
# во вложенном 2D-элементе узла всё, кроме стороны стены A (держатель + рамка A: целиком левее x_A в координатах профиля),
# поворачивается на +45° вокруг центра круга (0,0). Силуэт (линии профиля) — заново: выпуклая оболочка всех линий узла.
# Новое семейство: SaveAs в out_dir под новым именем. Проект НЕ меняется.
# Аргументы: jobs [{src_family, new_name}], out_dir, angle_deg (45), a_frac (0.7)
import json, math, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    import io
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
ANG = math.radians(float(args.get("angle_deg", 45)))
byname = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


def pts_of(el):
    out = []
    if isinstance(el, CurveElement):
        out += list(el.GeometryCurve.Tessellate())
    elif isinstance(el, FilledRegion):
        for lp in el.GetBoundaries():
            for c in lp:
                out += list(c.Tessellate())
    elif isinstance(el, Group):
        for mid in el.GetMemberIds():
            out += pts_of(el.Document.GetElement(mid))
    elif isinstance(el, FamilyInstance):
        bb = el.get_BoundingBox(None)
        if bb:
            out += [bb.Min, bb.Max]
    return out


def hull(points):
    p = sorted(set((round(q[0], 5), round(q[1], 5)) for q in points))
    if len(p) < 3:
        return p
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


res = []
for job in args["jobs"]:
    r = {"src": job["src_family"], "new": job["new_name"], "ok": False}
    pdoc = doc.EditFamily(byname[job["src_family"]])
    try:
        fi = list(FilteredElementCollector(pdoc).OfClass(FamilyInstance))[0]
        T = fi.GetTotalTransform()
        nd = pdoc.EditFamily(fi.Symbol.Family)
        try:
            # радиус круга — по самой большой дуге во вложенном элементе
            R = max([ce.GeometryCurve.Radius for ce in FilteredElementCollector(nd).OfClass(CurveElement) if isinstance(ce.GeometryCurve, Arc)] or [0])
            xa = -float(args.get("a_frac", 0.7)) * R
            cand = []
            for el in FilteredElementCollector(nd).WhereElementIsNotElementType():
                if not (isinstance(el, (CurveElement, FilledRegion, Group)) or (isinstance(el, FamilyInstance))):
                    continue
                if el.GroupId != ElementId.InvalidElementId:
                    continue
                if isinstance(el, CurveElement) and el.GetType().Name not in ("DetailLine", "DetailArc", "DetailNurbSpline", "DetailEllipse", "DetailCurve"):
                    continue
                ps = pts_of(el)
                if not ps:
                    continue
                pp = [T.OfPoint(q) for q in ps]
                cand.append((el, min(p.X for p in pp), max(p.X for p in pp), (min(p.Y for p in pp) + max(p.Y for p in pp)) / 2.0))
            # сторона стены A (слева, -X): группа целиком левее 0.5R или выходит за круг влево (держатель) — не трогаем
            keep = [c for c in cand if c[2] < -0.5 * R or c[1] < -1.1 * R]
            rot = [c for c in cand if c not in keep]
            # сторона стены B — по центрам повёрнутых групп, далеко ушедших от оси (ножки/рамка B)
            far = [c[3] for c in rot if abs(c[3]) > 0.5 * R]
            sB = -1 if (sum(far) / len(far) if far else -1) < 0 else 1
            ang_profile = ANG if sB < 0 else -ANG          # B поворачивается от A (к +X)
            det = T.BasisX.X * T.BasisY.Y - T.BasisX.Y * T.BasisY.X
            r["R_mm"] = round(R * FT, 1); r["kept_A"] = len(keep); r["rotated"] = len(rot); r["B_side"] = sB; r["det"] = round(det, 2)
            ids = List[ElementId]([c[0].Id for c in rot])
            # прямоугольники рамок A и B (в координатах вложенного) — для силуэта из 3 контуров
            def nbox(el):
                ps = pts_of(el); return (min(q.X for q in ps), min(q.Y for q in ps), max(q.X for q in ps), max(q.Y for q in ps))
            a_grp = min(keep, key=lambda c: c[1])[0]
            b_grp = max(rot, key=lambda c: abs(c[3]))[0]
            a_box = nbox(a_grp); b_box = nbox(b_grp)
            rot_ang = ang_profile * det
            t = Transaction(nd, u"поворот 45°"); t.Start()
            ElementTransformUtils.RotateElements(nd, ids, Line.CreateBound(XYZ(0, 0, 0), XYZ(0, 0, 1)), ang_profile * det)
            t.Commit()
            allp = []
            for el in FilteredElementCollector(nd).WhereElementIsNotElementType():
                if isinstance(el, CurveElement) and el.GroupId == ElementId.InvalidElementId or isinstance(el, Group):
                    allp += [T.OfPoint(q) for q in pts_of(el)]
            nd.LoadFamily(pdoc, LoadOpt())
        finally:
            nd.Close(False)
        # силуэт заново: выпуклая оболочка
        # у зеркального вложенного элемента реальные координаты в профиле — с обратным знаком Y
        ysg = -1 if fi.Mirrored else 1

        def to_prof(x, y):
            p = T.OfPoint(XYZ(x, y, 0)); return (p.X, ysg * p.Y)

        def rect(box, ang):
            ca, sa = math.cos(ang), math.sin(ang)
            pts = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
            return [to_prof(x * ca - y * sa, x * sa + y * ca) for x, y in pts]
        # силуэт = 3 отдельных замкнутых контура: круг (R-0.3 мм), рамка A, повёрнутая рамка B
        loops = [rect(a_box, 0.0), rect(b_box, rot_ang)]
        t = Transaction(pdoc, u"силуэт 135°"); t.Start()
        old = [ce.Id for ce in FilteredElementCollector(pdoc).OfClass(CurveElement) if ce.GetType().Name in ("DetailLine", "DetailArc", "DetailNurbSpline", "DetailEllipse", "DetailCurve")]
        view = [v for v in FilteredElementCollector(pdoc).OfClass(ViewPlan) if not v.IsTemplate][0]
        pdoc.Delete(List[ElementId](old))
        for lp in loops:
            for i in range(4):
                a, b = lp[i], lp[(i + 1) % 4]
                pdoc.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(a[0], a[1], 0), XYZ(b[0], b[1], 0)))
        rc = R - 0.3 / FT
        pdoc.FamilyCreate.NewDetailCurve(view, Arc.Create(XYZ.Zero, rc, 0.0, math.pi, XYZ.BasisX, XYZ.BasisY))
        pdoc.FamilyCreate.NewDetailCurve(view, Arc.Create(XYZ.Zero, rc, math.pi, 2 * math.pi, XYZ.BasisX, XYZ.BasisY))
        t.Commit()
        clean = [q for lp in loops for q in lp] + [(rc, 0), (-rc, 0), (0, rc), (0, -rc)]
        r["silhouette_loops"] = 3
        r["a_box_mm"] = [round(v * FT, 1) for v in a_box]; r["b_box_mm"] = [round(v * FT, 1) for v in b_box]
        xs = [q[0] * FT for q in clean]; ys = [q[1] * FT for q in clean]
        r["bbox_mm"] = [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)]
        opts = SaveAsOptions(); opts.OverwriteExistingFile = True
        r["rfa"] = os.path.join(args["out_dir"], job["new_name"] + u".rfa")
        pdoc.SaveAs(r["rfa"], opts)
        r["ok"] = True
    except Exception as ex:
        r["error"] = str(ex)[:200]
    finally:
        pdoc.Close(False)
    res.append(r)
__output__ = {"status": "completed_unverified" if all(x["ok"] for x in res) else "partial",
              "summary": u"профилей 135°: %d из %d; проект не изменён" % (sum(1 for x in res if x["ok"]), len(res)), "results": res}
