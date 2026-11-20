# -*- coding: utf-8 -*-
# Как silhouette_moves.py, но семейства берутся из проекта (EditFamily) и сохраняются копией в out_dir. Проект НЕ меняется.
# Аргументы: profiles [короткие имена без «BIMLIB_Профиль_»], moves_json, out_dir, tol_mm, args_out
import json, os
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if "args_file" in args:
    with open(args["args_file"], encoding="utf-8") as _f:
        args = json.load(_f)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
TOL = float(args.get("tol_mm", 0.06))
with open(args["moves_json"], encoding="utf-8") as f:
    MV = json.load(f)
if not os.path.isdir(args["out_dir"]):
    os.makedirs(args["out_dir"])
byname = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
res, items = [], []
for short in args["profiles"]:
    mv = MV[short]["moves"]
    fam = byname[u"BIMLIB_Профиль_" + short]
    r = {"profile": short[:50], "moved_ends": 0, "expected_ends": 2 * len(mv), "ok": False}

    def tgt(p):
        for x, y, nx, ny in mv:
            if abs(p.X * FT - x) <= TOL and abs(p.Y * FT - y) <= TOL:
                return XYZ(nx / FT, ny / FT, p.Z), True
        return p, False
    pdoc = doc.EditFamily(fam)
    try:
        t = Transaction(pdoc, u"силуэт: паз под уплотнитель"); t.Start()
        for ce in FilteredElementCollector(pdoc).OfClass(CurveElement):
            c = ce.GeometryCurve
            if not isinstance(c, Line):
                continue
            a, ma = tgt(c.GetEndPoint(0)); b, mb = tgt(c.GetEndPoint(1))
            if ma or mb:
                ce.SetGeometryCurve(Line.CreateBound(a, b), True)
                r["moved_ends"] += int(ma) + int(mb)
        t.Commit()
        opts = SaveAsOptions(); opts.OverwriteExistingFile = True
        rfa = os.path.join(args["out_dir"], fam.Name + u".rfa")
        pdoc.SaveAs(rfa, opts)
        r["ok"] = r["moved_ends"] == r["expected_ends"]
        sid = list(fam.GetFamilySymbolIds())[0]
        items.append({"symbol_id": int(sid.Value), "rfa": rfa, "family": fam.Name})
    except Exception as ex:
        r["error"] = str(ex)[:200]
    finally:
        pdoc.Close(False)
    res.append(r)
with open(args["args_out"], "w", encoding="utf-8") as f:
    json.dump({"items": items}, f, ensure_ascii=False)
__output__ = {"status": "completed_unverified" if all(x["ok"] for x in res) else "partial",
              "summary": u"профилей %d, все концы совпали %d; проект не изменён" % (len(res), sum(1 for x in res if x["ok"])), "results": res}
