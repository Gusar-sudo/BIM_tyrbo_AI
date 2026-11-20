# -*- coding: utf-8 -*-
# Только чтение: силуэт профиля (линии/дуги семейства профиля) и нарисованные уплотнители (заливки <= 12 мм во вложенных 2D,
# в координатах профиля) для заданных семейств -> JSON. Аргументы: names (без префикса BIMLIB_Профиль_), out_json
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if "args_file" in args:
    with open(args["args_file"], encoding="utf-8") as _f:
        args = json.load(_f)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
byname = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
out = {}
if args["names"] == "ALL":
    _s = set()
    for mt in FilteredElementCollector(doc).OfClass(MullionType):
        p = mt.get_Parameter(BuiltInParameter.MULLION_PROFILE)
        if p and p.AsElementId() != ElementId.InvalidElementId:
            e = doc.GetElement(p.AsElementId())
            if e is not None and e.Family.Name.startswith(u"BIMLIB_Профиль_"):
                _s.add(e.Family.Name[15:])
    args["names"] = sorted(_s)
for short in args["names"]:
    fam = byname[u"BIMLIB_Профиль_" + short]
    pdoc = doc.EditFamily(fam)
    r = {"curves": [], "seals": []}
    try:
        for ce in FilteredElementCollector(pdoc).OfClass(CurveElement):
            c = ce.GeometryCurve
            if isinstance(c, Arc):
                r["curves"].append({"t": "arc", "c": [c.Center.X * FT, c.Center.Y * FT], "r": c.Radius * FT,
                                    "p": [[p.X * FT, p.Y * FT] for p in c.Tessellate()]})
            else:
                r["curves"].append({"t": "line", "p": [[p.X * FT, p.Y * FT] for p in (c.GetEndPoint(0), c.GetEndPoint(1))]})
        for fi in FilteredElementCollector(pdoc).OfClass(FamilyInstance):
            T = fi.GetTotalTransform()
            nd = pdoc.EditFamily(fi.Symbol.Family)
            try:
                for fr in FilteredElementCollector(nd).OfClass(FilledRegion):
                    ft = nd.GetElement(fr.GetTypeId())
                    fp = nd.GetElement(ft.ForegroundPatternId) if ft else None
                    if fp is None or not fp.GetFillPattern().IsSolidFill:
                        continue
                    pts = [T.OfPoint(p) for lp in fr.GetBoundaries() for c in lp for p in c.Tessellate()]
                    xs = [p.X * FT for p in pts]; ys = [p.Y * FT for p in pts]
                    if max(xs) - min(xs) <= 12 and max(ys) - min(ys) <= 12:
                        r["seals"].append([min(xs), min(ys), max(xs), max(ys)])
            finally:
                nd.Close(False)
    finally:
        pdoc.Close(False)
    out[short] = r
with open(args["out_json"], "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
__output__ = {"status": "completed_unverified", "summary": u"выгружено %d профилей" % len(out),
              "counts": dict((k, [len(v["curves"]), len(v["seals"])]) for k, v in out.items())}
