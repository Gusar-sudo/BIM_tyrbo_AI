# -*- coding: utf-8 -*-
# Шаблоны видов «для клиента» + примеры видов у импоста; keep=false — проба С ОТКАТОМ (картинки), keep=true — оставить.
# FT_Клиент_План_1-50 (Medium, скрытые линии, тонкий разрез импостов/панелей), FT_Клиент_Узел_1-2 (Fine), FT_Клиент_3D (тонированный, Fine).
# Аргументы: mullion_type_like, out_dir, keep=false, plan_half_mm=1500, node_half_mm=90, cut_lw=1, px=1600
import json, io, os, glob
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
OUT = args.get("out_dir"); KEEP = bool(args.get("keep"))
if OUT and not os.path.isdir(OUT): os.makedirs(OUT)
like = args.get("mullion_type_like", u"").lower().split()
LW = int(args.get("cut_lw", 1))
res = {"errors": [], "files": [], "templates": {}}
mul = wall = None
for w in FilteredElementCollector(doc).OfClass(Wall):
    if w.CurtainGrid is None: continue
    for mid in w.CurtainGrid.GetMullionIds():
        m = doc.GetElement(mid)
        if all(k in (m.Symbol.FamilyName + u" " + m.Name).lower() for k in like) and m.LocationCurve is not None and abs(m.LocationCurve.Direction.Z) > 0.9:
            mul, wall = m, w; break
    if mul: break
lc = wall.Location.Curve; d = lc.Direction; d = XYZ(d.X, d.Y, 0).Normalize(); n = XYZ(-d.Y, d.X, 0)
p0 = mul.LocationCurve.GetEndPoint(0); p1 = mul.LocationCurve.GetEndPoint(1)
zb, zt = min(p0.Z, p1.Z), max(p0.Z, p1.Z); zm = (zb + zt) / 2; org = XYZ(p0.X, p0.Y, zm)
lvl = sorted([l for l in FilteredElementCollector(doc).OfClass(Level) if l.Elevation <= zb + 1e-6], key=lambda l: -l.Elevation)
lvl = lvl[0] if lvl else sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: l.Elevation)[0]
vft = lambda k: [v for v in FilteredElementCollector(doc).OfClass(ViewFamilyType) if v.ViewFamily == k][0]


def thin_cut(v):
    ogs = OverrideGraphicSettings(); ogs.SetCutLineWeight(LW); ogs.SetProjectionLineWeight(LW)
    for bic in (BuiltInCategory.OST_CurtainWallMullions, BuiltInCategory.OST_CurtainWallPanels):
        v.SetCategoryOverrides(ElementId(bic), ogs)
    # для клиента — без рабочих аннотаций
    for bic in (BuiltInCategory.OST_TextNotes, BuiltInCategory.OST_Sections, BuiltInCategory.OST_Elev, BuiltInCategory.OST_Callouts,
                BuiltInCategory.OST_CLines, BuiltInCategory.OST_Viewers, BuiltInCategory.OST_ReferenceViewer, BuiltInCategory.OST_Dimensions):
        try:
            cid = ElementId(bic)
            if v.CanCategoryBeHidden(cid): v.SetCategoryHidden(cid, True)
        except Exception:
            pass


def plan(name, scale, half, detail):
    vp = ViewPlan.Create(doc, vft(ViewFamily.FloorPlan).Id, lvl.Id); vp.Name = name
    vr = vp.GetViewRange()
    vr.SetLevelId(PlanViewPlane.TopClipPlane, lvl.Id); vr.SetOffset(PlanViewPlane.TopClipPlane, zt - lvl.Elevation + 1)
    vr.SetLevelId(PlanViewPlane.CutPlane, lvl.Id); vr.SetOffset(PlanViewPlane.CutPlane, zm - lvl.Elevation)
    vr.SetLevelId(PlanViewPlane.BottomClipPlane, lvl.Id); vr.SetOffset(PlanViewPlane.BottomClipPlane, 0)
    vr.SetLevelId(PlanViewPlane.ViewDepthPlane, lvl.Id); vr.SetOffset(PlanViewPlane.ViewDepthPlane, 0)
    vp.SetViewRange(vr); vp.Scale = scale; vp.DetailLevel = detail; vp.DisplayStyle = DisplayStyle.HLR
    c = [org + d * half + n * half * 0.6, org - d * half - n * half * 0.6, org + d * half - n * half * 0.6, org - d * half + n * half * 0.6]
    bb = BoundingBoxXYZ(); bb.Min = XYZ(min(p.X for p in c), min(p.Y for p in c), lvl.Elevation - 1); bb.Max = XYZ(max(p.X for p in c), max(p.Y for p in c), zt + 1)
    vp.CropBoxActive = True; vp.CropBox = bb; vp.CropBoxVisible = False
    thin_cut(vp)
    return vp


