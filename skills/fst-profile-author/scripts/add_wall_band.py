# -*- coding: utf-8 -*-
# Лента «Дихтунгсбанд» (альбом М2/М3, табл. 10: прокладка 50×3 мм между каркасом и стеной/полом/потолком) в графику
# краевого профиля: серая сплошная заливка band_t × band_w во ВЛОЖЕННОМ «Элементы узлов» у грани профиля со стороны стены.
# Сторона стены: «Правый» (начало стены, низ) — минимальный x собственного контура; «Левый» (конец, верх) — максимальный x.
# Собственный контур (3D-тело) не меняется. Сохраняет КОПИИ .rfa в out_dir; проект не меняется.
# Аргументы: profiles [{name, side: "min"|"max"}] (side можно не задавать — по «Правый/Левый/Нижний/Верхний» в имени),
#            out_dir, band_t_mm (3), band_w_mm (50), fill_rgb [150,150,150],
#            shift_mm (0; 3 — сдвинуть стойку от стены на толщину ленты, лента встаёт на прежнее место грани;
#                      стекло у этого края тогда короче на 3 мм — поправка панелей glass_corrections.py, EDGE_BAND)
import json, os
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):   # большие наборы — файлом
    import io
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
BT = float(args.get("band_t_mm", 3)); BW = float(args.get("band_w_mm", 50))
RGB = args.get("fill_rgb", [150, 150, 150])
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))


class _LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True
        return True

    def OnSharedFamilyFound(self, a, b, src, c):
        src.Value = FamilySource.Family; c.Value = True
        return True


def side_of(name):
    if u"Левый" in name or u"Верхний" in name:
        return "max"
    return "min"


def solid_fill(d):
    for fp in FilteredElementCollector(d).OfClass(FillPatternElement):
        p = fp.GetFillPattern()
        if p.IsSolidFill and p.Target == FillPatternTarget.Drafting:
            return fp.Id
    return None


def band_type(d):
    for ft in FilteredElementCollector(d).OfClass(FilledRegionType):
        if ft.Name == u"FT_Дихтунгсбанд":
            return ft
    base = list(FilteredElementCollector(d).OfClass(FilledRegionType))
    if not base:
        return None
    nt = base[0].Duplicate(u"FT_Дихтунгсбанд")
    sid = solid_fill(d)
    if sid:
        nt.ForegroundPatternId = sid
    nt.ForegroundPatternColor = Color(RGB[0], RGB[1], RGB[2])
    try:
        nt.BackgroundPatternId = ElementId.InvalidElementId
    except Exception:
        pass
    return nt


