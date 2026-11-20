# -*- coding: utf-8 -*-
# Ламели жалюзи ВЛОЖЕННЫМ семейством (замена массива выдавливаний, который в проекте не слушает видимость и длину):
#  1) семейство «BIMLIB_ЭлементыУзлов_Жалюзи_Ламель_ФристайлТехнолоджи» (типовая модель): одна наклонная ламель вдоль X,
#     длина = экземплярный «Длина», материал = экземплярный «Материал», видна только на «Высокой»;
#  2) панель (src_rfa = копия с пакетом и карнизом, make_blinds_family.py): пакет — только «Низкая/Средняя»; экземпляр ламели
#     у «Слева» (выравнивание), Длина = FT_Жалюзи_Длина (= ADSK_Размер_Ширина), Материал = Материал_жалюзи,
#     видимость = FT_Жалюзи_Видимость; линейный массив по высоте, количество = FT_Жалюзи_Ламелей.
# Сохраняет nested_rfa и out_rfa. Проект не меняется.
# Аргументы: template, src_rfa, nested_rfa, out_rfa, lamel_w_mm 25, lamel_t_mm 1, lamel_angle_deg 30, lamel_step_mm 22
import json, os, math
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
FT = 304.8
MM = lambda v: v / FT
LW = float(args.get("lamel_w_mm", 25)); LT = float(args.get("lamel_t_mm", 1.0))
ANG = math.radians(float(args.get("lamel_angle_deg", 30))); ST = float(args.get("lamel_step_mm", 22))
res = {}


def rollback(t):
    if t is not None and t.HasStarted() and not t.HasEnded():
        t.RollBack()


# ---------- 1. семейство ламели
nd = app.NewFamilyDocument(args["template"])
t = None
try:
    nfm = nd.FamilyManager
    t = Transaction(nd, u"Ламель"); t.Start()
    if nfm.CurrentType is None:
        nfm.NewType(u"Ламель")
    p_len = nfm.AddParameter(u"Длина", GroupTypeId.Geometry, SpecTypeId.Length, True)
    p_mat = nfm.AddParameter(u"Материал", GroupTypeId.Materials, SpecTypeId.Reference.Material, True)
    nfm.Set(p_len, MM(1000))
    rpx = [r for r in FilteredElementCollector(nd).OfClass(ReferencePlane) if abs(abs(r.Normal.X) - 1) < 1e-6][0]
    sp = SketchPlane.Create(nd, rpx.Id)
    x0 = rpx.BubbleEnd.X
    cs, sn = math.cos(ANG), math.sin(ANG)
    hy, hz = MM(LW / 2) * cs, MM(LW / 2) * sn
    ty, tz = -MM(LT / 2) * sn, MM(LT / 2) * cs
    pts = [XYZ(x0, -hy + ty, -hz + tz), XYZ(x0, hy + ty, hz + tz), XYZ(x0, hy - ty, hz - tz), XYZ(x0, -hy - ty, -hz - tz)]
    ca = CurveArray()
    for j in range(4):
        ca.Append(Line.CreateBound(pts[j], pts[(j + 1) % 4]))
    caa = CurveArrArray(); caa.Append(ca)
    # ламель симметрично от центра: от −Длина/2 до +Длина/2 (экземпляр в панели стоит по центру, без выравниваний —
    # иначе при смене ширины первая копия массива сдвигается, а остальные нет, и массив перекашивается)
    p_half = nfm.AddParameter(u"Полудлина", GroupTypeId.Geometry, SpecTypeId.Length, True)
    p_neg = nfm.AddParameter(u"Начало", GroupTypeId.Geometry, SpecTypeId.Length, True)
    nfm.SetFormula(p_half, u"Длина / 2"); nfm.SetFormula(p_neg, u"-Полудлина")
    ex = nd.FamilyCreate.NewExtrusion(True, caa, sp, MM(500))
    ex.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM).Set(-MM(500))
    nd.Regenerate()
    res["nested_dir"] = 0
    nfm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM), p_neg)
    nfm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.EXTRUSION_END_PARAM), p_half)
    nfm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM), p_mat)
    fv = FamilyElementVisibility(FamilyElementVisibilityType.Model)
    fv.IsShownInCoarse = False; fv.IsShownInMedium = False
    ex.SetVisibility(fv)
    t.Commit(); t = None
    # проверка гибкости длины
    t = Transaction(nd, u"flex"); t.Start()
    flex = []
    for L in (500, 1000, 3000):
        nfm.Set(p_len, MM(L)); nd.Regenerate()
        b2 = ex.get_BoundingBox(None); flex.append([L, round(b2.Min.X * FT, 1), round(b2.Max.X * FT, 1)])
    t.RollBack(); t = None
    res["nested_flex"] = flex
    so = SaveAsOptions(); so.OverwriteExistingFile = True
    nd.SaveAs(args["nested_rfa"], so)
finally:
    rollback(t)
    nd.Close(False)