def export(view, tag):
    if not OUT: return
    o = ImageExportOptions(); o.ExportRange = ExportRange.SetOfViews; o.SetViewsAndSheets(List[ElementId]([view.Id]))
    o.FilePath = os.path.join(OUT, tag); o.ZoomType = ZoomFitType.FitToPage; o.PixelSize = args.get("px", 1600)
    o.HLRandWFViewsFileType = ImageFileType.PNG; o.ShadowViewsFileType = ImageFileType.PNG; o.ImageResolution = ImageResolution.DPI_300
    before = set(glob.glob(os.path.join(OUT, tag + "*"))); doc.ExportImage(o)
    new = [f for f in glob.glob(os.path.join(OUT, tag + "*")) if f not in before]
    if new:
        dst = os.path.join(OUT, tag + ".png")
        if os.path.exists(dst) and new[0] != dst: os.remove(dst)
        if new[0] != dst: os.rename(new[0], dst)
        res["files"].append(dst)


tg = TransactionGroup(doc, u"шаблоны видов для клиента" + (u"" if KEEP else u" (откат)")); tg.Start()
try:
    t = Transaction(doc, u"виды и шаблоны"); t.Start()
    vP = plan(u"FT_Клиент_пример_План 1-50", 50, args.get("plan_half_mm", 1500) / FT, ViewDetailLevel.Medium)
    vN = plan(u"FT_Клиент_пример_Узел 1-2", 2, args.get("node_half_mm", 90) / FT, ViewDetailLevel.Fine)
    v3 = View3D.CreateIsometric(doc, vft(ViewFamily.ThreeDimensional).Id); v3.Name = u"FT_Клиент_пример_3D"
    H = 1200 / FT; sb = BoundingBoxXYZ(); tr = Transform.Identity; tr.Origin = org; tr.BasisX = d; tr.BasisY = n; tr.BasisZ = XYZ.BasisZ; sb.Transform = tr
    sb.Min = XYZ(-H, -H * 0.3, -(zm - zb)); sb.Max = XYZ(H, H * 0.3, (zt - zm)); v3.SetSectionBox(sb)
    eye = org + d * (-3.0) + n * (-3.0) + XYZ.BasisZ * 2.0; fwd = (org - eye).Normalize()
    up = XYZ.BasisZ.Subtract(fwd.Multiply(XYZ.BasisZ.DotProduct(fwd))).Normalize(); v3.SetOrientation(ViewOrientation3D(eye, up, fwd))
    v3.DetailLevel = ViewDetailLevel.Fine; v3.DisplayStyle = DisplayStyle.ShadingWithEdges; v3.Scale = 20; thin_cut(v3)
    doc.Regenerate()
    for v, tn in ((vP, u"FT_Клиент_План_1-50"), (vN, u"FT_Клиент_Узел_1-2"), (v3, u"FT_Клиент_3D")):
        old = [x for x in FilteredElementCollector(doc).OfClass(View) if x.IsTemplate and x.Name == tn]
        for x in old: doc.Delete(x.Id)
        tpl = v.CreateViewTemplate(); tpl.Name = tn
        v.ViewTemplateId = tpl.Id; res["templates"][tn] = int(tpl.Id.Value)
    t.Commit()
    for v, tag in ((vP, "plan_1-50"), (vN, "node_1-2"), (v3, "3d")):
        try: export(v, tag)
        except Exception as ex: res["errors"].append(tag + ": " + str(ex)[:150])
    if KEEP:
        tg.Assimilate(); res["kept"] = True
    else:
        tg.RollBack(); res["rolled_back"] = True
except Exception as ex:
    res["errors"].append(str(ex)[:200])
    if tg.HasStarted() and not tg.HasEnded(): tg.RollBack(); res["rolled_back"] = True
__output__ = {"status": "partial" if res["errors"] else "completed_unverified", "summary": u"шаблоны: %s; картинок %d" % (u", ".join(res["templates"]), len(res["files"])), "result": res}
