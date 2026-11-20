# -*- coding: utf-8 -*-
# Глухая панель ГКЛ 12,5 с утеплителем: копия семейства двухслойной панели.
#  - листы = «стекло» толщиной 12,5 (растут внутрь от лицевой плоскости), материал ГКЛ; уплотнители выключены;
#  - новое тело «утеплитель» между листами, от грани до грани импостов (выравнено по Слева/Справа/Верх/уровню);
#  - параметры: FT_Утеплитель_Показать (тип), Материал_утеплитель (тип), FT_Утеплитель_Полутолщина (формула), FT_Утеплитель_Площадь (экз.);
#  - типы: 62 мм (М2) и 72 мм (М3). Файл семейства сохраняется в out_dir.
# Затем (в проекте, в группе транзакций): загрузка, подбор захода листа в стойку по пересечению тел, откат при dry_run.
# Аргументы: src_family, out_dir, dry_run, types [{name, thk, vs, vt, vb}], probe_stands [{wall_type, mullion_type, type}], probe_range [a,b,step]
import json, os, clr, math
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if "args_file" in args:
    _d = args.get("dry_run")
    with open(args["args_file"], encoding="utf-8-sig") as _f:
        args = json.load(_f)
    if _d is not None:
        args["dry_run"] = _d
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MM = lambda v: v / FT
DRY = bool(args.get("dry_run", True))
NEW = u"BIMLIB_ПанельВитража_Глухая_ФристайлТехнолоджи"
res = {"family": {}, "probe": []}


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = True
        return True


def pattern(fd, name, angle_deg, sp_mm, cross=False):
    for fp in FilteredElementCollector(fd).OfClass(FillPatternElement):
        if fp.Name == name:
            return fp.Id
    if cross:
        p = FillPattern(name, FillPatternTarget.Drafting, FillPatternHostOrientation.ToView, math.radians(angle_deg), sp_mm / FT, sp_mm / FT)
    else:
        p = FillPattern(name, FillPatternTarget.Drafting, FillPatternHostOrientation.ToView, math.radians(angle_deg), sp_mm / FT)
    return FillPatternElement.Create(fd, p).Id


def mat(fd, name, rgb, pat=None):
    m = [x for x in FilteredElementCollector(fd).OfClass(Material) if x.Name == name]
    mm = m[0] if m else fd.GetElement(Material.Create(fd, name))
    mm.Color = Color(rgb[0], rgb[1], rgb[2])
    if pat is not None:
        mm.CutForegroundPatternId = pat
        mm.CutForegroundPatternColor = Color(0, 0, 0)
    return mm.Id


