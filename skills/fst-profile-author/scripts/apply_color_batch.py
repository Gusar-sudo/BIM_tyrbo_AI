# -*- coding: utf-8 -*-
# ПРИМЕНЕНИЕ (без отката): загрузить копии .rfa профилей (каждая — своя транзакция) и задать цвета материалов;
# до/после: пересечения импостов с панелями, импосты без геометрии, предупреждения. Не сохраняет (save_doc.py отдельно).
# Аргументы: rfa_dir, materials {имя: {shade, cut|null, transp}}, out_json
import json, io, os, glob
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
rfas = sorted(glob.glob(os.path.join(args["rfa_dir"], "*.rfa")))


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


opt = Options()
panels = List[ElementId](FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType().ToElementIds())


def snapshot():
    clash = 0; nogeo = 0; n = 0
    for m in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType():
        n += 1
        g = m.get_Geometry(opt)
        if g is None or not any(True for _ in g): nogeo += 1; continue
        try:
            if FilteredElementCollector(doc, panels).WherePasses(ElementIntersectsElementFilter(m)).GetElementCount(): clash += 1
        except Exception: pass
    return {"mullions": n, "clash": clash, "nogeo": nogeo, "warnings": len(doc.GetWarnings())}


def hexc(h):
    h = h.lstrip("#"); return Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


res = {"before": snapshot(), "loaded": 0, "failed": []}
for i, p in enumerate(rfas):
    checkpoint(os.path.basename(p), i, len(rfas))
    t = Transaction(doc, u"цвет: " + os.path.basename(p)); t.Start()
    try:
        doc.LoadFamily(p, LO())
        if t.Commit() == TransactionStatus.Committed: res["loaded"] += 1
        else: res["failed"].append(os.path.basename(p))
    except Exception as ex:
        if t.HasStarted() and not t.HasEnded(): t.RollBack()
        res["failed"].append(os.path.basename(p) + ": " + str(ex)[:80])
solid = [fp for fp in FilteredElementCollector(doc).OfClass(FillPatternElement) if fp.GetFillPattern().IsSolidFill and fp.GetFillPattern().Target == FillPatternTarget.Drafting][0]
t = Transaction(doc, u"цвет: материалы (палитра B)"); t.Start()
mats = dict((m.Name, m) for m in FilteredElementCollector(doc).OfClass(Material)); res["materials"] = {}
for nm, sp in args.get("materials", {}).items():
    m = mats.get(nm)
    if m is None: res["materials"][nm] = u"нет"; continue
    if sp.get("shade"): m.Color = hexc(sp["shade"]); m.UseRenderAppearanceForShading = False
    if sp.get("cut"): m.CutForegroundPatternId = solid.Id; m.CutForegroundPatternColor = hexc(sp["cut"])
    if sp.get("transp") is not None: m.Transparency = int(sp["transp"])
    c = m.Color
    res["materials"][nm] = ["#%02x%02x%02x" % (c.Red, c.Green, c.Blue), m.Transparency, m.CutForegroundPatternId.Value != -1]
t.Commit()
res["after"] = snapshot()
io.open(args["out_json"], "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
ok = not res["failed"] and res["after"]["clash"] <= res["before"]["clash"] and res["after"]["nogeo"] == 0 and res["after"]["warnings"] <= res["before"]["warnings"]
__output__ = {"status": "completed_unverified" if ok else "partial", "summary": u"загружено %d/%d; коллизий %d→%d; без геометрии %d; предупреждений %d→%d; файл не сохранён" % (
    res["loaded"], len(rfas), res["before"]["clash"], res["after"]["clash"], res["after"]["nogeo"], res["before"]["warnings"], res["after"]["warnings"]), "result": res}
