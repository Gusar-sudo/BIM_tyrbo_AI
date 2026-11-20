# -*- coding: utf-8 -*-
# Пакет: цветная графика узлов для многих профилей активного проекта (логика color_nested.py):
# заливка «алюминий» (FT_Алюминий, сплошная, под линиями, граница невидимая) по готовым контурам fills_dir\<семейство>.json,
# чёрные заливки уплотнителя -> цвет уплотнителя. Сохраняет КОПИИ .rfa в out_dir; сам проект не меняется.
# Аргументы: fills_dir, out_dir, families (список), rgb, seal_rgb
import json, io, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
RGB = args.get("rgb", [184, 196, 208]); SEAL = args.get("seal_rgb", [70, 72, 76]); TN = u"FT_Алюминий"
TOL_MM = __revit__.Application.ShortCurveTolerance * FT * 1.15
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


def clean(pts):
    out = []
    for p in pts:
        if not out or ((p[0] - out[-1][0]) ** 2 + (p[1] - out[-1][1]) ** 2) ** 0.5 >= TOL_MM:
            out.append(p)
    while len(out) > 3 and ((out[0][0] - out[-1][0]) ** 2 + (out[0][1] - out[-1][1]) ** 2) ** 0.5 < TOL_MM:
        out.pop()
    return out


def loop_of(pts):
    pts = clean(pts); cl = CurveLoop(); n = len(pts)
    for i in range(n):
        a = pts[i]; b = pts[(i + 1) % n]
        cl.Append(Line.CreateBound(XYZ(a[0] / FT, a[1] / FT, 0), XYZ(b[0] / FT, b[1] / FT, 0)))
    return cl


rows = []
for i, fn in enumerate(args["families"]):
    checkpoint(fn, i, len(args["families"]))
    r = {"family": fn, "ok": False}
    pd = None
    try:
        F = json.loads(io.open(os.path.join(args["fills_dir"], fn + u".json"), encoding="utf-8").read())["regions"]
        pd = doc.EditFamily(fams[fn])
        fi = list(FilteredElementCollector(pd).OfClass(FamilyInstance))[0]
        nd = pd.EditFamily(fi.Symbol.Family)
        try:
            t = Transaction(nd, u"цвет"); t.Start()
            try:
                solid = [fp for fp in FilteredElementCollector(nd).OfClass(FillPatternElement) if fp.GetFillPattern().IsSolidFill][0]
                frts = list(FilteredElementCollector(nd).OfClass(FilledRegionType))
                ft = [x for x in frts if x.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == TN]
                ft = ft[0] if ft else frts[0].Duplicate(TN)
                ft.ForegroundPatternId = solid.Id; ft.ForegroundPatternColor = Color(RGB[0], RGB[1], RGB[2])
                ft.BackgroundPatternId = ElementId.InvalidElementId
                r["seal_recolored"] = 0
                for x in frts:
                    if x.Id == ft.Id:
                        continue
                    c0 = x.ForegroundPatternColor
                    if c0.IsValid and c0.Red < 30 and c0.Green < 30 and c0.Blue < 30:
                        x.ForegroundPatternColor = Color(SEAL[0], SEAL[1], SEAL[2]); r["seal_recolored"] += 1
                view = [v for v in FilteredElementCollector(nd).OfClass(View) if not v.IsTemplate and v.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Detail, ViewType.DraftingView)][0]
                inv = None
                for gs in FilteredElementCollector(nd).OfClass(GraphicsStyle):
                    nm = gs.Name or ""
                    if (u"Невидим" in nm or "Invisible" in nm) and FilledRegion.IsValidLineStyleIdForFilledRegion(nd, gs.Id):
                        inv = gs.Id; break
                made = []; errs = []
                for reg in F:
                    ll = List[CurveLoop]()
                    try:
                        ll.Add(loop_of(reg["outer"]))
                        for k, h in enumerate(reg["holes"]):
                            try:
                                ll.Add(loop_of(h))
                            except Exception:
                                errs.append(u"полость пропущена")
                        try:
                            fr = FilledRegion.Create(nd, ft.Id, view.Id, ll)
                        except Exception:
                            # какая-то полость пересеклась с контуром после упрощения: добавляем полости по одной,
                            # оставляя только те, с которыми заливка создаётся
                            acc = [ll[0]]
                            for h in [ll[k] for k in range(1, ll.Count)]:
                                test = List[CurveLoop](acc + [h])
                                st = SubTransaction(nd); st.Start()
                                try:
                                    tmp = FilledRegion.Create(nd, ft.Id, view.Id, test); st.RollBack(); acc.append(h)
                                except Exception:
                                    st.RollBack(); errs.append(u"полость не принята")
                            fr = FilledRegion.Create(nd, ft.Id, view.Id, List[CurveLoop](acc))
                        if inv is not None:
                            fr.SetLineStyleId(inv)
                        made.append(fr.Id)
                    except Exception as ex:
                        errs.append(str(ex)[:120])
                if made:
                    try:
                        DetailElementOrderUtils.SendToBack(nd, view, List[ElementId](made))
                    except Exception as ex:
                        errs.append(u"порядок: " + str(ex)[:80])
                r.update(regions=len(made), regions_expected=len(F), errors=errs[:6], n_errors=len(errs))
                t.Commit()
            except Exception:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise
            nd.LoadFamily(pd, LoadOpt())
        finally:
            nd.Close(False)
        o = SaveAsOptions(); o.OverwriteExistingFile = True
        r["rfa"] = os.path.join(OUT, fn + u".rfa"); pd.SaveAs(r["rfa"], o)
        r["ok"] = r.get("regions", 0) > 0
    except Exception as ex:
        r["error"] = str(ex)[:160]
    finally:
        if pd is not None:
            pd.Close(False)
    rows.append(r)
io.open(os.path.join(OUT, u"_report.json"), "w", encoding="utf-8").write(json.dumps(rows, ensure_ascii=False, indent=1))
bad = [x for x in rows if not x["ok"]]
__output__ = {"status": "completed_unverified" if not bad else "partial", "summary": u"цветных копий %d из %d; проект не менялся" % (len(rows) - len(bad), len(rows)),
              "bad": [[x["family"], x.get("error") or x.get("errors")] for x in bad][:30],
              "with_errors": len([x for x in rows if x.get("n_errors")])}
