# -*- coding: utf-8 -*-
# Цветная графика узла: в графику узла (вложенное «Элементы узлов») профиля из .rfa добавляется заливка
# «алюминий» по готовым контурам (batches\M2_C\fill_mask.py: внешний контур + полости), граница невидимая,
# заливка уходит под линии. Тип заливки FT_Алюминий: сплошная, цвет rgb. Сохраняет КОПИЮ .rfa в out_dir.
# Аргументы: rfa_path, fills_json, out_dir, rgb [184,196,208], type_name ("FT_Алюминий")
import json, io, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
FT = 304.8
F = json.loads(io.open(args["fills_json"], encoding="utf-8").read())["regions"]
RGB = args.get("rgb", [184, 196, 208]); TN = args.get("type_name", u"FT_Алюминий")


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


TOL_MM = __revit__.Application.ShortCurveTolerance * FT * 1.15


def clean(pts):
    """убрать точки, дающие отрезки короче допуска Revit (включая замыкающий)"""
    out = []
    for p in pts:
        if not out or ((p[0] - out[-1][0]) ** 2 + (p[1] - out[-1][1]) ** 2) ** 0.5 >= TOL_MM:
            out.append(p)
    while len(out) > 3 and ((out[0][0] - out[-1][0]) ** 2 + (out[0][1] - out[-1][1]) ** 2) ** 0.5 < TOL_MM:
        out.pop()
    return out


def loop_of(pts):
    pts = clean(pts)
    cl = CurveLoop(); n = len(pts)
    for i in range(n):
        a = pts[i]; b = pts[(i + 1) % n]
        cl.Append(Line.CreateBound(XYZ(a[0] / FT, a[1] / FT, 0), XYZ(b[0] / FT, b[1] / FT, 0)))
    return cl


res = {"ok": False}
if args.get("rfa_path"):
    pd = __revit__.Application.OpenDocumentFile(args["rfa_path"]); base = os.path.basename(args["rfa_path"])
else:   # семейство из активного проекта (копия; сам проект не меняется)
    _d = __revit__.ActiveUIDocument.Document
    pd = _d.EditFamily([f for f in FilteredElementCollector(_d).OfClass(Family) if f.Name == args["family"]][0]); base = args["family"] + u".rfa"
try:
    fi = list(FilteredElementCollector(pd).OfClass(FamilyInstance))[0]
    nd = pd.EditFamily(fi.Symbol.Family)
    try:
        t = Transaction(nd, u"цвет: алюминий"); t.Start()
        try:
            solid = [fp for fp in FilteredElementCollector(nd).OfClass(FillPatternElement) if fp.GetFillPattern().IsSolidFill][0]
            frts = list(FilteredElementCollector(nd).OfClass(FilledRegionType))
            ft = [x for x in frts if x.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == TN]
            ft = ft[0] if ft else frts[0].Duplicate(TN)
            ft.ForegroundPatternId = solid.Id; ft.ForegroundPatternColor = Color(RGB[0], RGB[1], RGB[2])
            ft.BackgroundPatternId = ElementId.InvalidElementId   # сплошная заливка в семействе всегда маскирующая — поэтому SendToBack
            # уже нарисованный уплотнитель (заливка чёрным) — в тот же цвет, что материал уплотнителя в панелях
            SEAL = args.get("seal_rgb", [70, 72, 76]); res["seal_types_recolored"] = 0
            for x in frts:
                if x.Id == ft.Id:
                    continue
                c0 = x.ForegroundPatternColor
                if c0.IsValid and c0.Red < 30 and c0.Green < 30 and c0.Blue < 30:
                    x.ForegroundPatternColor = Color(SEAL[0], SEAL[1], SEAL[2]); res["seal_types_recolored"] += 1
            views = [v for v in FilteredElementCollector(nd).OfClass(View) if not v.IsTemplate and v.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Detail, ViewType.DraftingView)]
            view = views[0]
            inv = None
            for gs in FilteredElementCollector(nd).OfClass(GraphicsStyle):
                nm = gs.Name or ""
                if (u"Невидим" in nm or "Invisible" in nm) and FilledRegion.IsValidLineStyleIdForFilledRegion(nd, gs.Id):
                    inv = gs.Id; break
            made = []; errs = []
            for r in F:
                ll = List[CurveLoop]()
                try:
                    ll.Add(loop_of(r["outer"]))
                    for k, h in enumerate(r["holes"]):
                        try:
                            ll.Add(loop_of(h))
                        except Exception as exh:   # крошечная полость — пропустить (зальётся вместе со стенкой)
                            errs.append(u"полость %d пропущена: %d точек" % (k, len(h)))
                    fr = FilledRegion.Create(nd, ft.Id, view.Id, ll)
                    if inv is not None:
                        fr.SetLineStyleId(inv)
                    made.append(fr.Id)
                except Exception as ex:
                    errs.append(str(ex)[:160])
            try:
                DetailElementOrderUtils.SendToBack(nd, view, List[ElementId](made)); res["to_back"] = True
            except Exception as ex:
                res["to_back"] = str(ex)[:120]
            res.update(regions=len(made), errors=errs, invisible_lines=inv is not None, view=view.Name)
            t.Commit()
        except Exception:
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
            raise
        nd.LoadFamily(pd, LoadOpt())
    finally:
        nd.Close(False)
    if not os.path.isdir(args["out_dir"]):
        os.makedirs(args["out_dir"])
    o = SaveAsOptions(); o.OverwriteExistingFile = True
    res["rfa"] = os.path.join(args["out_dir"], base); pd.SaveAs(res["rfa"], o)
    res["ok"] = res.get("regions", 0) > 0
finally:
    pd.Close(False)
__output__ = {"status": "completed_unverified" if res["ok"] else "partial", "summary": u"заливок %s; копия %s; проект не менялся" % (res.get("regions"), res.get("rfa")), "result": res}
