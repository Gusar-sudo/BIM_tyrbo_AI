# -*- coding: utf-8 -*-
# Планы торца витража 1:2 (Fine): крайний импост в конце стены заменяется на заданный тип; по желанию у торца ставится
# стена (примыкание) — для проверки «примыкание к стене» и «не доходит до стены» (свободный край).
# Новые типы можно создать временно (new_types: копия base_type + values) — в группе транзакций, которая ОТКАТЫВАЕТСЯ.
# PNG планов -> out_dir. Модель не меняется.
# Аргументы: new_types [{base_type, new_type, values{param: text}}], cases [{key, wall_type, end_type, abut_wall_type|null}],
#            out_dir, length_mm (1500), half_mm (260), px (1400), origin_mm [x, y]
import json, os
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
Lm = float(args.get("length_mm", 1500)); HALF = float(args.get("half_mm", 260))
ox, oy = [float(v) for v in args.get("origin_mm", [60000, 600000])]
wtypes = dict((w.Name, w) for w in FilteredElementCollector(doc).OfClass(WallType))
mtypes = dict((m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.FloorPlan][0]
res = {"cases": [], "types": []}
tg = TransactionGroup(doc, u"FT: планы торца (откат)"); tg.Start()
try:
    if args.get("prep") and "PREP" in globals():   # include с PREP(doc, args) (например prep_wall_band.py)
        res["prep"] = PREP(doc, args["prep"])
        mtypes = dict((m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
    t = Transaction(doc, u"типы"); t.Start()
    for nt in args.get("new_types", []):
        if nt["new_type"] in mtypes:
            res["types"].append([nt["new_type"], "exists"]); continue
        m = mtypes[nt["base_type"]].Duplicate(nt["new_type"])
        for pn, pv in (nt.get("values") or {}).items():
            p = m.LookupParameter(pn)
            ok = bool(p and not p.IsReadOnly and p.Set(pv))
            res["types"].append([nt["new_type"], pn, ok])
        mtypes[nt["new_type"]] = m
    t.Commit()
    views = []
    for k, c in enumerate(args["cases"]):
        r = {"key": c["key"]}
        t = Transaction(doc, u"торец"); t.Start()
        P0 = XYZ(MM(ox), MM(oy + 3000 * k), level.Elevation)
        w = Wall.Create(doc, Line.CreateBound(P0, P0 + XYZ.BasisX * MM(Lm)), wtypes[c["wall_type"]].Id, level.Id, MM(3000), 0, False, False)
        WallUtils.DisallowWallJoinAtEnd(w, 0); WallUtils.DisallowWallJoinAtEnd(w, 1)
        doc.Regenerate()
        end = None
        for mid in w.CurtainGrid.GetMullionIds():
            m = doc.GetElement(mid); bb = m.get_BoundingBox(None)
            if bb and (bb.Max.Z - bb.Min.Z) > (bb.Max.X - bb.Min.X) and abs((bb.Min.X + bb.Max.X) / 2 - (P0.X + MM(Lm))) < MM(100):
                end = m
        if end is None:
            r["error"] = u"нет крайнего импоста"
        else:
            end.Pinned = False; end.ChangeTypeId(mtypes[c["end_type"]].Id)
            r["end_type"] = c["end_type"]
        doc.Regenerate()
        xe = P0.X + MM(Lm)
        if end is not None:
            bb = end.get_BoundingBox(None); xe = bb.Max.X
        if c.get("abut_wall_type"):
            at = wtypes[c["abut_wall_type"]]
            th = at.Width
            aw = Wall.Create(doc, Line.CreateBound(XYZ(xe + th / 2, P0.Y - MM(700), P0.Z), XYZ(xe + th / 2, P0.Y + MM(700), P0.Z)), at.Id, level.Id, MM(3000), 0, False, False)
            WallUtils.DisallowWallJoinAtEnd(aw, 0); WallUtils.DisallowWallJoinAtEnd(aw, 1)
            r["abut"] = c["abut_wall_type"]
        v = ViewPlan.Create(doc, vft.Id, level.Id)
        v.Name = u"FT торец %s" % c["key"]
        v.Scale = 2; v.DetailLevel = ViewDetailLevel.Fine
        cb = v.CropBox
        cx = xe - MM(60)
        cb.Min = XYZ(cx - MM(HALF), P0.Y - MM(HALF * 0.6), cb.Min.Z); cb.Max = XYZ(cx + MM(HALF), P0.Y + MM(HALF * 0.6), cb.Max.Z)
        v.CropBox = cb; v.CropBoxActive = True; v.CropBoxVisible = False
        t.Commit()
        views.append((v, c["key"]))
        res["cases"].append(r)
    for v, key in views:
        opt = ImageExportOptions()
        opt.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); opt.SetViewsAndSheets(ids)
        opt.FilePath = os.path.join(OUT, key)
        opt.ZoomType = ZoomFitType.FitToPage; opt.PixelSize = int(args.get("px", 1400))
        opt.HLRandWFViewsFileType = ImageFileType.PNG; opt.ShadowViewsFileType = ImageFileType.PNG
        opt.ImageResolution = ImageResolution.DPI_300
        doc.ExportImage(opt)
    res["png"] = sorted(f for f in os.listdir(OUT) if f.lower().endswith(".png"))
    res["warnings"] = len(doc.GetWarnings())
finally:
    tg.RollBack()
bad = [c for c in res["cases"] if c.get("error")]
__output__ = {"status": "completed_unverified" if not bad else "partial", "summary": u"планов %d, ошибок %d, PNG %d; всё откатано" % (len(res["cases"]), len(bad), len(res.get("png", []))), "result": res}
