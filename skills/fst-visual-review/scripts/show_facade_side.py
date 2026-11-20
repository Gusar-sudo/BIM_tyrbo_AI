# -*- coding: utf-8 -*-
# Показ «с какой стороны стекло относительно стрелок разворота»: стена заданного типа (как нарисована) и та же стена,
# перевёрнутая (Flip), план Fine; стрелка и подпись — сторона Wall.Orientation (там Revit рисует стрелки разворота).
# Всё в группе транзакций и откатывается. Аргументы: wall_type, out_dir, length_mm=1200, origin_mm=[x,y], scale=5, px=1600
import json, io, os, math
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
res = {"files": [], "walls": []}
tg = TransactionGroup(doc, u"показ стороны стекла (откат)"); tg.Start()
try:
    t = Transaction(doc, u"стены и виды"); t.Start()
    lvl = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
    wt = [w for w in FilteredElementCollector(doc).OfClass(WallType) if w.Name == args["wall_type"]][0]
    ox, oy = [v / FT for v in args.get("origin_mm", [200000, -200000])]
    L = args.get("length_mm", 1200) / FT; Z = lvl.Elevation
    vft = [x for x in FilteredElementCollector(doc).OfClass(ViewFamilyType) if x.ViewFamily == ViewFamily.FloorPlan][0]
    tnt = FilteredElementCollector(doc).OfClass(TextNoteType).FirstElement()
    views = []
    for i, flip in enumerate((False, True)):
        y = oy - i * 3000 / FT
        w = Wall.Create(doc, Line.CreateBound(XYZ(ox, y, Z), XYZ(ox + L, y, Z)), wt.Id, lvl.Id, 2700 / FT, 0, False, False)
        doc.Regenerate()
        if flip:
            w.Flip(); doc.Regenerate()
        # у витража Wall.Orientation после Flip() не меняется — меняется только Flipped (проверено 14.11);
        # наружная сторона (где Revit рисует стрелки разворота) = Orientation × (−1, если Flipped)
        o = w.Orientation.Multiply(-1.0 if w.Flipped else 1.0)
        v = ViewPlan.Create(doc, vft.Id, lvl.Id); v.Name = u"Сторона стекла %d" % i
        v.Scale = int(args.get("scale", 5)); v.DetailLevel = ViewDetailLevel.Fine
        vr = v.GetViewRange(); vr.SetOffset(PlanViewPlane.CutPlane, 1200 / FT); v.SetViewRange(vr)
        cx = ox + 330 / FT; H = 260 / FT   # кадр у начала стены — виден профиль края и стекло
        bx = BoundingBoxXYZ(); bx.Min = XYZ(cx - 400 / FT, y - H, -1000); bx.Max = XYZ(cx + 400 / FT, y + H, 1000)
        v.CropBox = bx; v.CropBoxActive = True; v.CropBoxVisible = False
        doc.Regenerate()
        # стрелка в сторону Orientation (стрелки разворота) и подписи
        a0 = XYZ(cx + 60 / FT, y + o.Y * 70 / FT, Z); a1 = XYZ(cx + 60 / FT, y + o.Y * 190 / FT, Z)
        doc.Create.NewDetailCurve(v, Line.CreateBound(a0, a1))
        for sx in (-1, 1):
            doc.Create.NewDetailCurve(v, Line.CreateBound(a1, a1 + XYZ(sx * 18 / FT, -o.Y * 30 / FT, 0)))
        TextNote.Create(doc, v.Id, XYZ(cx + 90 / FT, y + o.Y * 170 / FT, Z), u"сторона стрелок разворота (в Revit «наружная»)", tnt.Id)
        TextNote.Create(doc, v.Id, XYZ(cx + 90 / FT, y - o.Y * 150 / FT, Z), u"противоположная сторона (в Revit «внутренняя»)", tnt.Id)
        res["walls"].append({"flip": flip, "exterior_y": round(o.Y, 3), "flipped": bool(w.Flipped)})
        views.append((v, i))
    t.Commit()
    for v, i in views:
        e = ImageExportOptions(); e.ExportRange = ExportRange.SetOfViews
        e.SetViewsAndSheets(List[ElementId]([v.Id])); e.ZoomType = ZoomFitType.FitToPage; e.PixelSize = int(args.get("px", 1600))
        e.ImageResolution = ImageResolution.DPI_300; e.HLRandWFViewsFileType = ImageFileType.PNG
        e.FilePath = os.path.join(OUT, u"wall_%d" % i)
        doc.ExportImage(e)
    res["files"] = sorted(os.listdir(OUT))
finally:
    if tg.HasStarted() and not tg.HasEnded():
        tg.RollBack()
__output__ = {"status": "completed_unverified", "summary": u"виды сняты, всё откатано", "r": res}
