# -*- coding: utf-8 -*-
# Картинки уже стоящих образцов «до подвесного потолка» (W1) и «проём» (W2) по координатам; все виды временные —
# группа транзакций откатывается, модель не меняется.
# Аргументы: samples [{tag, origin_mm [x, y]}] (W1 в origin, W2 на 4000 мм ниже по y), out_dir, px (1300),
#            L 3000, grid 1000, post_step_mm 1000, H_slab 3500, H_ceil 2700, H 3000, H_head 2100, open_bay [1000, 2000]
import json, os, io
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8; MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
L = float(args.get("L", 3000)); G = float(args.get("grid", 1000)); PS = float(args.get("post_step_mm", 1000))
HS = float(args.get("H_slab", 3500)); HC = float(args.get("H_ceil", 2700)); H = float(args.get("H", 3000)); HH = float(args.get("H_head", 2100))
xa, xb = [float(v) for v in args.get("open_bay", [1000, 2000])]
level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
Z0 = level.Elevation
vft = dict((t.ViewFamily, t) for t in FilteredElementCollector(doc).OfClass(ViewFamilyType))
HIDE = [BuiltInCategory.OST_Levels, BuiltInCategory.OST_Grids, BuiltInCategory.OST_Elev, BuiltInCategory.OST_Sections, BuiltInCategory.OST_CLines,
        BuiltInCategory.OST_SectionHeads, BuiltInCategory.OST_Viewers]
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


def section_across(x, y, z0, z1, half, name, scale=2):
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


res = {"samples": []}
tg = TransactionGroup(doc, u"FT: съёмка образцов (откат)"); tg.Start()
try:
    for s in args["samples"]:
        tag = s["tag"]; ox, oy = s["origin_mm"]
        P1 = XYZ(MM(ox), MM(oy), Z0); P2 = XYZ(MM(ox), MM(oy - 4000), Z0)
        r = {"tag": tag}
        t = Transaction(doc, u"виды %s" % tag); t.Start()
        V = [(facade(P1, L, HS, u"FT съёмка %s потолок фасад" % tag), u"%s_1_потолок_фасад" % tag),
             (plan(P1.X + MM(PS), P1.Y, HC + 400, u"FT съёмка %s над потолком стойка" % tag), u"%s_2_потолок_план_стойка" % tag),
             (section_across(P1.X + MM(PS / 2), P1.Y, HC - 150, HC + 150, 130, u"FT съёмка %s ригель у потолка" % tag), u"%s_4_потолок_ригель_разрез" % tag),
             (facade(P2, L, H, u"FT съёмка %s проём фасад" % tag), u"%s_7_проём_фасад" % tag),
             (plan(P2.X + MM(xa), P2.Y, 1000, u"FT съёмка %s проём левая" % tag), u"%s_8_проём_план_левая" % tag),
             (plan(P2.X + MM(xb), P2.Y, 1000, u"FT съёмка %s проём правая" % tag), u"%s_9_проём_план_правая" % tag),
             (section_across(P2.X + MM((xa + xb) / 2), P2.Y, HH - 150, HH + 150, 130, u"FT съёмка %s над проёмом" % tag), u"%s_10_проём_над_проёмом_разрез" % tag),
             (plan(P2.X + MM(xa), P2.Y, HH + 400, u"FT съёмка %s стойка выше проёма" % tag), u"%s_11_проём_план_стойка_выше_проёма" % tag),
             (view3d(XYZ(P2.X - MM(300), P2.Y - MM(600), Z0 - MM(50)), XYZ(P1.X + MM(L + 300), P1.Y + MM(600), Z0 + MM(HS + 50)), [1, 1.4, -0.6], u"FT съёмка %s 3D" % tag), u"%s_0_3D_оба" % tag)]
        t.Commit()
        for v, key in V:
            opt = ImageExportOptions(); opt.ExportRange = ExportRange.SetOfViews
            ids = List[ElementId](); ids.Add(v.Id); opt.SetViewsAndSheets(ids)
            opt.FilePath = os.path.join(OUT, key); opt.ZoomType = ZoomFitType.FitToPage; opt.PixelSize = int(args.get("px", 1300))
            opt.HLRandWFViewsFileType = ImageFileType.PNG; opt.ShadowViewsFileType = ImageFileType.PNG; opt.ImageResolution = ImageResolution.DPI_300
            doc.ExportImage(opt)
        r["views"] = len(V); res["samples"].append(r)
finally:
    tg.RollBack()
__output__ = {"status": "completed_unverified", "summary": u"снято образцов %d; временные виды откатаны, модель не менялась" % len(res["samples"]), "result": res}
