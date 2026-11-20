# -*- coding: utf-8 -*-
# 3D крупным планом угла витража у пола и у стены (всё откатывается): стена length_mm × height_mm, у начала — стена-примыкание,
# снизу — плита. Вид 3D с секущим ящиком box_mm вокруг угла (низ/верх), Fine, «Тонированный с рёбрами». PNG -> out_dir.
# Аргументы: wall_types [имена], out_dir, corners ["низ","верх"], box_mm (250), px (1400), abut_wall_type ("auto"), tag_offset, view_dir [x,y,z]
import json, os
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
FT = 304.8
MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
L = float(args.get("length_mm", 1500)); H = float(args.get("height_mm", 2700)); BOX = float(args.get("box_mm", 250))
wtypes = dict((Element.Name.GetValue(w), w) for w in FilteredElementCollector(doc).OfClass(WallType))
abut = None
if args.get("abut_wall_type", "auto") == "auto":
    cand = sorted([w for w in wtypes.values() if w.Kind == WallKind.Basic and MM(100) <= w.Width <= MM(300)], key=lambda w: w.Width)
    abut = cand[0] if cand else None
else:
    abut = wtypes.get(args["abut_wall_type"])
level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.ThreeDimensional][0]
vd = args.get("view_dir", [-1, 1, -0.6])
res = {"types": []}
tg = TransactionGroup(doc, u"FT: 3D углов (откат)"); tg.Start()
try:
    if args.get("prep") and "PREP" in globals():
        res["prep"] = PREP(doc, args["prep"])
    views = []
    for k, wn in enumerate(args["wall_types"]):
        checkpoint(wn, k, len(args["wall_types"]))
        tag = u"%02d" % (k + 1 + int(args.get("tag_offset", 0)))
        t = Transaction(doc, u"угол"); t.Start()
        P0 = XYZ(MM(90000), MM(520000 + 4000 * k), level.Elevation)
        w = Wall.Create(doc, Line.CreateBound(P0, P0 + XYZ.BasisX * MM(L)), wtypes[wn].Id, level.Id, MM(H), 0, False, False)
        WallUtils.DisallowWallJoinAtEnd(w, 0); WallUtils.DisallowWallJoinAtEnd(w, 1)
        if abut is not None:
            th = abut.Width
            aw = Wall.Create(doc, Line.CreateBound(XYZ(P0.X - th / 2, P0.Y - MM(600), P0.Z), XYZ(P0.X - th / 2, P0.Y + MM(600), P0.Z)), abut.Id, level.Id, MM(H), 0, False, False)
            WallUtils.DisallowWallJoinAtEnd(aw, 0); WallUtils.DisallowWallJoinAtEnd(aw, 1)
        doc.Regenerate()
        for key in args.get("corners", [u"низ", u"верх"]):
            z0 = P0.Z if key == u"низ" else P0.Z + MM(H)
            v = View3D.CreateIsometric(doc, vft.Id); v.Name = u"FT угол %s %s" % (tag, key)
            v.DetailLevel = ViewDetailLevel.Fine
            v.DisplayStyle = getattr(DisplayStyle, args.get("style", "ShadingWithEdges"))   # Shading | Realistic | ShadingWithEdges
            if args.get("thin_lines"):
                try:
                    v.get_Parameter(BuiltInParameter.VIEW_SCALE_PULLDOWN_METRIC).Set(1)
                except Exception:
                    pass
                v.Scale = int(args.get("scale", 1))
            if args.get("line_weight"):   # толщина линий из таблиц файла бывает большой — задаём её в виде явно
                ogs = OverrideGraphicSettings()
                ogs.SetProjectionLineWeight(int(args["line_weight"])); ogs.SetCutLineWeight(int(args["line_weight"]))
                for bic in (BuiltInCategory.OST_CurtainWallMullions, BuiltInCategory.OST_CurtainWallPanels, BuiltInCategory.OST_Walls,
                            BuiltInCategory.OST_GenericModel, BuiltInCategory.OST_Windows, BuiltInCategory.OST_Doors):
                    try:
                        v.SetCategoryOverrides(ElementId(bic), ogs)
                    except Exception:
                        pass
            bb = BoundingBoxXYZ()
            bb.Min = XYZ(P0.X - MM(BOX * 0.6), P0.Y - MM(BOX), z0 - MM(BOX * 0.5)); bb.Max = XYZ(P0.X + MM(BOX), P0.Y + MM(BOX), z0 + MM(BOX * 0.5))
            v.SetSectionBox(bb)
            d = XYZ(vd[0], vd[1], vd[2] if key == u"низ" else -vd[2]).Normalize()
            up = XYZ(0, 0, 1); up = (up - d.Multiply(up.DotProduct(d))).Normalize()
            v.SetOrientation(ViewOrientation3D(XYZ(P0.X, P0.Y, z0) - d.Multiply(MM(5000)), up, d))
            # рамка вида = проекция секущего ящика (иначе FitToPage вписывает весь проект и угол выходит крошечным)
            cb = v.CropBox; inv = cb.Transform.Inverse
            pts = [inv.OfPoint(XYZ(x, y, z)) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y) for z in (bb.Min.Z, bb.Max.Z)]
            cb.Min = XYZ(min(p.X for p in pts), min(p.Y for p in pts), cb.Min.Z); cb.Max = XYZ(max(p.X for p in pts), max(p.Y for p in pts), cb.Max.Z)
            v.CropBox = cb; v.CropBoxActive = True; v.CropBoxVisible = False
            views.append((v, u"%s_угол_%s" % (tag, key)))
        t.Commit()
        res["types"].append({"tag": tag, "wall_type": wn})
    for v, key in views:
        opt = ImageExportOptions(); opt.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); opt.SetViewsAndSheets(ids)
        opt.FilePath = os.path.join(OUT, key); opt.ZoomType = ZoomFitType.FitToPage; opt.PixelSize = int(args.get("px", 1400))
        opt.HLRandWFViewsFileType = ImageFileType.PNG; opt.ShadowViewsFileType = ImageFileType.PNG; opt.ImageResolution = ImageResolution.DPI_300
        _thin = None
        if args.get("thin_lines"):   # выгрузка картинки берёт переключатель «Тонкие линии» из интерфейса, а не из вида
            try:
                from Autodesk.Revit.UI import ThinLinesOptions
                _thin = ThinLinesOptions.AreThinLinesEnabled; ThinLinesOptions.AreThinLinesEnabled = True
            except Exception:
                _thin = None
        try:
            doc.ExportImage(opt)
        finally:
            if _thin is not None:
                ThinLinesOptions.AreThinLinesEnabled = _thin
    res["warnings"] = len(doc.GetWarnings())
finally:
    tg.RollBack()
__output__ = {"status": "completed_unverified", "summary": u"типов %d; всё откатано" % len(res["types"]), "result": res}
