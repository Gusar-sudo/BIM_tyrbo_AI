# -*- coding: utf-8 -*-
# Картинки импостов «по месту» (с соседним стеклом): по имени типа — первый (или все, до max_each) экземпляр;
# вертикальный — план 1:2 на середине высоты, горизонтальный — разрез поперёк стены 1:2. Виды временные — откат.
# Аргументы: types [имя типа импоста], out_dir, px (1300), max_each (1), half_mm (130)
import json, os
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8; MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
HALF = float(args.get("half_mm", 130))
level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
vft = dict((t.ViewFamily, t) for t in FilteredElementCollector(doc).OfClass(ViewFamilyType))
HIDE = [BuiltInCategory.OST_Levels, BuiltInCategory.OST_Grids, BuiltInCategory.OST_Elev, BuiltInCategory.OST_Sections, BuiltInCategory.OST_CLines,
        BuiltInCategory.OST_SectionHeads, BuiltInCategory.OST_Viewers]
mts = dict((Element.Name.GetValue(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
inst = list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType())


def tidy(v):
    for b in HIDE:
        try:
            v.SetCategoryHidden(ElementId(b), True)
        except Exception:
            pass


res = []; V = []
tg = TransactionGroup(doc, u"FT: съёмка импостов (откат)"); tg.Start()
try:
    t = Transaction(doc, u"виды"); t.Start()
    for i, tn in enumerate(args["types"]):
        mt = mts.get(tn)
        ms = [m for m in inst if mt is not None and m.GetTypeId() == mt.Id][:int(args.get("max_each", 1))]
        if not ms:
            res.append({"type": tn, "error": u"нет экземпляров"}); continue
        for j, m in enumerate(ms):
            bb = m.get_BoundingBox(None); c = (bb.Min + bb.Max) / 2
            w = m.Host; d = w.Location.Curve.Direction.Normalize()
            vert = (bb.Max.Z - bb.Min.Z) > max(bb.Max.X - bb.Min.X, bb.Max.Y - bb.Min.Y)
            key = u"%02d_%s%s" % (i + 1, tn, "" if j == 0 else "_%d" % (j + 1))
            if vert:
                v = ViewPlan.Create(doc, vft[ViewFamily.FloorPlan].Id, level.Id)
                z = (c.Z - level.Elevation)
                vr = v.GetViewRange()
                vr.SetOffset(PlanViewPlane.TopClipPlane, z + MM(300)); vr.SetOffset(PlanViewPlane.CutPlane, z)
                vr.SetOffset(PlanViewPlane.BottomClipPlane, z - MM(300)); vr.SetOffset(PlanViewPlane.ViewDepthPlane, z - MM(300))
                v.SetViewRange(vr)
                cb = v.CropBox; cb.Min = XYZ(c.X - MM(HALF), c.Y - MM(HALF * .75), cb.Min.Z); cb.Max = XYZ(c.X + MM(HALF), c.Y + MM(HALF * .75), cb.Max.Z)
                v.CropBox = cb; v.CropBoxActive = True; v.CropBoxVisible = False
            else:
                n = XYZ(-d.Y, d.X, 0)
                tr = Transform.Identity; tr.Origin = XYZ(c.X, c.Y, c.Z)
                tr.BasisX = n; tr.BasisY = XYZ.BasisZ; tr.BasisZ = n.CrossProduct(XYZ.BasisZ)
                sb = BoundingBoxXYZ(); sb.Transform = tr
                sb.Min = XYZ(-MM(HALF), -MM(HALF * .75), -MM(40)); sb.Max = XYZ(MM(HALF), MM(HALF * .75), 0)
                v = ViewSection.CreateSection(doc, vft[ViewFamily.Section].Id, sb)
            v.Scale = 2; v.DetailLevel = ViewDetailLevel.Fine; tidy(v)
            V.append((v, key)); res.append({"type": tn, "mullion": m.Id.Value, "vertical": vert, "image": key})
    t.Commit()
    for v, key in V:
        opt = ImageExportOptions(); opt.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); opt.SetViewsAndSheets(ids)
        opt.FilePath = os.path.join(OUT, key); opt.ZoomType = ZoomFitType.FitToPage; opt.PixelSize = int(args.get("px", 1300))
        opt.HLRandWFViewsFileType = ImageFileType.PNG; opt.ImageResolution = ImageResolution.DPI_300
        doc.ExportImage(opt)
finally:
    tg.RollBack()
__output__ = {"status": "completed_unverified", "summary": u"снято %d; виды откатаны, модель не менялась" % len(V), "result": res}
