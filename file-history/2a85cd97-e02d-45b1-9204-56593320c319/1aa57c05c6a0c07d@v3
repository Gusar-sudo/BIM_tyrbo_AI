# -*- coding: utf-8 -*-
# Универсальный столб (FSC05 М3 / FSC18 М2): угловой профиль под angle_deg, вторая стена — на держателе.
# Основа — «угловой … левый» 90°: стена A вдоль -X профиля, стена B вдоль -Y.
# 1) Во вложенной графике узла группы rot_names (все экземпляры) и рейка стены B (группа rail_name с меньшим Y)
#    поворачиваются вокруг центра круга (0,0) на (angle-90)°.
#      М3: rot_names = ["FC.C-06"] (держатель стены B), столб с ножками A не трогается;
#      М2: rot_names = ["FS.C-18"] (столб — его ножки держат стену B), держатель FS.C-19 стены A не трогается.
# 2) Тело профиля (собственные линии) — готовые контуры из body_json[angle] (batches\M2_C\body_union.py):
#    точное объединение деталей узла, без коробок, двойного круга и вырезов под стекло.
# Сохраняет КОПИИ .rfa в out_dir; проект не меняется.
# Аргументы: jobs [{src_family, new_name, angle_deg}], body_json, out_dir, rot_names, rail_name
import json, io, math, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
byname = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
BJ = json.loads(io.open(args["body_json"], encoding="utf-8").read())
ROT = args["rot_names"]; RAIL = args["rail_name"]


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = False; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = False; return True


res = []
for job in args["jobs"]:
    r = {"new": job["new_name"], "angle": job["angle_deg"], "ok": False}
    dang = math.radians(float(job["angle_deg"]) - 90.0)
    pdoc = doc.EditFamily(byname[job["src_family"]])
    try:
        fi = list(FilteredElementCollector(pdoc).OfClass(FamilyInstance))[0]
        T = fi.GetTotalTransform(); ysg = -1 if fi.Mirrored else 1
        nd = pdoc.EditFamily(fi.Symbol.Family)
        try:
            groups = list(FilteredElementCollector(nd).OfClass(Group))

            def cen_y(g):
                ys = []
                for mid in g.GetMemberIds():
                    el = nd.GetElement(mid)
                    if isinstance(el, CurveElement) and el.GeometryCurve is not None:
                        ys += [ysg * T.OfPoint(p).Y for p in el.GeometryCurve.Tessellate()]
                return sum(ys) / len(ys)
            rails = [g for g in groups if g.GroupType.Name == RAIL]
            railB = min(rails, key=cen_y)
            rot = [g for g in groups if g.GroupType.Name in ROT] + [railB]
            r["rotated"] = [g.GroupType.Name for g in rot]
            if abs(dang) > 1e-9:
                t = Transaction(nd, u"поворот стены B"); t.Start()
                ElementTransformUtils.RotateElements(nd, List[ElementId]([g.Id for g in rot]), Line.CreateBound(XYZ.Zero, XYZ.BasisZ), dang * ysg)
                t.Commit()
            nd.LoadFamily(pdoc, LoadOpt())
        finally:
            nd.Close(False)
        out_loops = BJ[str(int(job["angle_deg"]))]
        t = Transaction(pdoc, u"тело профиля"); t.Start()
        old = [ce.Id for ce in FilteredElementCollector(pdoc).OfClass(CurveElement) if ce.GetType().Name in ("DetailLine", "DetailArc", "DetailNurbSpline", "DetailEllipse", "DetailCurve")]
        view = [v for v in FilteredElementCollector(pdoc).OfClass(ViewPlan) if not v.IsTemplate][0]
        pdoc.Delete(List[ElementId](old))
        n = 0
        for lp in out_loops:
            for i in range(len(lp)):
                a = lp[i]; b = lp[(i + 1) % len(lp)]
                pdoc.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(a[0] / FT, a[1] / FT, 0), XYZ(b[0] / FT, b[1] / FT, 0))); n += 1
        t.Commit()
        xs = [p[0] for lp in out_loops for p in lp]; ys = [p[1] for lp in out_loops for p in lp]
        r.update(loops=len(out_loops), lines=n, bbox_mm=[round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)])
        opts = SaveAsOptions(); opts.OverwriteExistingFile = True
        r["rfa"] = os.path.join(args["out_dir"], job["new_name"] + u".rfa"); pdoc.SaveAs(r["rfa"], opts)
        r["ok"] = True
    except Exception as ex:
        import traceback
        r["error"] = traceback.format_exc()[-400:]
    finally:
        pdoc.Close(False)
    res.append(r)
__output__ = {"status": "completed_unverified" if all(x["ok"] for x in res) else "partial",
              "summary": u"профилей: %d из %d; проект не изменён" % (sum(1 for x in res if x["ok"]), len(res)), "results": res}