# ---------- 2. панель
fd = app.OpenDocumentFile(args["src_rfa"])
t = None
try:
    fm = fd.FamilyManager
    P = dict((p.Definition.Name, p) for p in fm.Parameters)
    p_vis = P[u"FT_Жалюзи_Видимость"]; p_ml = P[u"Материал_жалюзи"]
    rps = dict((rp.Name, rp) for rp in FilteredElementCollector(fd).OfClass(ReferencePlane))
    xl = rps[u"Слева"].BubbleEnd.X; y0 = rps[u"По центру (Вперед/Вправо)"].BubbleEnd.Y
    view = [v for v in FilteredElementCollector(fd).OfClass(View) if not v.IsTemplate and v.ViewType == ViewType.Elevation and abs(abs(v.ViewDirection.Y) - 1) < 1e-6][0]
    lvl = list(FilteredElementCollector(fd).OfClass(Level))[0]
    fam = clr_ref = None
    import clr
    fr = clr.Reference[Family]()
    t = Transaction(fd, u"Загрузка ламели"); t.Start()
    ok = fd.LoadFamily(args["nested_rfa"], fr)
    t.Commit(); t = None
    nfam = fr.Value if ok else [f for f in FilteredElementCollector(fd).OfClass(Family) if f.Name == os.path.splitext(os.path.basename(args["nested_rfa"]))[0]][0]
    sym = fd.GetElement(list(nfam.GetFamilySymbolIds())[0])
    t = Transaction(fd, u"Ламели вложенным семейством"); t.Start()
    # пакет — не на «Высокой»
    pack = []
    for ex in FilteredElementCollector(fd).OfClass(Extrusion):
        pv = fm.GetAssociatedFamilyParameter(ex.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM))
        pm = fm.GetAssociatedFamilyParameter(ex.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM))
        if pv and pm and pv.Id == p_vis.Id and pm.Id == p_ml.Id:
            v_ = FamilyElementVisibility(FamilyElementVisibilityType.Model); v_.IsShownInFine = False
            ex.SetVisibility(v_); pack.append(ex.Id.Value)
    res["pack"] = pack
    if not sym.IsActive:
        sym.Activate()
    p_len = P.get(u"FT_Жалюзи_Длина") or fm.AddParameter(u"FT_Жалюзи_Длина", GroupTypeId.Construction, SpecTypeId.Length, True)
    fm.SetFormula(p_len, u"ADSK_Размер_Ширина")
    p_st = P.get(u"FT_Жалюзи_Шаг") or fm.AddParameter(u"FT_Жалюзи_Шаг", GroupTypeId.Construction, SpecTypeId.Length, False)
    fm.SetFormula(p_st, u"%g мм" % ST)
    p_n = P.get(u"FT_Жалюзи_Ламелей") or fm.AddParameter(u"FT_Жалюзи_Ламелей", GroupTypeId.Construction, SpecTypeId.Int.Integer, True)
    fm.SetFormula(p_n, u"if(ADSK_Размер_Высота - FT_Жалюзи_Карниз < 2 * FT_Жалюзи_Шаг, 2, rounddown((ADSK_Размер_Высота - FT_Жалюзи_Карниз) / FT_Жалюзи_Шаг))")
    fd.Regenerate()
    xc = (rps[u"Слева"].BubbleEnd.X + rps[u"Справа"].BubbleEnd.X) / 2
    fi = fd.FamilyCreate.NewFamilyInstance(XYZ(xc, y0, MM(ST / 2)), sym, lvl, StructuralType.NonStructural)
    fd.Regenerate()
    # z экземпляра: смещение от уровня
    off = fi.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM) or fi.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM)
    if off and not off.IsReadOnly:
        off.Set(MM(ST / 2))
    fm.AssociateElementParameterToFamilyParameter(fi.LookupParameter(u"Длина"), p_len)
    fm.AssociateElementParameterToFamilyParameter(fi.LookupParameter(u"Материал"), p_ml)
    fm.AssociateElementParameterToFamilyParameter(fi.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM), p_vis)
    fd.Regenerate()
    res["aligned"] = [True]   # без выравниваний: центр панели неподвижен (Слева/Справа симметричны)
    res["center_x"] = round(xc * FT, 2)
    fd.Regenerate()
    n0 = fm.CurrentType.AsInteger(p_n) or 2
    ids = List[ElementId](); ids.Add(fi.Id)
    la = LinearArray.Create(fd, view, ids, max(2, n0), XYZ(0, 0, MM(ST)), ArrayAnchorMember.Second)
    fd.Regenerate()
    la.Label = p_n
    fd.Regenerate()
    bbi = fi.get_BoundingBox(None)
    res["first"] = [round(bbi.Min.X * FT, 1), round(bbi.Max.X * FT, 1), round(bbi.Min.Z * FT, 1), round(bbi.Max.Z * FT, 1)] if bbi else None
    res["array_n"] = fm.CurrentType.AsInteger(p_n)
    t.Commit(); t = None
    so = SaveAsOptions(); so.OverwriteExistingFile = True
    fd.SaveAs(args["out_rfa"], so)
    res["rfa"] = args["out_rfa"]
finally:
    rollback(t)
    fd.Close(False)
ok_ = res.get("aligned") == [True] and res.get("first") is not None
__output__ = {"status": "completed_unverified" if ok_ else "partial", "summary": u"ламель: %s; панель: выравнивание %s, массив %s, первая %s" % (res.get("nested_flex"), res.get("aligned"), res.get("array_n"), res.get("first")), "result": res}