src = [f for f in FilteredElementCollector(doc).OfClass(Family) if f.Name == args["src_family"]][0]
fd = doc.EditFamily(src)
rfa = os.path.join(args["out_dir"], NEW + u".rfa")
try:
    fm = fd.FamilyManager
    P = dict((p.Definition.Name, p) for p in fm.Parameters)
    t = Transaction(fd, u"Глухая панель ГКЛ"); t.Start()
    m_gkl = mat(fd, u"ФТ_ГКЛ 12,5", (225, 225, 220), pattern(fd, u"ФТ_ГКЛ диагональ", 45, 1.5))
    m_ins = mat(fd, u"ФТ_Утеплитель минвата", (240, 220, 120), pattern(fd, u"ФТ_Утеплитель сетка", 45, 3.0, cross=True))

    def add(name, spec, inst, grp=GroupTypeId.Construction):
        if name in P:
            return P[name]
        p = fm.AddParameter(name, grp, spec, inst)
        P[name] = p
        return p
    p_show = add(u"FT_Утеплитель_Показать", SpecTypeId.Boolean.YesNo, False)
    p_mat = add(u"Материал_утеплитель", SpecTypeId.Reference.Material, False, GroupTypeId.Materials)
    p_half = add(u"FT_Утеплитель_Полутолщина", SpecTypeId.Length, False)
    p_area = add(u"FT_Утеплитель_Площадь", SpecTypeId.Area, True)
    # уплотнители и стекольные артикулы — выключить
    fm.SetFormula(P[u"FT_Уплотнитель_Показать"], u"1 < 0")
    fm.SetFormula(P[u"FT_Стекло_Уплотнитель_Артикул"], u'""')
    fm.SetFormula(P[u"FT_Стекло_Уплотнитель_Длина"], u"0 мм")
    # тело утеплителя
    rps = dict((rp.Name, rp) for rp in FilteredElementCollector(fd).OfClass(ReferencePlane))
    rpc = rps[u"По центру (Вперед/Вправо)"]
    sp = SketchPlane.Create(fd, rpc.Id)
    xl = rps[u"Слева"].BubbleEnd.X; xr = rps[u"Справа"].BubbleEnd.X
    zt = rps[u"Верх"].BubbleEnd.Z; zb = 0.0
    y0 = rpc.BubbleEnd.Y
    pts = [XYZ(xl, y0, zb), XYZ(xr, y0, zb), XYZ(xr, y0, zt), XYZ(xl, y0, zt)]
    ca = CurveArray()
    for i in range(4):
        ca.Append(Line.CreateBound(pts[i], pts[(i + 1) % 4]))
    caa = CurveArrArray(); caa.Append(ca)
    ex = fd.FamilyCreate.NewExtrusion(True, caa, sp, MM(20))
    fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM), None)
    fm.SetFormula(p_half, u"ADSK_Размер_Толщина / 2 - Толщина стекла")
    p_neg = add(u"FT_Утеплитель_Начало", SpecTypeId.Length, False)
    fm.SetFormula(p_neg, u"-FT_Утеплитель_Полутолщина")
    fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM), p_neg)
    fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.EXTRUSION_END_PARAM), p_half)
    fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM), p_show)
    fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM), p_mat)
    fd.Regenerate()
    # выравнивание эскиза по Слева/Справа/Верх/уровню (вид спереди)
    view = None
    for v in FilteredElementCollector(fd).OfClass(View):
        try:
            if not v.IsTemplate and v.ViewType == ViewType.Elevation and abs(abs(v.ViewDirection.Y) - 1) < 1e-6:
                view = v
                break
        except Exception:
            pass
    lvl = [l for l in FilteredElementCollector(fd).OfClass(Level)]
    aligned = []
    for arr in ex.Sketch.Profile:
        for c in arr:
            a, b = c.GetEndPoint(0), c.GetEndPoint(1)
            target = None
            if abs(a.X - b.X) < 1e-6:
                target = rps[u"Слева"].GetReference() if abs(a.X - xl) < 1e-6 else rps[u"Справа"].GetReference()
            elif abs(a.Z - zt) < 1e-6:
                target = rps[u"Верх"].GetReference()
            elif lvl:
                target = lvl[0].GetPlaneReference()
            if target is not None and view is not None:
                try:
                    fd.FamilyCreate.NewAlignment(view, target, c.Reference)
                    aligned.append(True)
                except Exception as e:
                    aligned.append(str(e)[:60])
    res["family"]["aligned"] = aligned
    # площадь утеплителя
    fm.SetFormula(p_area, u"if(FT_Утеплитель_Показать, ADSK_Размер_Ширина * ADSK_Размер_Высота, 0 м²)")
    # типы: создать новые, старые удалить
    old = list(fm.Types)
    made = []
    for ty in args["types"]:
        nt = fm.NewType(ty["name"])
        fm.CurrentType = nt
        fm.Set(P[u"ADSK_Размер_Толщина"], MM(ty["thk"]))
        fm.Set(P[u"Толщина стекла"], MM(12.5))
        fm.Set(P[u"Выступ сбоку"], MM(ty["vs"]))
        fm.Set(P[u"Выступ сверху"], MM(ty["vt"]))
        fm.Set(P[u"Выступ снизу"], MM(ty["vb"]))
        fm.Set(P[u"FT_Система_М1"], 0)
        fm.Set(p_show, 1)
        fm.Set(P[u"Материал_остекление"], m_gkl)
        fm.Set(p_mat, m_ins)
        if u"FT_Стекло_Уплотнитель_Линий" in P:
            fm.Set(P[u"FT_Стекло_Уплотнитель_Линий"], 0.0)
        if u"FT_Стекло_Добавка" in P:
            fm.Set(P[u"FT_Стекло_Добавка"], MM(ty["vs"] - 1.5))
        for pn, val in ((u"ADSK_Наименование", ty.get("adsk_name")), (u"Описание", ty.get("descr"))):
            if val and pn in P and P[pn].StorageType == StorageType.String and not P[pn].Formula:
                fm.Set(P[pn], val)
        made.append(ty["name"])
    for ot in old:
        fm.CurrentType = ot
        fm.DeleteCurrentType()
    t.Commit()
    if not os.path.isdir(args["out_dir"]):
        os.makedirs(args["out_dir"])
    so = SaveAsOptions(); so.OverwriteExistingFile = True
    fd.SaveAs(rfa, so)
    res["family"].update(rfa=rfa, types=made, view=view.Name if view else None)
