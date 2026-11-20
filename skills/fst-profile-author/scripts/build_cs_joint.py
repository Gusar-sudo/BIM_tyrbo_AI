# -*- coding: utf-8 -*-
# Цельностеклянный стык (замечания 10.11): сохраняет КОПИИ семейств в out_dir, проект не меняется.
# 1) Панель (panel_family): параметр типа FT_Уплотнитель_Бок_Показать; видимость боковых «рукавов» уплотнителя
#    = and(FT_Уплотнитель_Ux_Показать, FT_Уплотнитель_Бок_Показать); длина уплотнителя без боков, если бок выключен;
#    материал ламелей жалюзи -> параметр «Материал_жалюзи».
# 2) Профили межстекольного УП-008: копия base_profile, контур = два прямоугольника 2 × (glass_depth) у каждого стекла.
# 3) Профили края цельностеклянных: во вложенные «Элементы узлов» — заливка уплотнителя стекла (форма бокового
#    рукава панели для стекла seal_glass мм) у кромки стекла (крайняя точка контура со стороны стекла).
# Аргументы: out_dir, panel_family, seal_glass_mm (8), up008 [{save_as, outer_mm}], up_base_profile, up_width_mm (2),
#            up_depth_mm (13), edges [{name, save_as?}]
import json, os, io, clr
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
FT = 304.8
MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
res = {"panel": {}, "up008": [], "edges": []}
T = Transaction


def tx(d, name, fn):
    t = T(d, name); t.Start()
    try:
        r = fn(); t.Commit(); return r
    except Exception:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        raise


# ---------- 1) панель ----------
seal_loops = None   # кривые бокового рукава для стекла seal_glass (левый бок панели), в координатах панели
pd = doc.EditFamily(fams[args["panel_family"]]) if not args.get("skip_panel") else None
try:
  if pd is not None:
    fm = pd.FamilyManager
    P = dict((p.Definition.Name, p) for p in fm.Parameters)
    tpt = None
    if args.get("panel_type"):   # форму уплотнителя снимать с этого типа панели (толщина стекла!); только чтение — откат
        tpt = T(pd, u"FT: тип панели для формы"); tpt.Start()
        fm.CurrentType = [x for x in fm.Types if x.Name == args["panel_type"]][0]
        pd.Regenerate()
        res["panel"]["shape_type"] = args["panel_type"]
    sweeps = [s for s in FilteredElementCollector(pd).OfClass(Sweep)]

    def vis_name(e):
        a = fm.GetAssociatedFamilyParameter(e.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM))
        return a.Definition.Name if a else None
    side = [s for s in sweeps if (lambda b: (b.Max.X - b.Min.X) * FT < 20)(s.get_BoundingBox(None))]
    gl = int(args.get("seal_glass_mm", 8))
    key = u"FT_Уплотнитель_U%d_Показать" % gl
    pick = [s for s in side if vis_name(s) in (key, u"FT_Уплотнитель_U%d_Бок" % gl) and s.get_BoundingBox(None).Max.X < 0]
    if pick:
        loops = []
        opt = Options(); opt.DetailLevel = ViewDetailLevel.Fine
        for s in pick:   # форма = нижний торец твёрдого тела рукава (рукав идёт по z)
            try:
                for g in s.get_Geometry(opt):
                    if isinstance(g, Solid) and g.Volume > 0:
                        caps = [f for f in g.Faces if isinstance(f, PlanarFace) and abs(f.FaceNormal.Z) > 0.99]
                        cap = sorted(caps, key=lambda f: f.Origin.Z)[0]
                        for cl in cap.GetEdgesAsCurveLoops():
                            loops.append([c for c in cl])
            except Exception as ex:
                res["panel"]["seal_profile_error"] = str(ex)
        glass = [e for e in FilteredElementCollector(pd).OfClass(Extrusion) if vis_name(e) is None]
        gx = min(e.get_BoundingBox(None).Min.X for e in glass)
        seal_loops = (loops, gx)
        res["panel"]["seal_loops"] = len(loops); res["panel"]["glass_edge_mm"] = round(gx * FT, 2)
        xs_ = [c.GetEndPoint(0) for lp in loops for c in lp]
        if xs_:
            res["panel"]["seal_bbox_mm"] = [round(min(p.X for p in xs_) * FT, 2), round(max(p.X for p in xs_) * FT, 2), round(min(p.Y for p in xs_) * FT, 2), round(max(p.Y for p in xs_) * FT, 2)]
    if tpt is not None:
        tpt.RollBack()

    def edit_panel():
        if args.get("panel_read_only"):   # только взять форму уплотнителя, панель не менять
            return {"read_only": True}
        out = {}
        bok = P.get(u"FT_Уплотнитель_Бок_Показать") or fm.AddParameter(u"FT_Уплотнитель_Бок_Показать", GroupTypeId.Graphics, SpecTypeId.Boolean.YesNo, False)
        for t in fm.Types:
            fm.CurrentType = t; fm.Set(bok, 1)
        n = 0
        for g in (5, 6, 8, 10):
            nm = u"FT_Уплотнитель_U%d_Бок" % g
            pp = P.get(nm) or fm.AddParameter(nm, GroupTypeId.Graphics, SpecTypeId.Boolean.YesNo, False)
            fm.SetFormula(pp, u"and(FT_Уплотнитель_U%d_Показать, FT_Уплотнитель_Бок_Показать)" % g)
            for s in side:
                if vis_name(s) in (u"FT_Уплотнитель_U%d_Показать" % g, nm):
                    fm.AssociateElementParameterToFamilyParameter(s.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM), pp); n += 1
        out["side_sweeps_rebound"] = n
        L = P[u"FT_Стекло_Уплотнитель_Длина"]
        fm.SetFormula(L, u"if(FT_Система_М1, 0 мм, 2 * (ADSK_Размер_Ширина + if(FT_Уплотнитель_Бок_Показать, ADSK_Размер_Высота, 0 мм)) * FT_Стекло_Уплотнитель_Линий)")
        mj = P.get(u"Материал_жалюзи"); k = 0; info = {}
        for fi in FilteredElementCollector(pd).OfClass(FamilyInstance):
            for mp in list(fi.Parameters) + list(fi.Symbol.Parameters):
                if mp.Definition.Name != u"Материал" or mp.StorageType != StorageType.ElementId:
                    continue
                a = fm.GetAssociatedFamilyParameter(mp)
                info[(u"тип" if mp.Element.Id == fi.Symbol.Id else u"экз") + u":" + (a.Definition.Name if a else u"—")] = 1
                if mp.Element.Id == fi.Symbol.Id:   # параметр типа вложенного: просто назначить материал
                    if mj and fm.CurrentType:
                        mid = fm.CurrentType.AsElementId(mj)
                        if mid and mid != ElementId.InvalidElementId:
                            mp.Set(mid); k += 1
                elif mj and (a is None or a.Definition.Name != u"Материал_жалюзи"):
                    fm.AssociateElementParameterToFamilyParameter(mp, mj); k += 1
        out["lamels_material_bound"] = k; out["lamel_material_params"] = list(info.keys())
        return out
    res["panel"].update(tx(pd, u"FT: стык цс — панель", edit_panel))
    if not args.get("panel_read_only"):
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        pth = os.path.join(OUT, args["panel_family"] + ".rfa"); pd.SaveAs(pth, so); res["panel"]["rfa"] = pth
finally:
    if pd is not None:
        pd.Close(False)


