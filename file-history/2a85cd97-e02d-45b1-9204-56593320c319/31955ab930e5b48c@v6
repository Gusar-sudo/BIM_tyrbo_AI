# -*- coding: utf-8 -*-
# Образцы узлов (всё откатывается, если keep = false):
#  W1 «за подвесной потолок»: стена L×H_slab до перекрытия, ригель на H_ceil, подвесной потолок, выше ригеля — пустые панели,
#     стойки выше ригеля — types.above_post / above_wall_start / above_wall_end, ригель — types.ceil_transom, верхнего профиля нет.
#  W2 «проём»: стена L×H, средний пролёт (bay) без заполнения до H_head, по бокам types.open_left / open_right,
#     над проёмом types.open_head, нижнего профиля в проёме нет.
# Виды PNG: фасады 1:20, планы 1:2 (над потолком — разрез на H_ceil+400), разрезы 1:2 поперёк стены, 3D.
#  Цельностеклянные (cs: true): ниже ригеля — стыки стекло–стекло (линии сетки только ниже ригеля), выше ригеля — свои стойки
#     с шагом post_step_mm (600–1200), не совпадающие со стыками стёкол; проём (W2) не строится.
# Аргументы: walls [{wall_type, types{...}, cs, tag}] (или один wall_type + types), out_dir, L (3000), grid (1000), post_step_mm (750),
#            H_slab (3500), H_ceil (2700), H (3000), H_head (2100), prep (путь JSON для include PREP), keep (false), px (1400),
#            panel_empty ("Пусто"), views ["all"|"short"]
import json, os, io
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    _a = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read()); _a.update(dict((k, v) for k, v in args.items() if k != "args_file")); args = _a
if isinstance(args.get("prep"), str):
    args["prep"] = json.loads(io.open(args["prep"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8; MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
L = float(args.get("L", 3000)); G = float(args.get("grid", 1000))
HS = float(args.get("H_slab", 3500)); HC = float(args.get("H_ceil", 2700)); H = float(args.get("H", 3000)); HH = float(args.get("H_head", 2100))
level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
Z0 = level.Elevation
vft = dict((t.ViewFamily, t) for t in FilteredElementCollector(doc).OfClass(ViewFamilyType))
HIDE = [BuiltInCategory.OST_Levels, BuiltInCategory.OST_Grids, BuiltInCategory.OST_Elev, BuiltInCategory.OST_Sections, BuiltInCategory.OST_CLines,
        BuiltInCategory.OST_SectionHeads, BuiltInCategory.OST_Viewers]
res = {"w1": {}, "w2": {}}
existing = set(v.Name for v in FilteredElementCollector(doc).OfClass(View))


def uname(n):
    k = n; i = 2
    while k in existing:
        k = u"%s (%d)" % (n, i); i += 1
    existing.add(k); return k


def tidy(v):
    for b in HIDE:
        try:
            v.SetCategoryHidden(ElementId(b), True)
        except Exception:
            pass


def mt(name):
    r = [m for m in FilteredElementCollector(doc).OfClass(MullionType) if Element.Name.GetValue(m) == name]
    if not r:
        raise Exception(u"нет типа импоста " + name)
    return r[0]


def classify(w, P0):
    out = []
    for mid in w.CurtainGrid.GetMullionIds():
        m = doc.GetElement(mid); bb = m.get_BoundingBox(None)
        if bb is None:
            continue
        vert = (bb.Max.Z - bb.Min.Z) > (bb.Max.X - bb.Min.X)
        out.append((m, vert, ((bb.Min.X + bb.Max.X) / 2 - P0.X) * FT, ((bb.Min.Z + bb.Max.Z) / 2 - Z0) * FT, (bb.Min.Z - Z0) * FT, (bb.Max.Z - Z0) * FT))
    return out


def set_type(m, t):
    if m.Pinned:   # импост, добавленный вручную (AddMullions), не закреплён и не открепляется
        m.Pinned = False
    if m.GetTypeId() != t.Id:
        m.ChangeTypeId(t.Id)


def section_across(x, y, z0, z1, half, name, scale=2):
    """Разрез поперёк стены в точке x (смотрит вдоль +X), окно half мм в стороны от оси стены, по высоте z0..z1."""
    tr = Transform.Identity; tr.Origin = XYZ(x, y, Z0)
    tr.BasisX = XYZ(0, -1, 0); tr.BasisY = XYZ.BasisZ; tr.BasisZ = XYZ(-1, 0, 0)
    sb = BoundingBoxXYZ(); sb.Transform = tr
    sb.Min = XYZ(-MM(half), MM(z0), -MM(40)); sb.Max = XYZ(MM(half), MM(z1), 0)
    v = ViewSection.CreateSection(doc, vft[ViewFamily.Section].Id, sb); v.Name = uname(name)
    v.Scale = scale; v.DetailLevel = ViewDetailLevel.Fine; tidy(v); return v


def facade(P0, Lw, Hw, name):
    tr = Transform.Identity; tr.Origin = XYZ(P0.X + MM(Lw / 2), P0.Y - MM(500), Z0)
    tr.BasisX = XYZ.BasisX; tr.BasisY = XYZ.BasisZ; tr.BasisZ = XYZ(0, -1, 0)
    sb = BoundingBoxXYZ(); sb.Transform = tr
    sb.Min = XYZ(-MM(Lw / 2 + 300), MM(-150), MM(-1000)); sb.Max = XYZ(MM(Lw / 2 + 300), MM(Hw + 350), 0)
    v = ViewSection.CreateSection(doc, vft[ViewFamily.Section].Id, sb); v.Name = uname(name)
    v.Scale = 20; v.DetailLevel = ViewDetailLevel.Fine; tidy(v); return v


def plan(cx, y, cut, name, half=130):
    v = ViewPlan.Create(doc, vft[ViewFamily.FloorPlan].Id, level.Id); v.Name = uname(name)
    v.Scale = 2; v.DetailLevel = ViewDetailLevel.Fine
    vr = v.GetViewRange()
    vr.SetOffset(PlanViewPlane.TopClipPlane, MM(max(cut + 200, HS + 300))); vr.SetOffset(PlanViewPlane.CutPlane, MM(cut))
    vr.SetOffset(PlanViewPlane.BottomClipPlane, MM(cut - 300)); vr.SetOffset(PlanViewPlane.ViewDepthPlane, MM(cut - 300))
    v.SetViewRange(vr)
    cb = v.CropBox
    cb.Min = XYZ(cx - MM(half), y - MM(half * 0.75), cb.Min.Z); cb.Max = XYZ(cx + MM(half), y + MM(half * 0.75), cb.Max.Z)
    v.CropBox = cb; v.CropBoxActive = True; v.CropBoxVisible = False; tidy(v); return v


def view3d(a, b, d, name):
    v = View3D.CreateIsometric(doc, vft[ViewFamily.ThreeDimensional].Id); v.Name = uname(name)
    v.DetailLevel = ViewDetailLevel.Fine; v.DisplayStyle = DisplayStyle.ShadingWithEdges
    bb = BoundingBoxXYZ(); bb.Min = a; bb.Max = b; v.SetSectionBox(bb)
    f = XYZ(d[0], d[1], d[2]).Normalize(); up = (XYZ.BasisZ - f.Multiply(XYZ.BasisZ.DotProduct(f))).Normalize()
    c = (a + b) / 2; v.SetOrientation(ViewOrientation3D(c - f.Multiply(MM(20000)), up, f))
    cb = v.CropBox; inv = cb.Transform.Inverse
    pts = [inv.OfPoint(XYZ(x, y, z)) for x in (a.X, b.X) for y in (a.Y, b.Y) for z in (a.Z, b.Z)]
    cb.Min = XYZ(min(p.X for p in pts), min(p.Y for p in pts), cb.Min.Z); cb.Max = XYZ(max(p.X for p in pts), max(p.Y for p in pts), cb.Max.Z)
    v.CropBox = cb; v.CropBoxActive = True; v.CropBoxVisible = False; tidy(v); return v




class _JoinOk(IFailuresPreprocessor):
    """Разрывы линий сетки у цельностеклянных: «импосты между присоединяемыми панелями будут удалены» — штатное решение Revit."""
    log = []

    def PreprocessFailures(self, fa):
        for f in list(fa.GetFailureMessages()):
            _JoinOk.log.append([str(f.GetSeverity()), f.GetDescriptionText()[:90], [i.Value for i in f.GetFailingElementIds()][:4]])
            if f.GetSeverity() == FailureSeverity.Warning:
                fa.DeleteWarning(f)
            elif f.GetSeverity() == FailureSeverity.Error and f.HasResolutions():
                fa.ResolveFailure(f)
        return FailureProcessingResult.ProceedWithCommit


def build(entry, idx):
    r = {"wall_type": entry["wall_type"], "tag": entry.get("tag", "%02d" % (idx + 1)), "cs": bool(entry.get("cs"))}
    T = dict((k, mt(v)) for k, v in entry["types"].items())
    wt = [w for w in FilteredElementCollector(doc).OfClass(WallType) if Element.Name.GetValue(w) == entry["wall_type"]][0]
    cs = r["cs"]; PS = float(args.get("post_step_mm", 750)); tag = r["tag"]
    ox_, oy_ = entry.get("origin_mm") or [OX + 6000 * idx, OY]   # своё место образца (библиотека) или ряд по idx
    P1 = XYZ(MM(ox_), MM(oy_), Z0); P2 = XYZ(MM(ox_), MM(oy_ - 4000 if entry.get("origin_mm") else oy_ + 4000), Z0)
    if entry.get("only_w2"):   # временная стена до потолка — в стороне, чтобы не перекрывать уже стоящий образец
        P1 = P1 + XYZ(0, MM(-300000), 0)
    CTX = args.get("context", True)   # стены-примыкания, перекрытие, подвесной потолок — только для проб
    t = Transaction(doc, u"образцы %s" % tag)
    if cs and args.get("use_pp"):   # 11.11: обработчик отказов ломает фиксацию (стена пропадает) — по умолчанию не ставить
        fo = t.GetFailureHandlingOptions(); fo.SetFailuresPreprocessor(_JoinOk()); t.SetFailureHandlingOptions(fo)
    t.Start()
    try:
        w1 = Wall.Create(doc, Line.CreateBound(P1, P1 + XYZ.BasisX * MM(L)), wt.Id, level.Id, MM(HS), 0, False, False)
        pairs = [(w1, P1, HS)]
        w2 = None
        if not cs or entry.get("cs_open"):   # цс-проём: стойки по краям до потолка, над проёмом стекло
            w2 = Wall.Create(doc, Line.CreateBound(P2, P2 + XYZ.BasisX * MM(L)), wt.Id, level.Id, MM(H), 0, False, False)
            pairs.append((w2, P2, H))
        for w, P, h in pairs:
            WallUtils.DisallowWallJoinAtEnd(w, 0); WallUtils.DisallowWallJoinAtEnd(w, 1)
            th = basic.Width if basic else 0
            for xx in ((P.X - th / 2, P.X + MM(L) + th / 2) if (basic and CTX) else ()):
                aw = Wall.Create(doc, Line.CreateBound(XYZ(xx, P.Y - MM(800), Z0), XYZ(xx, P.Y + MM(800), Z0)), basic.Id, level.Id, MM(h), 0, False, False)
                WallUtils.DisallowWallJoinAtEnd(aw, 0); WallUtils.DisallowWallJoinAtEnd(aw, 1)
        doc.Regenerate()
        glu = w1.CurtainGrid.AddGridLine(True, P1 + XYZ.BasisX * MM(G / 2) + XYZ(0, 0, MM(HC)), False)
        doc.Regenerate()
        n = int(round(L / G))
        if cs:   # стыки стёкол — только ниже ригеля; стойки над потолком — свой шаг, только выше ригеля
            # Проверено 11.11: линия «на один пролёт» (oneSegmentOnly) даёт ошибку «импосты между присоединяемыми панелями будут
            # удалены» и откат; надёжно так: линии на всю высоту -> панели над ригелем пустые -> удалить импосты на лишних
            # кусках -> RemoveSegment этих кусков.
            joints = [G * i for i in range(1, n)]
            posts = []; k = 1
            while PS * k < L - 150:
                posts.append(PS * k); k += 1
            lines = {}
            for x in sorted(set(joints + posts)):
                lines[x] = w1.CurtainGrid.AddGridLine(False, P1 + XYZ.BasisX * MM(x) + XYZ(0, 0, MM(HC / 2)), False)
            doc.Regenerate()
            for pid in w1.CurtainGrid.GetPanelIds():
                p = doc.GetElement(pid); bb = p.get_BoundingBox(None)
                if bb is not None and ((bb.Min.Z + bb.Max.Z) / 2 - Z0) * FT > HC and empty is not None:
                    p.Pinned = False; p.ChangeTypeId(empty.Id)
            doc.Regenerate()
            cut = {}   # x -> какую часть убрать: "low" (только стойка над потолком) или "up" (только стык стёкол)
            for x in lines:
                isj = any(abs(x - j) < 20 for j in joints); isp = any(abs(x - q) < 20 for q in posts)
                if isp and not isj:
                    cut[x] = "low"
                elif isj and not isp:
                    cut[x] = "up"
            dl = []
            for mid in w1.CurtainGrid.GetMullionIds():
                m = doc.GetElement(mid); bb = m.get_BoundingBox(None)
                if bb is None or (bb.Max.Z - bb.Min.Z) <= (bb.Max.X - bb.Min.X):
                    continue
                xc = ((bb.Min.X + bb.Max.X) / 2 - P1.X) * FT; zc = ((bb.Min.Z + bb.Max.Z) / 2 - Z0) * FT
                for x, part in cut.items():
                    if abs(xc - x) < 20 and ((part == "low" and zc < HC) or (part == "up" and zc > HC)):
                        m.Pinned = False; dl.append(m.Id)
            if dl:
                doc.Delete(List[ElementId](dl))
            doc.Regenerate()
            rs = 0
            for x, part in cut.items():
                for c in list(lines[x].AllSegmentCurves):
                    zlo = (min(c.GetEndPoint(0).Z, c.GetEndPoint(1).Z) - Z0) * FT
                    if (part == "low" and zlo < HC - 100) or (part == "up" and zlo > HC - 100):
                        lines[x].RemoveSegment(c); rs += 1
            doc.Regenerate()
            r["cs_grid"] = {"joints": joints, "posts": posts, "mullions_removed": len(dl), "segments_removed": rs}
            # у цельностеклянного типа на горизонтальных линиях импоста нет — ригель ставим явно
            segs = list(glu.AllSegmentCurves)
            if segs:
                glu.AddMullions(segs[0], T["ceil_transom"], False)
            doc.Regenerate()
        else:
            for i in range(1, n):
                w1.CurtainGrid.AddGridLine(False, P1 + XYZ.BasisX * MM(G * i) + XYZ(0, 0, 1), False)
        if w2 is not None:
            for i in range(1, n):
                w2.CurtainGrid.AddGridLine(False, P2 + XYZ.BasisX * MM(G * i) + XYZ(0, 0, 1), False)
            glh = w2.CurtainGrid.AddGridLine(True, P2 + XYZ.BasisX * MM(G / 2) + XYZ(0, 0, MM(HH)), False)
            if cs:   # цс: горизонталь только над проёмом (у цс на горизонтали импостов нет — куски убираются без слияния импостов)
                doc.Regenerate()
                xa_, xb_ = G * int(args.get("bay", 1)), G * (int(args.get("bay", 1)) + 1)
                keep_seg = None
                for c in list(glh.AllSegmentCurves):
                    xm = ((c.GetEndPoint(0).X + c.GetEndPoint(1).X) / 2 - P2.X) * FT
                    if xa_ < xm < xb_:
                        keep_seg = c
                    else:
                        glh.RemoveSegment(c)
                doc.Regenerate()
                segs = [c for c in glh.AllSegmentCurves if xa_ < ((c.GetEndPoint(0).X + c.GetEndPoint(1).X) / 2 - P2.X) * FT < xb_]
                if segs:
                    glh.AddMullions(segs[0], T["open_head"], True)
        doc.Regenerate()
        try:
            if not CTX:
                raise Exception(u"без окружения")
            ftp = [f for f in FilteredElementCollector(doc).OfClass(FloorType) if not f.IsFoundationSlab][0]
            q = [XYZ(P1.X - MM(600), P1.Y - MM(1200), Z0), XYZ(P1.X + MM(L + 600), P1.Y - MM(1200), Z0), XYZ(P1.X + MM(L + 600), P1.Y + MM(1200), Z0), XYZ(P1.X - MM(600), P1.Y + MM(1200), Z0)]
            fl = Floor.Create(doc, List[CurveLoop]([CurveLoop.Create(List[Curve]([Line.CreateBound(q[i], q[(i + 1) % 4]) for i in range(4)]))]), ftp.Id, level.Id)
            thk = ftp.GetCompoundStructure().GetWidth() if ftp.GetCompoundStructure() else MM(200)
            fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(MM(HS) + thk)
        except Exception as ex:
            r["slab"] = str(ex)
        try:
            if not CTX:
                raise Exception(u"без окружения")
            ct = [c for c in FilteredElementCollector(doc).OfClass(CeilingType)][0]
            for y0, y1 in ((P1.Y + MM(40), P1.Y + MM(1100)), (P1.Y - MM(1100), P1.Y - MM(40))):
                q = [XYZ(P1.X, y0, Z0), XYZ(P1.X + MM(L), y0, Z0), XYZ(P1.X + MM(L), y1, Z0), XYZ(P1.X, y1, Z0)]
                c = Ceiling.Create(doc, List[CurveLoop]([CurveLoop.Create(List[Curve]([Line.CreateBound(q[i], q[(i + 1) % 4]) for i in range(4)]))]), ct.Id, level.Id)
                c.get_Parameter(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM).Set(MM(HC + 25))
        except Exception as ex:
            r["ceiling"] = str(ex)
        ch = []; dl = []
        for m, vert, xc, zc, zmin, zmax in classify(w1, P1):
            if vert and zc > HC and zmin > HC - 100:   # импост над ригелем (нижний конец может заходить за ригель)
                k = "above_wall_start" if xc < 60 else ("above_wall_end" if xc > L - 60 else "above_post")
                set_type(m, T[k]); ch.append(k)
            elif not vert and abs(zc - HC) < 60:
                set_type(m, T["ceil_transom"]); ch.append("ceil_transom")
            elif not vert and zc > HS - 120:
                m.Pinned = False; dl.append(m.Id)
        if dl:
            doc.Delete(List[ElementId](dl))
        np = 0
        for pid in w1.CurtainGrid.GetPanelIds():
            p = doc.GetElement(pid); bb = p.get_BoundingBox(None)
            if bb is not None and ((bb.Min.Z + bb.Max.Z) / 2 - Z0) * FT > HC and empty is not None:
                p.Pinned = False; p.ChangeTypeId(empty.Id); np += 1
        r["w1"] = {"changed": dict((k, ch.count(k)) for k in set(ch)), "deleted_top": len(dl), "empty_panels": np}
        bay = int(args.get("bay", 1)); xa, xb = G * bay, G * (bay + 1)
        if w2 is not None:
            ch = []; dl = []
            for m, vert, xc, zc, zmin, zmax in classify(w2, P2):
                if vert and zmax < HH + 5 and abs(xc - xa) < 60:
                    set_type(m, T["open_left"]); ch.append("open_left")
                elif vert and zmax < HH + 5 and abs(xc - xb) < 60:
                    set_type(m, T["open_right"]); ch.append("open_right")
                elif vert and zc > HH and (abs(xc - xa) < 60 or abs(xc - xb) < 60) and "post_above_open" in T:
                    set_type(m, T["post_above_open"]); ch.append("post_above_open")
                elif not vert and abs(zc - HH) < 60 and xa < xc < xb:
                    set_type(m, T["open_head"]); ch.append("open_head")
                elif not vert and zc < 120 and xa < xc < xb:
                    m.Pinned = False; dl.append(m.Id)
            if dl:
                doc.Delete(List[ElementId](dl))
            np = 0
            for pid in w2.CurtainGrid.GetPanelIds():
                p = doc.GetElement(pid); bb = p.get_BoundingBox(None)
                if bb is None:
                    continue
                xc = ((bb.Min.X + bb.Max.X) / 2 - P2.X) * FT; zc = ((bb.Min.Z + bb.Max.Z) / 2 - Z0) * FT
                if xa < xc < xb and zc < HH and empty is not None:
                    p.Pinned = False; p.ChangeTypeId(empty.Id); np += 1
            r["w2"] = {"changed": dict((k, ch.count(k)) for k in set(ch)), "deleted_bottom": len(dl), "empty_panels": np}
        r["commit"] = str(t.Commit())
    except Exception:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        raise
    if not w1.IsValidObject:
        raise Exception(u"стена удалена при фиксации: " + r["commit"])
    own = set([w1.Id.Value] + [i.Value for i in w1.CurtainGrid.GetMullionIds()] + ([w2.Id.Value] + [i.Value for i in w2.CurtainGrid.GetMullionIds()] if w2 else []))
    r["warnings"] = sorted(set(wr.GetDescriptionText() for wr in doc.GetWarnings() if any(i.Value in own for i in wr.GetFailingElements())))
    if entry.get("only_w2") and w2 is not None:   # в библиотеке участок до потолка уже стоит — добавить только проём
        t = Transaction(doc, u"только проём %s" % tag); t.Start()
        doc.Delete(w1.Id); r["w1_removed"] = True; t.Commit()
        r["w2_id"] = w2.Id.Value
    # виды (views: "none" — без видов, для образцов в библиотеке)
    if args.get("views", "all") == "none":
        r["views"] = 0
        return r
    t = Transaction(doc, u"виды %s" % tag); t.Start()
    try:
        xp = PS if cs else G
        V = [(facade(P1, L, HS, u"FT обр %s потолок фасад" % tag), u"%s_1_потолок_фасад" % tag),
             (plan(P1.X + MM(xp), P1.Y, HC + 400, u"FT обр %s потолок план стойка" % tag), u"%s_2_потолок_план_стойка" % tag),
             (plan(P1.X + MM(40), P1.Y, HC + 400, u"FT обр %s потолок план у стены" % tag), u"%s_3_потолок_план_стена" % tag),
             (section_across(P1.X + MM(G / 2 if not cs else (G + PS) / 2 - G / 2), P1.Y, HC - 150, HC + 150, 130, u"FT обр %s потолок ригель" % tag), u"%s_4_потолок_ригель_разрез" % tag)]
        if cs:
            V.append((plan(P1.X + MM(G), P1.Y, HC - 400, u"FT обр %s стык стёкол" % tag), u"%s_5_потолок_стык_стёкол_ниже" % tag))
        if args.get("views", "all") == "all":
            V.append((view3d(XYZ(P1.X - MM(150), P1.Y - MM(400), Z0 + MM(HC - 500)), XYZ(P1.X + MM(max(G, PS) * 2 + 300), P1.Y + MM(400), Z0 + MM(HS + 50)), [1, 1.6, -0.5], u"FT обр %s потолок 3D" % tag), u"%s_6_потолок_3D" % tag))
        if w2 is not None:
            V += [(facade(P2, L, H, u"FT обр %s проём фасад" % tag), u"%s_7_проём_фасад" % tag),
                  (plan(P2.X + MM(xa), P2.Y, 1000, u"FT обр %s проём план левая" % tag), u"%s_8_проём_план_левая" % tag),
                  (plan(P2.X + MM(xb), P2.Y, 1000, u"FT обр %s проём план правая" % tag), u"%s_9_проём_план_правая" % tag),
                  (section_across(P2.X + MM((xa + xb) / 2), P2.Y, HH - 150, HH + 150, 130, u"FT обр %s над проёмом" % tag), u"%s_10_проём_над_проёмом_разрез" % tag)]
            if cs:
                V.append((plan(P2.X + MM(xa), P2.Y, HH + 400, u"FT обр %s стойка выше проёма" % tag), u"%s_11_проём_план_стойка_выше_проёма" % tag))
            if args.get("views", "all") == "all":
                V.append((view3d(XYZ(P2.X + MM(xa - 300), P2.Y - MM(400), Z0 - MM(50)), XYZ(P2.X + MM(xb + 300), P2.Y + MM(400), Z0 + MM(HH + 400)), [1, 1.6, -0.5], u"FT обр %s проём 3D" % tag), u"%s_12_проём_3D" % tag))
        t.Commit()
    except Exception:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        raise
    for v, key in V:
        opt = ImageExportOptions(); opt.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); opt.SetViewsAndSheets(ids)
        opt.FilePath = os.path.join(OUT, key); opt.ZoomType = ZoomFitType.FitToPage; opt.PixelSize = int(args.get("px", 1400))
        opt.HLRandWFViewsFileType = ImageFileType.PNG; opt.ShadowViewsFileType = ImageFileType.PNG; opt.ImageResolution = ImageResolution.DPI_300
        doc.ExportImage(opt)
    r["views"] = len(V)
    return r


tg = TransactionGroup(doc, u"FT: образцы подвесной потолок / проём"); tg.Start()
keep = bool(args.get("keep", False))
res = {"walls": []}
try:
    if args.get("prep") and "PREP" in globals():
        pr = PREP(doc, args["prep"]); res["prep_fail"] = pr.get("swap_fail"); res["prep_created"] = len(pr.get("types_created") or [])
    empty = [s for s in FilteredElementCollector(doc).OfClass(PanelType) if Element.Name.GetValue(s) == args.get("panel_empty", u"Пусто")]
    empty = empty[0] if empty else None
    bl = sorted([w for w in FilteredElementCollector(doc).OfClass(WallType) if w.Kind == WallKind.Basic], key=lambda w: abs(w.Width - MM(150)))
    basic = bl[0] if bl else None
    OX, OY = [float(a) for a in args.get("origin_mm", [140000, 620000])]
    walls = args.get("walls") or [{"wall_type": args["wall_type"], "types": args["types"], "cs": args.get("cs", False)}]
    for i, e in enumerate(walls):
        checkpoint(u"образец %s" % e["wall_type"], i, len(walls))
        try:
            res["walls"].append(build(e, i))
        except Exception as ex:
            import traceback
            res["walls"].append({"wall_type": e["wall_type"], "error": str(ex), "where": traceback.format_exc()[-300:], "failures": _JoinOk.log[-12:]})
    res["n_warnings"] = len(doc.GetWarnings())
finally:
    if keep:
        tg.Assimilate()
    else:
        tg.RollBack()
bad = [w for w in res["walls"] if w.get("error") or w.get("warnings")]
__output__ = {"status": "completed_unverified" if not bad else "partial", "summary": u"образцов %d, с ошибками/предупр. %d; %s" % (len(res["walls"]), len(bad), u"СОХРАНЕНО в модели" if keep else u"всё откатано"), "result": res}
