# -*- coding: utf-8 -*-
# Этап 2 жалюзи: в готовой копии семейства (пакет + карниз, make_blinds_family.py) добавляет отдельные наклонные ламели.
#  - пакет виден только на «Низкая/Средняя», ламели — только на «Высокая»;
#  - ламели: одно выдавливание из N сечений (ширина lamel_w_mm, толщина lamel_t_mm, шаг lamel_step_mm, наклон lamel_angle_deg),
#    в плоскости «Слева», торец выровнен по «Справа»; выше низа карниза срезаются пустотой, привязанной к «Жалюзи_Карниз».
# Открывает src_rfa (файл), сохраняет в out_rfa. Проект не меняется. Аргументы: src_rfa, out_rfa, lamel_*.
import json, os, math
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
FT = 304.8
MM = lambda v: v / FT
res = {}
fd = app.OpenDocumentFile(args["src_rfa"])
t = None
try:
    fm = fd.FamilyManager
    P = dict((p.Definition.Name, p) for p in fm.Parameters)
    p_vis = P[u"FT_Жалюзи_Видимость"]; p_ml = P[u"Материал_жалюзи"]
    rps = dict((rp.Name, rp) for rp in FilteredElementCollector(fd).OfClass(ReferencePlane))
    xl = rps[u"Слева"].BubbleEnd.X; xr = rps[u"Справа"].BubbleEnd.X
    rk = rps[u"Жалюзи_Карниз"]; zk = rk.BubbleEnd.Z
    rpc = rps[u"По центру (Вперед/Вправо)"]; y0 = rpc.BubbleEnd.Y
    view = None
    for v in FilteredElementCollector(fd).OfClass(View):
        try:
            if not v.IsTemplate and v.ViewType == ViewType.Elevation and abs(abs(v.ViewDirection.Y) - 1) < 1e-6:
                view = v; break
        except Exception:
            pass
    # пакет = выдавливание с видимостью FT_Жалюзи_Видимость и материалом Материал_жалюзи
    pack = []
    for ex in FilteredElementCollector(fd).OfClass(Extrusion):
        pv = fm.GetAssociatedFamilyParameter(ex.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM))
        pm = fm.GetAssociatedFamilyParameter(ex.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM))
        if pv and pm and pv.Id == p_vis.Id and pm.Id == p_ml.Id:
            pack.append(ex)
    res["pack_found"] = len(pack)
    t = Transaction(fd, u"Жалюзи ламели"); t.Start()
    for ex in pack:
        fv = FamilyElementVisibility(FamilyElementVisibilityType.Model)
        fv.IsShownInFine = False
        ex.SetVisibility(fv)
    LW = float(args.get("lamel_w_mm", 25)); LT = float(args.get("lamel_t_mm", 1.0)); ST = float(args.get("lamel_step_mm", 22))
    ANG = math.radians(float(args.get("lamel_angle_deg", 30))); HMAX = float(args.get("lamel_hmax_mm", 4200))
    rl = rps[u"Слева"]
    spl = SketchPlane.Create(fd, rl.Id)
    xs = xl
    cs_, sn_ = math.cos(ANG), math.sin(ANG)
    caa = CurveArrArray()
    n_ = 1 if args.get("mode") == "array" else int(HMAX / ST)
    hy = MM(LW / 2.0) * cs_; hz = MM(LW / 2.0) * sn_
    ty = -MM(LT / 2.0) * sn_; tz = MM(LT / 2.0) * cs_
    for i in range(n_):
        zc = MM(ST * (i + 0.5))
        p = [XYZ(xs, y0 - hy + ty, zc - hz + tz), XYZ(xs, y0 + hy + ty, zc + hz + tz), XYZ(xs, y0 + hy - ty, zc + hz - tz), XYZ(xs, y0 - hy - ty, zc - hz - tz)]
        ca = CurveArray()
        for j in range(4):
            ca.Append(Line.CreateBound(p[j], p[(j + 1) % 4]))
        caa.Append(ca)
    e3 = fd.FamilyCreate.NewExtrusion(True, caa, spl, MM(100))
    fd.Regenerate()
    bb3 = e3.get_BoundingBox(None)
    sign = 1 if (bb3.Max.X + bb3.Min.X) / 2 > xs else -1
    e3.get_Parameter(BuiltInParameter.EXTRUSION_END_PARAM).Set(sign * abs(xr - xl))
    fd.Regenerate()
    go = Options(); go.ComputeReferences = True; go.IncludeNonVisibleObjects = True
    far = None
    for g in e3.get_Geometry(go):
        if isinstance(g, Solid):
            for f in g.Faces:
                if isinstance(f, PlanarFace) and abs(abs(f.FaceNormal.X) - 1) < 1e-6 and abs(f.Origin.X - xr) < MM(0.5):
                    far = f; break
        if far:
            break
    try:
        fd.FamilyCreate.NewAlignment(view, rps[u"Справа"].GetReference(), far.Reference); res["lamel_end_aligned"] = True
    except Exception as e:
        res["lamel_end_aligned"] = str(e)[:100]
    fm.AssociateElementParameterToFamilyParameter(e3.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM), p_vis)
    fm.AssociateElementParameterToFamilyParameter(e3.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM), p_ml)
    fv3 = FamilyElementVisibility(FamilyElementVisibilityType.Model)
    fv3.IsShownInCoarse = False; fv3.IsShownInMedium = False
    e3.SetVisibility(fv3)
    fd.Regenerate()
    # пустота выше низа карниза
    sp = SketchPlane.Create(fd, rpc.Id)
    al3 = []

    def make_void():
        pts = [XYZ(xl - MM(200), y0, zk), XYZ(xr + MM(200), y0, zk), XYZ(xr + MM(200), y0, MM(HMAX + 800)), XYZ(xl - MM(200), y0, MM(HMAX + 800))]
        ca = CurveArray()
        for j in range(4):
            ca.Append(Line.CreateBound(pts[j], pts[(j + 1) % 4]))
        cv = CurveArrArray(); cv.Append(ca)
        vd = fd.FamilyCreate.NewExtrusion(False, cv, sp, MM(60))
        vd.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM).Set(MM(-60))
        fd.Regenerate()
        for arr in vd.Sketch.Profile:
            for c in arr:
                a, b = c.GetEndPoint(0), c.GetEndPoint(1)
                if abs(a.Z - b.Z) < 1e-6 and abs(a.Z - zk) < 1e-6:
                    try:
                        fd.FamilyCreate.NewAlignment(view, rk.GetReference(), c.Reference); al3.append(True)
                    except Exception as e:
                        al3.append(str(e)[:80])
        try:
            cea = CombinableElementArray(); cea.Append(e3); cea.Append(vd)
            gc = fd.CombineElements(cea); al3.append(u"combine %s" % gc.Id.Value)
        except Exception as e:
            al3.append(u"combine: " + str(e)[:80])
    if args.get("mode") == "array":
        # массив ламелей: количество = rounddown((высота панели - карниз) / шаг), не меньше 2
        p_st = P.get(u"FT_Жалюзи_Шаг") or fm.AddParameter(u"FT_Жалюзи_Шаг", GroupTypeId.Construction, SpecTypeId.Length, False)
        p_n = P.get(u"FT_Жалюзи_Ламелей") or fm.AddParameter(u"FT_Жалюзи_Ламелей", GroupTypeId.Construction, SpecTypeId.Int.Integer, True)
        fm.SetFormula(p_st, u"%g мм" % ST)
        fm.SetFormula(p_n, u"if(ADSK_Размер_Высота - FT_Жалюзи_Карниз < 2 * FT_Жалюзи_Шаг, 2, rounddown((ADSK_Размер_Высота - FT_Жалюзи_Карниз) / FT_Жалюзи_Шаг))")
        fd.Regenerate()
        n0 = fm.CurrentType.AsInteger(p_n) or 2
        ids = List[ElementId](); ids.Add(e3.Id)
        la = LinearArray.Create(fd, view, ids, max(2, n0), XYZ(0, 0, MM(ST)), ArrayAnchorMember.Second)
        fd.Regenerate()
        la.Label = p_n
        fd.Regenerate()
        al3.append(u"array %s n=%s" % (la.Id.Value, fm.CurrentType.AsInteger(p_n)))
    elif not args.get("no_void"):
        make_void()
    fd.Regenerate()
    zs = []
    o = Options(); o.DetailLevel = ViewDetailLevel.Fine
    for el in [e3] + [x for x in FilteredElementCollector(fd).OfClass(GeomCombination)]:
        for g in el.get_Geometry(o) or []:
            if isinstance(g, Solid) and g.Volume > 0:
                for ed in g.Edges:
                    zs.append(max(p.Z for p in ed.Tessellate()) * FT)
    res["lamel_zmax_geom"] = round(max(zs), 1) if zs else None
    res["zk"] = round(zk * FT, 1)
    bb = e3.get_BoundingBox(None)
    res["lamels"] = {"count": n_, "sign": sign, "void": al3,
                     "bbox_mm": [round(bb.Min.X * FT, 1), round(bb.Min.Y * FT, 1), round(bb.Min.Z * FT, 1), round(bb.Max.X * FT, 1), round(bb.Max.Y * FT, 1), round(bb.Max.Z * FT, 1)]}
    t.Commit(); t = None
    so = SaveAsOptions(); so.OverwriteExistingFile = True
    fd.SaveAs(args["out_rfa"], so)
    res["rfa"] = args["out_rfa"]
finally:
    if t is not None and t.HasStarted() and not t.HasEnded():
        t.RollBack()
    try:
        fd.Close(False)
    except Exception as e:
        res["close"] = str(e)[:80]
vv = res.get("lamels", {}).get("void", [])
ok = res.get("lamel_end_aligned") is True and (True in vv or any(str(x).startswith(u"array") for x in vv))
__output__ = {"status": "completed_unverified" if ok else "partial", "summary": u"ламели: %s" % res.get("lamels"), "result": res}