# ---------- 2) УП-008 ----------
def rect(d, x0, x1, y0, y1, view):
    pts = [XYZ(x0, y0, 0), XYZ(x1, y0, 0), XYZ(x1, y1, 0), XYZ(x0, y1, 0)]
    return [d.FamilyCreate.NewDetailCurve(view, Line.CreateBound(pts[i], pts[(i + 1) % 4])) for i in range(4)]


for u in args.get("up008", []):
    r = {"save_as": u["save_as"]}
    bd = doc.EditFamily(fams[args["up_base_profile"]])
    try:
        own = [ce for ce in FilteredElementCollector(bd).OfClass(CurveElement) if ce.GeometryCurve is not None]
        view = bd.GetElement(own[0].OwnerViewId)
        W = MM(float(args.get("up_width_mm", 2))) / 2; D = MM(float(args.get("up_depth_mm", 13))); O = MM(float(u["outer_mm"]))

        def mk():
            ids = [ce.Id for ce in own] + [fi.Id for fi in FilteredElementCollector(bd).OfClass(FamilyInstance)]
            bd.Delete(List[ElementId](ids))
            # полоска в габарите стекла: от наружной грани стекла (outer) внутрь на up_inset_mm, глубина up_depth_mm.
            # (до 11.11 было inset = -1, depth 13 — выходило за стекло 8 мм на 1 мм наружу и 4 мм внутрь)
            I = MM(float(args.get("up_inset_mm", 0.5)))
            rect(bd, -W, W, O - I - D, O - I, view)       # у стекла со стороны +y
            rect(bd, -W, W, -O + I, -O + I + D, view)     # у стекла со стороны -y
            return len(ids)
        r["deleted"] = tx(bd, u"FT: УП-008", mk)
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        pth = os.path.join(OUT, u["save_as"] + ".rfa"); bd.SaveAs(pth, so); r["rfa"] = pth
    except Exception as ex:
        r["error"] = str(ex)
    finally:
        bd.Close(False)
    res["up008"].append(r)


# ---------- 3) уплотнитель стекла в профилях края цс ----------
def seal_type(d):
    for ft in FilteredElementCollector(d).OfClass(FilledRegionType):
        if ft.Name == u"FT_Уплотнитель_стекла":
            return ft
    base = list(FilteredElementCollector(d).OfClass(FilledRegionType))[0]
    nt = base.Duplicate(u"FT_Уплотнитель_стекла")
    for fp in FilteredElementCollector(d).OfClass(FillPatternElement):
        p = fp.GetFillPattern()
        if p.IsSolidFill and p.Target == FillPatternTarget.Drafting:
            nt.ForegroundPatternId = fp.Id
    nt.ForegroundPatternColor = Color(0, 0, 0)
    return nt