finally:
    fd.Close(False)

# --- проект: загрузка и подбор захода листа ---
level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
wtypes = dict((w.Name, w) for w in FilteredElementCollector(doc).OfClass(WallType))
mtypes = dict((m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), m) for m in FilteredElementCollector(doc).OfClass(MullionType))


def solids(el):
    out = []

    def wk(ge, tr):
        for g in ge:
            if isinstance(g, Solid) and g.Volume > 1e-9:
                out.append(SolidUtils.CreateTransformed(g, tr) if tr else g)
            elif isinstance(g, GeometryInstance):
                wk(g.GetSymbolGeometry(), tr.Multiply(g.Transform) if tr else g.Transform)
    o = Options(); o.DetailLevel = ViewDetailLevel.Fine
    wk(el.get_Geometry(o), None)
    return out


tg = TransactionGroup(doc, u"Глухая панель ГКЛ"); tg.Start()
try:
    t = Transaction(doc, u"Загрузка глухой панели"); t.Start()
    res["loaded"] = bool(doc.LoadFamily(rfa, LoadOpt(), clr.Reference[Family]()))
    t.Commit()
    syms = dict((s.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), s) for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels) if s.FamilyName == NEW)
    res["types_in_project"] = sorted(syms.keys())
    a, b, st = args.get("probe_range", [10, 24, 1])
    for k, pr in enumerate(args.get("probe_stands", [])):
        checkpoint(pr["mullion_type"][:40], k, len(args["probe_stands"]))
        r = {"stand": pr["mullion_type"], "ok_max_mm": None, "vol": []}
        t = Transaction(doc, u"проба"); t.Start()
        Pt = XYZ(MM(20000 + 3000 * k), MM(330000), level.Elevation)
        w = Wall.Create(doc, Line.CreateBound(Pt - XYZ(MM(600), 0, 0), Pt + XYZ(MM(600), 0, 0)), wtypes[pr["wall_type"]].Id, level.Id, MM(2700), 0, False, False)
        doc.Regenerate()
        w.CurtainGrid.AddGridLine(False, Pt + XYZ(0, 0, 1), False); doc.Regenerate()
        m = None
        for mid in w.CurtainGrid.GetMullionIds():
            mm_ = doc.GetElement(mid); bb = mm_.get_BoundingBox(None)
            if bb and (bb.Max.Z - bb.Min.Z) > 1 and abs((bb.Min.X + bb.Max.X) / 2 - Pt.X) < MM(60):
                m = mm_
        m.ChangeTypeId(mtypes[pr["mullion_type"]].Id)
        sym = syms[pr["type"]]
        if not sym.IsActive:
            sym.Activate()
        for pid in w.CurtainGrid.GetPanelIds():
            p = doc.GetElement(pid); p.Pinned = False; p.ChangeTypeId(sym.Id)
        doc.Regenerate()
        cs = solids(m)
        vs_p = sym.LookupParameter(u"Выступ сбоку")
        v = a
        while v <= b + 1e-9:
            vs_p.Set(MM(v)); doc.Regenerate()
            tot = 0.0
            for pid in w.CurtainGrid.GetPanelIds():
                for ps in solids(doc.GetElement(pid)):
                    for c in cs:
                        try:
                            x = BooleanOperationsUtils.ExecuteBooleanOperation(c, ps, BooleanOperationsType.Intersect)
                            if x:
                                tot += x.Volume
                        except Exception:
                            pass
            vol = round(tot * FT ** 3 / 2700.0, 0)
            r["vol"].append([v, vol])
            if vol < 500:
                r["ok_max_mm"] = v
            v += st
        t.RollBack()
        res["probe"].append(r)
    res["warnings"] = len(doc.GetWarnings())
finally:
    if DRY:
        tg.RollBack()
    else:
        tg.Assimilate()
res["dry_run"] = DRY
res["status"] = "completed_unverified"
res["summary"] = u"%sсемейство %s, типов %d, проб %d" % (u"ПРОБНЫЙ ПРОГОН (откат): " if DRY else u"", res.get("loaded"), len(res.get("types_in_project", [])), len(res["probe"]))
__output__ = res
