# -*- coding: utf-8 -*-
# FS.C-01К: в собственном контуре профиля (тело импоста) паз под стекло начинается с |y|=30.7 мм, у FS.C-01 и по графике — с 20.6.
# Скрипт: для каждого семейства профиля с подстрокой match в имени переносит вершины контура |y|≈from -> to (только вершины
# паза, |x| >= x_min), сохраняет копию rfa в out_dir и (в группе транзакций) загружает в проект. dry_run -> откат проекта.
# Аргументы: match, from_mm, to_mm, x_min_mm, out_dir, dry_run, only (необязательно: список имён)
import json, os, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
DRY = bool(args.get("dry_run", True))
Y0 = float(args.get("from_mm", 30.7)); Y1 = float(args.get("to_mm", 20.6)); XM = float(args.get("x_min_mm", 7.0))
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


def mv(p):
    x, y = p.X * FT, p.Y * FT
    if abs(abs(y) - Y0) < 0.06 and abs(x) >= XM:
        return XYZ(p.X, (Y1 if y > 0 else -Y1) / FT, p.Z), True
    return p, False


fams = [f for f in FilteredElementCollector(doc).OfClass(Family) if args["match"] in f.Name and f.Name.startswith(u"BIMLIB_Профиль_")]
if args.get("only"):
    fams = [f for f in fams if f.Name in args["only"]]
res = {"families": [], "skipped": []}
rfas = []
for f in fams:
    r = {"family": f.Name}
    pdoc = doc.EditFamily(f)
    try:
        lines = [ce for ce in FilteredElementCollector(pdoc).OfClass(CurveElement) if ce.GeometryCurve is not None and isinstance(ce.GeometryCurve, Line)]
        plan = []
        for ce in lines:
            c = ce.GeometryCurve
            a, ma = mv(c.GetEndPoint(0)); b, mb = mv(c.GetEndPoint(1))
            if ma or mb:
                plan.append((ce, a, b))
        r["moved_lines"] = len(plan)
        if not plan:
            res["skipped"].append(f.Name.replace(u"BIMLIB_Профиль_", u""))
            continue
        t = Transaction(pdoc, u"Паз под стекло 20.6"); t.Start()
        try:
            for ce, a, b in plan:
                if a.DistanceTo(b) * FT < 0.5:
                    pdoc.Delete(ce.Id)      # вырожденный отрезок (боковая стенка паза стала нулевой)
                else:
                    ce.SetGeometryCurve(Line.CreateBound(a, b), True)
            t.Commit()
        except Exception as e:
            t.RollBack(); raise
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        p = os.path.join(OUT, f.Name + u".rfa")
        pdoc.SaveAs(p, so)
        rfas.append(p); r["ok"] = True
    except Exception as ex:
        r["error"] = str(ex)[:200]
    finally:
        try:
            pdoc.Close(False)
        except Exception:
            pass
    res["families"].append(r)

tg = TransactionGroup(doc, u"FS.C-01К: паз под стекло"); tg.Start()
try:
    t = Transaction(doc, u"загрузка профилей"); t.Start()
    res["loaded"] = sum(1 for p in rfas if doc.LoadFamily(p, LoadOpt(), clr.Reference[Family]()))
    t.Commit()
    res["warnings"] = len(doc.GetWarnings())
finally:
    if DRY:
        tg.RollBack()
    else:
        tg.Assimilate()
bad = [x["family"] for x in res["families"] if "error" in x]
res["status"] = "completed_unverified" if not bad else "partial"
res["summary"] = u"%sисправлено %d, без изменений %d, ошибок %d, загружено %d" % (u"ПРОБНЫЙ ПРОГОН (откат): " if DRY else u"", len(rfas), len(res["skipped"]), len(bad), res.get("loaded", 0))
__output__ = res
