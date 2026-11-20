# -*- coding: utf-8 -*-
# Только чтение модели: экспорт видов в PNG (ExportImage). Аргументы: view_ids, out_dir, px
import json, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
out = []
for vid in args["view_ids"]:
    v = doc.GetElement(ElementId(int(vid)))
    o = ImageExportOptions()
    o.ExportRange = ExportRange.SetOfViews
    ids = List[ElementId](); ids.Add(v.Id)
    o.SetViewsAndSheets(ids)
    o.FilePath = os.path.join(args["out_dir"], "v%d" % int(vid))
    o.HLRandWFViewsFileType = ImageFileType.PNG
    o.ImageResolution = ImageResolution.DPI_300
    o.ZoomType = ZoomFitType.FitToPage
    o.PixelSize = int(args.get("px", 2400))
    o.FitDirection = FitDirectionType.Horizontal
    doc.ExportImage(o)
    out.append({"id": int(vid), "name": v.Name})
files = [f for f in os.listdir(args["out_dir"]) if f.lower().endswith(".png")]
__output__ = {"status": "completed_unverified", "summary": "exported %d views" % len(out), "views": out, "files": files}
