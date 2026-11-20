# -*- coding: utf-8 -*-
# 3D жалюзи крупно (всё откатывается): стена wall_type 1200×2400 без сетки, у панелей FT_Жалюзи = 1;
# виды: изометрия всей панели и крупный план угла; стили styles (ShadingWithEdges, Realistic); Fine. PNG -> out_dir.
# Аргументы: wall_type, out_dir, styles, px (1400), prep (include PREP)
import json, os
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
if isinstance(args.get("prep"), str):
    import io
    args["prep"] = json.loads(io.open(args["prep"], encoding="utf-8-sig").read())
FT = 304.8; MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
res = {}
tg = TransactionGroup(doc, u"FT: 3D жалюзи (откат)"); tg.Start()
try:
    if args.get("prep") and "PREP" in globals():
        res["prep_fail"] = PREP(doc, args["prep"]).get("swap_fail")
    wt = [w for w in FilteredElementCollector(doc).OfClass(WallType) if Element.Name.GetValue(w) == args["wall_type"]][0]
    lv = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
    vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.ThreeDimensional][0]
    t = Transaction(doc, u"стена"); t.Start()
    P0 = XYZ(MM(99000), MM(560000), lv.Elevation)
    w = Wall.Create(doc, Line.CreateBound(P0, P0 + XYZ.BasisX * MM(1200)), wt.Id, lv.Id, MM(2400), 0, False, False)
    doc.Regenerate()
    n = 0
    for pid in w.CurtainGrid.GetPanelIds():
        p = doc.GetElement(pid).LookupParameter(u"FT_Жалюзи")
        if p and p.Set(1):
            n += 1
    res["panels_on"] = n
    views = []
    boxes = {u"панель": (XYZ(P0.X - MM(100), P0.Y - MM(200), P0.Z), XYZ(P0.X + MM(1300), P0.Y + MM(200), P0.Z + MM(2500)), [1, -1.2, -0.5]),
             u"угол": (XYZ(P0.X - MM(60), P0.Y - MM(150), P0.Z + MM(1900)), XYZ(P0.X + MM(350), P0.Y + MM(150), P0.Z + MM(2450)), [1, -1.6, -0.3])}
    for key, (a, b, d) in boxes.items():
        for st in args.get("styles", ["ShadingWithEdges", "Realistic"]):
            v = View3D.CreateIsometric(doc, vft.Id); v.Name = u"FT жалюзи %s %s" % (key, st)
            v.DetailLevel = ViewDetailLevel.Fine; v.DisplayStyle = getattr(DisplayStyle, st); v.Scale = 10
            bb = BoundingBoxXYZ(); bb.Min = a; bb.Max = b; v.SetSectionBox(bb)
            dd = XYZ(d[0], d[1], d[2]).Normalize(); up = XYZ(0, 0, 1); up = (up - dd.Multiply(up.DotProduct(dd))).Normalize()
            c = (a + b) / 2
            v.SetOrientation(ViewOrientation3D(c - dd.Multiply(MM(8000)), up, dd))
            cb = v.CropBox; inv = cb.Transform.Inverse
            pts = [inv.OfPoint(XYZ(x, y, z)) for x in (a.X, b.X) for y in (a.Y, b.Y) for z in (a.Z, b.Z)]
            cb.Min = XYZ(min(p.X for p in pts), min(p.Y for p in pts), cb.Min.Z); cb.Max = XYZ(max(p.X for p in pts), max(p.Y for p in pts), cb.Max.Z)
            v.CropBox = cb; v.CropBoxActive = True; v.CropBoxVisible = False
            views.append((v, u"жалюзи_%s_%s" % (key, st)))
    t.Commit()
    for v, key in views:
        opt = ImageExportOptions(); opt.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); opt.SetViewsAndSheets(ids)
        opt.FilePath = os.path.join(OUT, key); opt.ZoomType = ZoomFitType.FitToPage; opt.PixelSize = int(args.get("px", 1400))
        opt.HLRandWFViewsFileType = ImageFileType.PNG; opt.ShadowViewsFileType = ImageFileType.PNG; opt.ImageResolution = ImageResolution.DPI_300
        doc.ExportImage(opt)
    res["views"] = len(views)
finally:
    tg.RollBack()
__output__ = {"status": "completed_unverified", "summary": u"видов %d; всё откатано" % res.get("views", 0), "result": res}
