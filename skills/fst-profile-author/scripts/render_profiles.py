# -*- coding: utf-8 -*-
# Только чтение: картинки сечений семейств профилей (вид семейства профиля = контур + вложенные «Элементы узлов»).
# Семейства открываются EditFamily и закрываются без сохранения — проект не меняется.
# Аргументы: names [имя семейства], out_dir, px (1200)
import json, os
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
FT = 304.8
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
res = []
# rfa_paths: ещё не загруженные копии .rfa — открываются с диска и закрываются без сохранения
items = [(n, None) for n in args.get("names", [])] + [(os.path.splitext(os.path.basename(p))[0], p) for p in args.get("rfa_paths", [])]
for i, (n, pth) in enumerate(items):
    r = {"name": n}
    fd = None
    try:
        fd = __revit__.Application.OpenDocumentFile(pth) if pth else doc.EditFamily(fams[n])
        vs = [v for v in FilteredElementCollector(fd).OfClass(View) if not v.IsTemplate and v.CanBePrinted and v.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Detail, ViewType.DraftingView, ViewType.EngineeringPlan)]
        v = vs[0]
        own = [ce.GeometryCurve for ce in FilteredElementCollector(fd).OfClass(CurveElement) if ce.GeometryCurve is not None]
        xs = [q.X * FT for c in own for q in (c.GetEndPoint(0), c.GetEndPoint(1))]; ys = [q.Y * FT for c in own for q in (c.GetEndPoint(0), c.GetEndPoint(1))]
        r["own_bbox_mm"] = [round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1)]; r["own_lines"] = len(own)
        t = Transaction(fd, u"вид"); t.Start()
        try:
            v.Scale = 1; v.DetailLevel = ViewDetailLevel.Fine
        except Exception:
            pass
        t.Commit()
        opt = ImageExportOptions(); opt.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); opt.SetViewsAndSheets(ids)
        opt.FilePath = os.path.join(OUT, "%02d_%s" % (i + 1, n.replace(u"BIMLIB_Профиль_", u"").replace(u"_ФристайлТехнолоджи", u"")))
        opt.ZoomType = ZoomFitType.FitToPage; opt.PixelSize = int(args.get("px", 1200))
        opt.HLRandWFViewsFileType = ImageFileType.PNG; opt.ImageResolution = ImageResolution.DPI_300
        fd.ExportImage(opt)
        r["ok"] = True
    except Exception as ex:
        r["error"] = str(ex)
    finally:
        if fd is not None:
            fd.Close(False)
    res.append(r)
__output__ = {"status": "completed_unverified", "summary": u"снято %d из %d; проект не менялся" % (len([x for x in res if x.get("ok")]), len(res)), "result": res}