res = []
for p in args["profiles"]:
    name = p["name"]; r = {"profile": name}
    side = p.get("side") or side_of(name)
    pdoc = doc.EditFamily(fams[name]); nd = None; t = None
    try:
        SH = float(args.get("shift_mm", 0))
        if SH:   # сдвиг стойки от стены: собственный контур и вложенная графика на SH мм в сторону стекла
            mv = XYZ(MM(SH) if side == "min" else -MM(SH), 0, 0)
            ids0 = List[ElementId]([ce.Id for ce in FilteredElementCollector(pdoc).OfClass(CurveElement) if ce.GeometryCurve is not None] +
                                   [fi.Id for fi in FilteredElementCollector(pdoc).OfClass(FamilyInstance)])
            tm = Transaction(pdoc, u"FT: сдвиг стойки от стены"); tm.Start()
            ElementTransformUtils.MoveElements(pdoc, ids0, mv)
            r["shift_commit"] = str(tm.Commit()); r["shifted"] = ids0.Count
        xs = []; ys = []
        for ce in FilteredElementCollector(pdoc).OfClass(CurveElement):
            c = ce.GeometryCurve
            if c is None:
                continue
            for q in (c.GetEndPoint(0), c.GetEndPoint(1)):
                xs.append(q.X); ys.append(q.Y)
        xf = min(xs) if side == "min" else max(xs)
        yc = (min(ys) + max(ys)) / 2
        x0, x1 = (xf - MM(BT), xf) if side == "min" else (xf, xf + MM(BT))
        r.update(side=side, face_mm=round(xf * FT, 2), y_mid_mm=round(yc * FT, 2))
        if args.get("band_in_body"):   # лента в собственном контуре: отдельный прямоугольник (зазор gap до грани — контуры не должны касаться)
            GAP = MM(float(args.get("gap_mm", 0.1)))
            bx0, bx1 = (x0, x1 - GAP) if side == "min" else (x0 + GAP, x1)
            old_own = [ce.Id for ce in FilteredElementCollector(pdoc).OfClass(CurveElement) if ce.GeometryCurve is not None and
                       all(((bx0 - 1e-4 <= q.X <= bx1 + 1e-4) and abs(abs(q.Y - yc) - MM(BW / 2)) < 1e-3) or ((abs(q.X - bx0) < 1e-4 or abs(q.X - bx1) < 1e-4) and abs(q.Y - yc) <= MM(BW / 2) + 1e-4)
                           for q in (ce.GeometryCurve.GetEndPoint(0), ce.GeometryCurve.GetEndPoint(1)))]
            tb = Transaction(pdoc, u"FT: лента в контуре"); tb.Start()
            if old_own:
                pdoc.Delete(List[ElementId](old_own))
            sp = [ce for ce in FilteredElementCollector(pdoc).OfClass(CurveElement) if ce.GeometryCurve is not None][0]
            sk = sp.SketchPlane
            # body_full_depth: в 3D-теле лента на всю глубину профиля — иначе Revit продлевает горизонтальный импост до стены
            # и он виден в зазоре выше/ниже ленты (артефакт 09.11); заливка на плане остаётся band_w_mm
            yb0, yb1 = (min(ys), max(ys)) if args.get("body_full_depth") else (yc - MM(BW / 2), yc + MM(BW / 2))
            q4 = [XYZ(bx0, yb0, 0), XYZ(bx1, yb0, 0), XYZ(bx1, yb1, 0), XYZ(bx0, yb1, 0)]
            made = []
            for i in range(4):
                ln = pdoc.FamilyCreate.NewDetailCurve(pdoc.ActiveView, Line.CreateBound(q4[i], q4[(i + 1) % 4])) if sk is None else \
                    pdoc.FamilyCreate.NewModelCurve(Line.CreateBound(q4[i], q4[(i + 1) % 4]), sk) if isinstance(sp, ModelCurve) else \
                    pdoc.FamilyCreate.NewDetailCurve(sp.OwnerViewId and pdoc.GetElement(sp.OwnerViewId) or pdoc.ActiveView, Line.CreateBound(q4[i], q4[(i + 1) % 4]))
                try:
                    ln.LineStyle = sp.LineStyle
                except Exception:
                    pass
                made.append(ln.Id.Value)
            r["body_commit"] = str(tb.Commit()); r["body_lines"] = len(made); r["body_replaced"] = len(old_own)
        insts = list(FilteredElementCollector(pdoc).OfClass(FamilyInstance))
        if not insts:
            r["error"] = u"нет вложенного"; res.append(r); continue
        fi = insts[0]
        inv = fi.GetTransform().Inverse
        nd = pdoc.EditFamily(fi.Symbol.Family)
        view = [v for v in FilteredElementCollector(nd).OfClass(View) if not v.IsTemplate and v.ViewType in (ViewType.FloorPlan, ViewType.DraftingView, ViewType.Detail, ViewType.EngineeringPlan)]
        view = view[0] if view else [v for v in FilteredElementCollector(nd).OfClass(View) if not v.IsTemplate][0]
        old = [fr.Id for fr in FilteredElementCollector(nd).OfClass(FilledRegion) if nd.GetElement(fr.GetTypeId()).Name == u"FT_Дихтунгсбанд"]
        t = Transaction(nd, u"FT: Дихтунгсбанд"); t.Start()
        if old:
            nd.Delete(List[ElementId](old))
        bt = band_type(nd)
        pts = [XYZ(x0, yc - MM(BW / 2), 0), XYZ(x1, yc - MM(BW / 2), 0), XYZ(x1, yc + MM(BW / 2), 0), XYZ(x0, yc + MM(BW / 2), 0)]
        pts = [inv.OfPoint(q) for q in pts]
        pts = [XYZ(q.X, q.Y, 0) for q in pts]
        loop = CurveLoop()
        for i in range(4):
            loop.Append(Line.CreateBound(pts[i], pts[(i + 1) % 4]))
        loops = List[CurveLoop](); loops.Add(loop)
        fr = FilledRegion.Create(nd, bt.Id, view.Id, loops)
        st = t.Commit(); t = None
        bb = fr.get_BoundingBox(view)
        r["nested"] = fi.Symbol.Family.Name
        r["band_nested_bb_mm"] = [round(bb.Min.X * FT, 2), round(bb.Max.X * FT, 2), round(bb.Min.Y * FT, 2), round(bb.Max.Y * FT, 2)] if bb else None
        r["replaced_old"] = len(old); r["commit"] = str(st)
        nd.LoadFamily(pdoc, _LO())
        nd.Close(False); nd = None
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        out = os.path.join(OUT, (p.get("save_as") or name) + ".rfa")   # save_as — копия под новым именем (общие с дверью/свободным краем)
        pdoc.SaveAs(out, so)
        r["rfa"] = out
    except Exception as ex:
        r["error"] = str(ex)
    finally:
        if t is not None and t.HasStarted() and not t.HasEnded():
            t.RollBack()
        if nd is not None:
            nd.Close(False)
        pdoc.Close(False)
    res.append(r)
bad = [x for x in res if x.get("error")]
__output__ = {"status": "completed_unverified" if not bad else "partial", "summary": u"профилей %d, ошибок %d; копии в %s, проект не менялся" % (len(res), len(bad), OUT), "result": res}
