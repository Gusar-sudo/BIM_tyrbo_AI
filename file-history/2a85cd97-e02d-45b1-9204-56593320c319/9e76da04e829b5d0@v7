# -*- coding: utf-8 -*-
# Показ перегородки целиком для человека: витраж между двумя стенами (стена — стекло — стык — стекло — стена),
# виды плана с ТОЧНО известными рамками (общий + узлы), цвет материалов разреза, PNG каждого вида
# + JSON с рамками и координатами деталей (стекло, импосты) — подписи потом ставятся на картинку по координатам.
# Всё в группе транзакций и откатывается. Аргументы: wall_type, length_mm, panel, end_left, end_right, mid,
# preload_rfas, mullion_types_create [{base_type,new_type,new_profile}], material_cut_rgb, out_dir, px, node_half_mm, origin_mm
import json, io, os, clr
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.FloorPlan][0]
res = {"views": {}}
tg = TransactionGroup(doc, u"показ перегородки (откат)"); tg.Start()
try:
    t = Transaction(doc, u"семейства и типы"); t.Start()
    for f in args.get("preload_rfas", []):
        doc.LoadFamily(f, LO(), clr.Reference[Family]())
    fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
    mt = dict((m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
    for it in args.get("mullion_types_create", []):
        if it["new_type"] not in mt:
            nt = mt[it["base_type"]].Duplicate(it["new_type"]); mt[it["new_type"]] = nt
        mt[it["new_type"]].get_Parameter(BuiltInParameter.MULLION_PROFILE).Set(list(fams[it["new_profile"]].GetFamilySymbolIds())[0])
        for k_, v_ in (it.get("params_mm") or {}).items():
            mt[it["new_type"]].LookupParameter(k_).Set(float(v_) / FT)
    sp = [fp for fp in FilteredElementCollector(doc).OfClass(FillPatternElement) if fp.GetFillPattern().IsSolidFill][0]
    mats = dict((m.Name, m) for m in FilteredElementCollector(doc).OfClass(Material))
    for mn, c in args.get("material_cut_rgb", {}).items():
        if mn in mats:
            mats[mn].CutForegroundPatternId = sp.Id; mats[mn].CutForegroundPatternColor = Color(c[0], c[1], c[2])
    t.Commit()
    ox, oy = [MM(v) for v in args.get("origin_mm", [20000, 340000])]
    Lw = MM(args.get("length_mm", 1800))
    P0 = XYZ(ox, oy, level.Elevation); P1 = XYZ(ox + Lw, oy, level.Elevation)
    t = Transaction(doc, u"перегородка"); t.Start()
    wt = [w for w in FilteredElementCollector(doc).OfClass(WallType) if w.Name == args["wall_type"]][0]
    w = Wall.Create(doc, Line.CreateBound(P0, P1), wt.Id, level.Id, MM(2700), 0, False, False)
    doc.Regenerate()
    w.CurtainGrid.AddGridLine(False, XYZ(ox + Lw / 2, oy, level.Elevation + 1), False)
    if args.get("hgrid_mm"):
        doc.Regenerate()
        w.CurtainGrid.AddGridLine(True, XYZ(ox + Lw / 4, oy, level.Elevation + MM(args["hgrid_mm"])), False)
    doc.Regenerate()

    def near(pt):
        best = None
        for mid in w.CurtainGrid.GetMullionIds():
            m = doc.GetElement(mid); bb = m.get_BoundingBox(None)
            if bb is None or (bb.Max.Z - bb.Min.Z) < 1.0:
                continue
            c = (bb.Min + bb.Max) * 0.5; dd = abs(c.X - pt.X)
            if best is None or dd < best[0]:
                best = (dd, m)
        return best[1]
    mL, mM, mR = near(P0), near(XYZ(ox + Lw / 2, oy, 0)), near(P1)
    for m, k in ((mL, "end_left"), (mM, "mid"), (mR, "end_right")):
        if args.get(k):   # иначе — импост из типа стены
            m.Pinned = False; m.ChangeTypeId(mt[args[k]].Id)
    # горизонтальные (пол/потолок)
    hz = []
    for mid_ in w.CurtainGrid.GetMullionIds():
        m = doc.GetElement(mid_); bb = m.get_BoundingBox(None)
        if bb is not None and (bb.Max.Z - bb.Min.Z) < 1.0:
            hz.append(m)
    hz.sort(key=lambda m: m.get_BoundingBox(None).Min.Z)
    res["horizontal"] = []
    for m in hz:
        k = "end_bottom" if m.get_BoundingBox(None).Min.Z < level.Elevation + MM(1000) else "end_top"
        if args.get(k):
            m.Pinned = False; m.ChangeTypeId(mt[args[k]].Id)
        res["horizontal"].append(doc.GetElement(m.GetTypeId()).get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())
    pst = [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels) if s.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == args["panel"] and (not args.get("panel_family") or s.Family.Name == args["panel_family"])][0]
    res["panel_family"] = pst.Family.Name
    for k_, v_ in args.get("panel_type_set_mm", {}).items():   # пробная правка типа панели (откатится)
        pst.LookupParameter(k_).Set(float(v_) / FT)
    wt.get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).Set(pst.Id)   # панель по умолчанию в типе (откатится)
    for pid in w.CurtainGrid.GetPanelIds():
        doc.GetElement(pid).ChangeTypeId(pst.Id)
    doc.Regenerate()
    # стены здания у концов — снаружи импостов
    basic = [x for x in FilteredElementCollector(doc).OfClass(WallType) if x.Kind == WallKind.Basic][0]
    hw = basic.Width / 2.0
    bbL = mL.get_BoundingBox(None); bbR = mR.get_BoundingBox(None)
    xl = bbL.Min.X - hw; xr = bbR.Max.X + hw
    for xx in (xl, xr):
        Wall.Create(doc, Line.CreateBound(XYZ(xx, oy - MM(400), level.Elevation), XYZ(xx, oy + MM(400), level.Elevation)), basic.Id, level.Id, MM(2700), 0, False, False)
    doc.Regenerate()
    # стены рядом пересоздают панели витража по типу стены — тип панели ставим ещё раз
    for pid in w.CurtainGrid.GetPanelIds():
        pn = doc.GetElement(pid)
        if pn.GetTypeId() != pst.Id:
            pn.ChangeTypeId(pst.Id)
    doc.Regenerate()
    if args.get("post_side"):   # заход стекла за край среднего столба: minus — панель слева от него, plus — справа
        for pid in w.CurtainGrid.GetPanelIds():
            pn = doc.GetElement(pid)
            vs = pn.Symbol.LookupParameter(u"Выступ сбоку").AsDouble() * FT
            bb = pn.get_BoundingBox(None)
            if (bb.Min.X + bb.Max.X) / 2 < ox + Lw / 2:
                pn.LookupParameter(u"FT_Стекло_Поправка_Справа").Set(MM(float(args["post_side"]["minus"]) - vs))
            else:
                pn.LookupParameter(u"FT_Стекло_Поправка_Слева").Set(MM(float(args["post_side"]["plus"]) - vs))
        doc.Regenerate()
    res["panels_after_walls"] = [doc.GetElement(pid).Symbol.Family.Name for pid in w.CurtainGrid.GetPanelIds()]
    # координаты деталей (мм от P0)
    def bbmm(e):
        bb = e.get_BoundingBox(None)
        return [round((bb.Min.X - ox) * FT, 1), round((bb.Max.X - ox) * FT, 1), round((bb.Min.Y - oy) * FT, 1), round((bb.Max.Y - oy) * FT, 1)]
    glass = []
    opt = Options(); opt.ComputeReferences = False
    for pid in w.CurtainGrid.GetPanelIds():
        pn = doc.GetElement(pid)
        for g in pn.get_Geometry(opt):
            gi = g.GetInstanceGeometry() if isinstance(g, GeometryInstance) else [g]
            for s in gi:
                if isinstance(s, Solid) and s.Volume > 0:
                    mid = list(s.Faces)[0].MaterialElementId if s.Faces.Size else ElementId.InvalidElementId
                    mn = doc.GetElement(mid).Name if mid != ElementId.InvalidElementId and doc.GetElement(mid) else ""
                    if u"Стекло" in mn:
                        bb = s.GetBoundingBox(); tr = bb.Transform
                        a = tr.OfPoint(bb.Min); b = tr.OfPoint(bb.Max)
                        glass.append([round((min(a.X, b.X) - ox) * FT, 1), round((max(a.X, b.X) - ox) * FT, 1), round((min(a.Y, b.Y) - oy) * FT, 1), round((max(a.Y, b.Y) - oy) * FT, 1)])
    res["glass"] = glass
    def pmm(e, n):
        q = e.LookupParameter(n)
        return round(q.AsDouble() * FT, 1) if q is not None and q.StorageType == StorageType.Double else None
    res["panel_spec"] = [{"ADSK_Размер_Ширина": pmm(doc.GetElement(pid), u"ADSK_Размер_Ширина"),
                          "FT_Стекло_Ширина": pmm(doc.GetElement(pid), u"FT_Стекло_Ширина"),
                          "FT_Стекло_Добавка": pmm(doc.GetElement(pid).Symbol, u"FT_Стекло_Добавка")} for pid in w.CurtainGrid.GetPanelIds()]
    if args.get("debug"):
        dbg = []
        opt = Options(); opt.DetailLevel = ViewDetailLevel.Fine
        def walk(geo, depth):
            for g in geo:
                if isinstance(g, GeometryInstance):
                    walk(g.GetInstanceGeometry(), depth + 1)
                elif isinstance(g, Solid) and g.Volume > 0:
                    ms = set()
                    for f in g.Faces:
                        m = doc.GetElement(f.MaterialElementId); ms.add(m.Name if m else "-")
                    bb = g.GetBoundingBox(); tr = bb.Transform; a = tr.OfPoint(bb.Min); b = tr.OfPoint(bb.Max)
                    dbg.append([depth, sorted(ms), round((min(a.Y, b.Y) - oy) * FT, 1), round((max(a.Y, b.Y) - oy) * FT, 1), round((min(a.X, b.X) - ox) * FT, 1), round((max(a.X, b.X) - ox) * FT, 1)])
        for pid in w.CurtainGrid.GetPanelIds():
            walk(doc.GetElement(pid).get_Geometry(opt), 0)
        res["panel_solids"] = dbg
        ol = Outline(XYZ(ox + MM(390), oy + MM(20), level.Elevation), XYZ(ox + MM(410), oy + MM(30), level.Elevation + MM(2000)))
        res["at_plus_y"] = [[int(e.Id.Value), e.Category.Name if e.Category else "", e.Name] for e in FilteredElementCollector(doc).WherePasses(BoundingBoxIntersectsFilter(ol)).WhereElementIsNotElementType()]
        p = doc.GetElement(list(w.CurtainGrid.GetPanelIds())[0])
        res["panel_params"] = dict((q.Definition.Name, q.AsValueString() or q.AsString()) for q in list(p.Symbol.Parameters) + list(p.Parameters) if q.StorageType != StorageType.ElementId)
        t.RollBack(); raise Exception("debug")
    res["mullions"] = {"left": bbmm(mL), "mid": bbmm(mM), "right": bbmm(mR)}
    res["walls_x"] = [round((xl - ox) * FT, 1), round((xr - ox) * FT, 1)]; res["basic_half_mm"] = round(hw * FT, 1)
    t.Commit()
    # виды
    t = Transaction(doc, u"виды"); t.Start()
    res["panels_at_views"] = sorted(set(doc.GetElement(pid).Symbol.Family.Name for pid in w.CurtainGrid.GetPanelIds()))
    NH = MM(args.get("node_half_mm", 70))
    lx = (bbL.Min.X + bbL.Max.X) / 2; rx = (bbR.Min.X + bbR.Max.X) / 2
    boxes = {"overall": (ox - MM(150), oy - MM(150), ox + Lw + MM(150), oy + MM(150), 5),
             "left": (lx - NH, oy - NH, lx + NH, oy + NH, 1), "mid": (ox + Lw / 2 - NH, oy - NH, ox + Lw / 2 + NH, oy + NH, 1),
             "right": (rx - NH, oy - NH, rx + NH, oy + NH, 1)}
    vids = {}
    if args.get("only_views"):
        boxes = dict((k, v) for k, v in boxes.items() if k in args["only_views"])
    for k, (x0, y0, x1, y1, sc) in boxes.items():
        v = ViewPlan.Create(doc, vft.Id, level.Id); v.Name = u"Показ " + k
        vr = v.GetViewRange(); vr.SetOffset(PlanViewPlane.CutPlane, MM(500)); v.SetViewRange(vr)
        v.Scale = sc; v.DetailLevel = ViewDetailLevel.Fine
        bx = BoundingBoxXYZ(); bx.Min = XYZ(x0, y0, -1000); bx.Max = XYZ(x1, y1, 1000)
        v.CropBox = bx; v.CropBoxActive = True; v.CropBoxVisible = False
        try:
            v.SetCategoryHidden(ElementId(BuiltInCategory.OST_Levels), True)
            v.SetCategoryHidden(ElementId(BuiltInCategory.OST_Viewers), True)
            v.SetCategoryHidden(ElementId(BuiltInCategory.OST_Sections), True)
        except Exception:
            pass
        vids[k] = v
        res["views"][k] = {"box_mm": [round((x0 - ox) * FT, 1), round((y0 - oy) * FT, 1), round((x1 - ox) * FT, 1), round((y1 - oy) * FT, 1)]}
    if args.get("hide_test"):
        x0, y0, x1, y1, sc = boxes["left"]
        for k, ids in (("left_nopanel", list(w.CurtainGrid.GetPanelIds())), ("left_nohz", [m.Id for m in hz])):
            v = ViewPlan.Create(doc, vft.Id, level.Id); v.Name = u"Показ " + k
            vr = v.GetViewRange(); vr.SetOffset(PlanViewPlane.CutPlane, MM(500)); v.SetViewRange(vr)
            v.Scale = 1; v.DetailLevel = ViewDetailLevel.Fine
            bx = BoundingBoxXYZ(); bx.Min = XYZ(x0, y0, -1000); bx.Max = XYZ(x1, y1, 1000)
            v.CropBox = bx; v.CropBoxActive = True
            v.HideElements(List[ElementId](ids)); vids[k] = v
    sft = [x for x in FilteredElementCollector(doc).OfClass(ViewFamilyType) if x.ViewFamily == ViewFamily.Section][0]
    H = MM(args.get("height_mm", 2700)); xs = ox + MM(args.get("section_at_mm", 400))
    secs = [("sec_bottom", -MM(40), MM(100)), ("sec_top", H - MM(100), H + MM(40))]
    if args.get("only_views"):
        secs = [s for s in secs if s[0] in args["only_views"]]
    if args.get("hgrid_mm"):   # разрез по ригелю (горизонтальный стык)
        hz = MM(args["hgrid_mm"]); secs.append(("sec_mid", hz - MM(70), hz + MM(70)))
    for k, z0, z1 in secs:
        tr = Transform.Identity; tr.Origin = XYZ(xs, oy, level.Elevation)
        tr.BasisX = XYZ(0, 1, 0); tr.BasisY = XYZ(0, 0, 1); tr.BasisZ = XYZ(1, 0, 0)
        bx = BoundingBoxXYZ(); bx.Transform = tr
        bx.Min = XYZ(-NH, z0, -MM(30)); bx.Max = XYZ(NH, z1, MM(30))
        v = ViewSection.CreateSection(doc, sft.Id, bx); v.Name = u"Показ " + k
        v.Scale = 1; v.DetailLevel = ViewDetailLevel.Fine
        try:
            v.get_Parameter(BuiltInParameter.VIEWER_BOUND_FAR_CLIPPING).Set(1)
        except Exception:
            pass
        vids[k] = v
        res["views"][k] = {"box_local_mm": [round(-NH * FT, 1), round(z0 * FT, 1), round(NH * FT, 1), round(z1 * FT, 1)], "right_is": "+Y"}
    doc.Regenerate()
    vw = [e.Id for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Viewers).WhereElementIsNotElementType()]
    res["viewers_hidden"] = 0
    for k in [k_ for k_ in ("overall", "left", "mid", "right") if k_ in vids]:
        try:
            ids = [i for i in vw if doc.GetElement(i).CanBeHidden(vids[k])]
            if ids:
                vids[k].HideElements(List[ElementId](ids)); res["viewers_hidden"] += len(ids)
        except Exception as ex:
            res["hide_err"] = str(ex)[:200]
    t.Commit()
    if args.get("debug_view"):
        dv = []
        for pid in w.CurtainGrid.GetPanelIds():
            pn = doc.GetElement(pid)
            o2 = Options(); o2.View = vids["left"]
            def walk2(geo, d, tag):
                for g in geo:
                    if isinstance(g, GeometryInstance):
                        walk2(g.GetInstanceGeometry(), d + 1, tag + "/" + (doc.GetElement(g.GetSymbolGeometryId().SymbolId).Name if doc.GetElement(g.GetSymbolGeometryId().SymbolId) else "?"))
                    else:
                        bb = None
                        try:
                            if isinstance(g, Solid):
                                if g.Volume <= 0: continue
                                b = g.GetBoundingBox(); tr = b.Transform; a1 = tr.OfPoint(b.Min); a2 = tr.OfPoint(b.Max)
                                bb = [round((min(a1.Y, a2.Y) - oy) * FT, 1), round((max(a1.Y, a2.Y) - oy) * FT, 1)]
                            elif isinstance(g, Curve):
                                bb = [round((min(g.GetEndPoint(0).Y, g.GetEndPoint(1).Y) - oy) * FT, 1), round((max(g.GetEndPoint(0).Y, g.GetEndPoint(1).Y) - oy) * FT, 1)]
                        except Exception:
                            pass
                        m = doc.GetElement(g.GraphicsStyleId)
                        dv.append([int(pid.Value), tag, g.GetType().Name, bb, m.Name if m else ""])
            walk2(pn.get_Geometry(o2), 0, "")
            dv.append(["panel", int(pid.Value), pn.FacingFlipped if hasattr(pn, "FacingFlipped") else None, pn.Symbol.Family.Name])
        res["view_geom"] = dv[:200]
        res["n_panels_in_view"] = [[int(e.Id.Value), e.Name] for e in FilteredElementCollector(doc, vids["left"].Id).OfCategory(BuiltInCategory.OST_CurtainWallPanels)]
    for k, v in vids.items():
        e = ImageExportOptions(); e.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); e.SetViewsAndSheets(ids)
        e.ZoomType = ZoomFitType.FitToPage; e.PixelSize = int(args.get("px", 2400))
        e.ImageResolution = ImageResolution.DPI_300; e.HLRandWFViewsFileType = ImageFileType.PNG
        e.FilePath = os.path.join(OUT, u"v_" + k)
        doc.ExportImage(e)
    res["files"] = sorted(os.listdir(OUT))
except Exception as ex:
    if str(ex) != "debug":
        raise
finally:
    tg.RollBack()
io.open(os.path.join(OUT, u"geom.json"), "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
__output__ = {"status": "completed_unverified", "summary": u"виды сняты, всё откатано", "r": res}
