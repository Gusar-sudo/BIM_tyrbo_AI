# -*- coding: utf-8 -*-
# Отрисовать страницы PDF через Revit (ImageType из PDF -> чертёжный вид -> PNG). Всё в откате, модель не меняется.
# Аргументы: pdf, pages [номера страниц PDF, с 1], out_dir, px, dpi
import json, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
if not os.path.isdir(args["out_dir"]):
    os.makedirs(args["out_dir"])
vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.Drafting][0]
done, errs = [], []
tg = TransactionGroup(doc, u"страницы PDF (откат)"); tg.Start()
try:
    for pg in args["pages"]:
        checkpoint(u"стр %d" % pg, len(done), len(args["pages"]))
        t = Transaction(doc, u"страница"); t.Start()
        try:
            o = ImageTypeOptions(args["pdf"], False, ImageTypeSource.Import)
            o.PageNumber = int(pg)
            o.Resolution = int(args.get("dpi", 200))
            it = ImageType.Create(doc, o)
            v = ViewDrafting.Create(doc, vft.Id)
            v.Scale = 1
            ImageInstance.Create(doc, v, it.Id, ImagePlacementOptions())
            t.Commit()
            e = ImageExportOptions(); e.ExportRange = ExportRange.SetOfViews
            ids = List[ElementId](); ids.Add(v.Id); e.SetViewsAndSheets(ids)
            e.ZoomType = ZoomFitType.FitToPage; e.PixelSize = int(args.get("px", 2400))
            e.ImageResolution = ImageResolution.DPI_300; e.HLRandWFViewsFileType = ImageFileType.PNG
            e.ShadowViewsFileType = ImageFileType.PNG
            e.FilePath = os.path.join(args["out_dir"], u"p%03d" % pg)
            doc.ExportImage(e)
            done.append(pg)
        except Exception as ex:
            errs.append([pg, str(ex)[:150]])
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
finally:
    tg.RollBack()
__output__ = {"status": "completed_unverified" if not errs else "partial", "summary": u"страниц %d, ошибок %d; всё откатано" % (len(done), len(errs)), "done": done, "errors": errs}
