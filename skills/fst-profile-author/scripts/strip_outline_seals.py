# -*- coding: utf-8 -*-
# Убрать нарисованный уплотнитель во вложенных 2D профилей: сплошные заливки <= max_mm и замкнутые контуры <= max_mm
# (линии/дуги, связанные общими концами). Контуры с центром ближе exclude_axis_mm к оси x=0 не трогаются (это не уплотнитель).
# EditFamily -> вложенные: удалить -> загрузить обратно -> SaveAs копией в out_dir. Проект НЕ меняется.
# Аргументы: profiles [короткие имена без «BIMLIB_Профиль_»], out_dir, max_mm, exclude_axis_mm, args_out
import json, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MAX = float(args.get("max_mm", 12.0))
EXA = float(args.get("exclude_axis_mm", 1.0))
if not os.path.isdir(args["out_dir"]):
    os.makedirs(args["out_dir"])


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


def key(p):
    return (round(p.X * FT, 2), round(p.Y * FT, 2))


byname = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
res, items = [], []
for short in args["profiles"]:
    fam = byname[u"BIMLIB_Профиль_" + short]
    r = {"profile": short[:60], "fills": 0, "loops": 0, "loop_centres": [], "ok": False}
    pdoc = doc.EditFamily(fam)
    try:
        for fi in list(FilteredElementCollector(pdoc).OfClass(FamilyInstance)):
            T = fi.GetTotalTransform()
            nd = pdoc.EditFamily(fi.Symbol.Family)
            try:
                dele = List[ElementId]()
                for fr in FilteredElementCollector(nd).OfClass(FilledRegion):
                    ft = nd.GetElement(fr.GetTypeId())
                    fp = nd.GetElement(ft.ForegroundPatternId) if ft else None
                    if fp is None or not fp.GetFillPattern().IsSolidFill:
                        continue
                    pts = [p for lp in fr.GetBoundaries() for c in lp for p in c.Tessellate()]
                    xs = [p.X * FT for p in pts]; ys = [p.Y * FT for p in pts]
                    if max(xs) - min(xs) <= MAX and max(ys) - min(ys) <= MAX:
                        dele.Add(fr.Id); r["fills"] += 1
                curves = []
                for ce in FilteredElementCollector(nd).OfClass(CurveElement):
                    c = ce.GeometryCurve
                    if c.IsBound:
                        curves.append((ce.Id, key(c.GetEndPoint(0)), key(c.GetEndPoint(1)), c.Tessellate()))
                parent = {}

                def find(a):
                    while parent.setdefault(a, a) != a:
                        parent[a] = parent[parent[a]]; a = parent[a]
                    return a
                for _, a, b, _ in curves:
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        parent[ra] = rb
                groups = {}
                for cid, a, b, pts in curves:
                    groups.setdefault(find(a), []).append((cid, a, b, pts))
                for g in groups.values():
                    deg = {}
                    for _, a, b, _ in g:
                        deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
                    if len(g) < 3 or any(v % 2 for v in deg.values()):
                        continue
                    pp = [T.OfPoint(p) for _, _, _, ps in g for p in ps]
                    gx = [p.X * FT for p in pp]; gy = [p.Y * FT for p in pp]
                    w = max(gx) - min(gx); h = max(gy) - min(gy)
                    cx = (max(gx) + min(gx)) / 2
                    if 2 < w <= MAX and 2 < h <= MAX and abs(cx) >= EXA:
                        for cid, _, _, _ in g:
                            dele.Add(cid)
                        r["loops"] += 1
                        r["loop_centres"].append([round(cx, 2), round((max(gy) + min(gy)) / 2, 2)])
                if dele.Count > 0:
                    t = Transaction(nd, u"Убрать нарисованный уплотнитель"); t.Start(); nd.Delete(dele); t.Commit()
                    nd.LoadFamily(pdoc, LoadOpt())
            finally:
                nd.Close(False)
        opts = SaveAsOptions(); opts.OverwriteExistingFile = True
        rfa = os.path.join(args["out_dir"], fam.Name + u".rfa")
        pdoc.SaveAs(rfa, opts)
        r["ok"] = True
        items.append({"symbol_id": int(list(fam.GetFamilySymbolIds())[0].Value), "rfa": rfa, "family": fam.Name})
    except Exception as ex:
        r["error"] = str(ex)[:200]
    finally:
        pdoc.Close(False)
    res.append(r)
with open(args["args_out"], "w", encoding="utf-8") as f:
    json.dump({"items": items}, f, ensure_ascii=False)
__output__ = {"status": "completed_unverified" if all(x["ok"] for x in res) else "partial",
              "summary": u"профилей %d, сохранено %d; проект не изменён" % (len(res), len(items)), "results": res}