for e in args.get("edges", []):
    r = {"profile": e["name"]}
    if not seal_loops:
        r["error"] = u"нет формы уплотнителя"; res["edges"].append(r); continue
    loops, gx = seal_loops
    ed = app.OpenDocumentFile(e["rfa"]) if e.get("rfa") else doc.EditFamily(fams[e["name"]]); nd = None   # rfa — копия, ещё не загруженная в проект
    try:
        own = [ce.GeometryCurve for ce in FilteredElementCollector(ed).OfClass(CurveElement) if ce.GeometryCurve is not None]
        nm_ = e.get("save_as") or e["name"]
        side = e.get("side") or ("min" if (u"Левый" in nm_ or u"Верхний" in nm_) else "max")   # "both" — стекло с двух сторон
        # лента (отдельный прямоугольник у стены) не мешает: берём крайнюю точку со стороны стекла
        xs = [q.X for c in own for q in (c.GetEndPoint(0), c.GetEndPoint(1))]
        fi = list(FilteredElementCollector(ed).OfClass(FamilyInstance))[0]
        inv = fi.GetTransform().Inverse
        fulls = []
        for sd in (["max", "min"] if side == "both" else [side]):
            xg = max(xs) if sd == "max" else min(xs)
            # панель: левый бок, стекло идёт в +x от gx. Правый профиль: стекло в +x от xg -> сдвиг; левый профиль: зеркало по x.
            if sd == "max":
                tr = Transform.CreateTranslation(XYZ(xg - gx, 0, 0))
            else:
                tr = Transform.CreateTranslation(XYZ(xg + gx, 0, 0)).Multiply(Transform.CreateReflection(Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero)))
            fulls.append(inv.Multiply(tr))
        nd = ed.EditFamily(fi.Symbol.Family)
        view = [v for v in FilteredElementCollector(nd).OfClass(View) if not v.IsTemplate and v.ViewType in (ViewType.FloorPlan, ViewType.DraftingView, ViewType.Detail, ViewType.EngineeringPlan)]
        view = view[0] if view else [v for v in FilteredElementCollector(nd).OfClass(View) if not v.IsTemplate][0]

        def mk():
            old = [x.Id for x in FilteredElementCollector(nd).OfClass(FilledRegion) if nd.GetElement(x.GetTypeId()).Name == u"FT_Уплотнитель_стекла"]
            if old:
                nd.Delete(List[ElementId](old))
            st = seal_type(nd); made = 0
            ysh = MM(float(e.get("y_shift_mm", 0)))   # 62 мм: стёкла на 5,1 мм ближе к оси, чем у 72 мм
            for full, lp in [(f_, l_) for f_ in fulls for l_ in loops]:
                cy = sum(c.GetEndPoint(0).Y for c in lp) / len(lp)
                sh = Transform.CreateTranslation(XYZ(0, -ysh if cy > 0 else ysh, 0))
                cl = CurveLoop()
                for c in lp:
                    cc = c.CreateTransformed(full.Multiply(sh))
                    a = cc.GetEndPoint(0); b = cc.GetEndPoint(1)
                    if isinstance(cc, Line):
                        cc = Line.CreateBound(XYZ(a.X, a.Y, 0), XYZ(b.X, b.Y, 0))
                    else:
                        m = cc.Evaluate(0.5, True); cc = Arc.Create(XYZ(a.X, a.Y, 0), XYZ(b.X, b.Y, 0), XYZ(m.X, m.Y, 0))
                    cl.Append(cc)
                ll = List[CurveLoop](); ll.Add(cl)
                FilledRegion.Create(nd, st.Id, view.Id, ll); made += 1
            return made
        r["seals"] = tx(nd, u"FT: уплотнитель стекла", mk)
        r["glass_edge_mm"] = round(xg * FT, 2); r["side"] = side
        class _LO2(IFamilyLoadOptions):
            def OnFamilyFound(self, a, b):
                b.Value = True; return True

            def OnSharedFamilyFound(self, a, b, src, c):
                src.Value = FamilySource.Family; c.Value = True; return True
        nd.LoadFamily(ed, _LO2()); nd.Close(False); nd = None
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        pth = os.path.join(OUT, (e.get("save_as") or e["name"]) + ".rfa"); ed.SaveAs(pth, so); r["rfa"] = pth
    except Exception as ex:
        r["error"] = str(ex)
    finally:
        if nd is not None:
            nd.Close(False)
        ed.Close(False)
    res["edges"].append(r)
bad = [x for x in res["up008"] + res["edges"] if x.get("error")]
__output__ = {"status": "completed_unverified" if not bad else "partial", "summary": u"панель, УП-008 %d, края %d, ошибок %d; копии в %s" % (len(res["up008"]), len(res["edges"]), len(bad), OUT), "result": res}
