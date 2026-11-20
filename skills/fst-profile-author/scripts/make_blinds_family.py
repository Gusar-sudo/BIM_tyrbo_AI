# -*- coding: utf-8 -*-
# Межрамные жалюзи в семействе двухслойной стеклянной панели (схематично):
#  - FT_Жалюзи (экземпляр, да/нет); FT_Жалюзи_Видимость = and(FT_Жалюзи, FT_Стекло_Добавка > 0 мм) — у цельностеклянных (добавка < 0) не включаются;
#  - пакет ламелей: тело толщиной FT_Жалюзи_Толщина (25 мм) по центру между стёклами, от Слева до Справа, от уровня до низа карниза;
#  - карниз: тело FT_Жалюзи_Карниз_Толщина (30 мм) высотой FT_Жалюзи_Карниз (40 мм) под «Верх»;
#  - спецификация: FT_Жалюзи_Площадь, FT_Жалюзи_Ручка_Артикул (FS.C-Rg), FT_Жалюзи_Ручка_Расход (1 шт).
# Семейство сохраняется копией в out_dir (проект не меняется). Аргументы: family, out_dir
import json, os, math
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MM = lambda v: v / FT
res = {}
src = [f for f in FilteredElementCollector(doc).OfClass(Family) if f.Name == args["family"]][0]
fd = doc.EditFamily(src)
try:
    fm = fd.FamilyManager
    P = dict((p.Definition.Name, p) for p in fm.Parameters)
    t = Transaction(fd, u"Жалюзи"); t.Start()

    def add(name, spec, inst, grp=GroupTypeId.Construction):
        if name in P:
            return P[name]
        p = fm.AddParameter(name, grp, spec, inst)
        P[name] = p
        return p

    def mat(name, rgb, transp=0):
        m = [x for x in FilteredElementCollector(fd).OfClass(Material) if x.Name == name]
        mm = m[0] if m else fd.GetElement(Material.Create(fd, name))
        mm.Color = Color(rgb[0], rgb[1], rgb[2]); mm.Transparency = transp
        return mm.Id
    p_on = add(u"FT_Жалюзи", SpecTypeId.Boolean.YesNo, True)
    p_vis = add(u"FT_Жалюзи_Видимость", SpecTypeId.Boolean.YesNo, True)
    p_t = add(u"FT_Жалюзи_Толщина", SpecTypeId.Length, False)
    p_h = add(u"FT_Жалюзи_Полутолщина", SpecTypeId.Length, False)
    p_hn = add(u"FT_Жалюзи_Начало", SpecTypeId.Length, False)
    p_kt = add(u"FT_Жалюзи_Карниз_Толщина", SpecTypeId.Length, False)
    p_kh = add(u"FT_Жалюзи_Карниз_Полутолщина", SpecTypeId.Length, False)
    p_kn = add(u"FT_Жалюзи_Карниз_Начало", SpecTypeId.Length, False)
    p_kz = add(u"FT_Жалюзи_Карниз", SpecTypeId.Length, False)
    p_ml = add(u"Материал_жалюзи", SpecTypeId.Reference.Material, False, GroupTypeId.Materials)
    p_mk = add(u"Материал_жалюзи_карниз", SpecTypeId.Reference.Material, False, GroupTypeId.Materials)
    p_ar = add(u"FT_Жалюзи_Площадь", SpecTypeId.Area, True, GroupTypeId.Data)
    p_ra = add(u"FT_Жалюзи_Ручка_Артикул", SpecTypeId.String.Text, True, GroupTypeId.Data)
    p_rr = add(u"FT_Жалюзи_Ручка_Расход", SpecTypeId.Number, True, GroupTypeId.Data)
    fm.SetFormula(p_t, u"25 мм"); fm.SetFormula(p_h, u"FT_Жалюзи_Толщина / 2"); fm.SetFormula(p_hn, u"-FT_Жалюзи_Полутолщина")
    fm.SetFormula(p_kt, u"30 мм"); fm.SetFormula(p_kh, u"FT_Жалюзи_Карниз_Толщина / 2"); fm.SetFormula(p_kn, u"-FT_Жалюзи_Карниз_Полутолщина")
    fm.SetFormula(p_kz, u"40 мм")
    fm.SetFormula(p_vis, u"and(FT_Жалюзи, FT_Стекло_Добавка > 0 мм)")
    fm.SetFormula(p_ar, u"if(FT_Жалюзи_Видимость, ADSK_Размер_Ширина * ADSK_Размер_Высота, 0 м²)")
    fm.SetFormula(p_ra, u'if(FT_Жалюзи_Видимость, "FS.C-Rg", "")')
    fm.SetFormula(p_rr, u"if(FT_Жалюзи_Видимость, 1, 0)")
    m_l = mat(u"ФТ_Жалюзи ламели", (205, 205, 210), 30); m_k = mat(u"ФТ_Жалюзи карниз", (140, 140, 145))
    for ty in fm.Types:
        fm.CurrentType = ty
        fm.Set(p_ml, m_l); fm.Set(p_mk, m_k)
    fd.Regenerate()
    rps = dict((rp.Name, rp) for rp in FilteredElementCollector(fd).OfClass(ReferencePlane))
    rpc = rps[u"По центру (Вперед/Вправо)"]
    xl = rps[u"Слева"].BubbleEnd.X; xr = rps[u"Справа"].BubbleEnd.X; zt = rps[u"Верх"].BubbleEnd.Z
    y0 = rpc.BubbleEnd.Y
    view = None
    for v in FilteredElementCollector(fd).OfClass(View):
        try:
            if not v.IsTemplate and v.ViewType == ViewType.Elevation and abs(abs(v.ViewDirection.Y) - 1) < 1e-6:
                view = v; break
        except Exception:
            pass
    # опорная плоскость «Жалюзи_Карниз» = Верх - FT_Жалюзи_Карниз
    zk = zt - MM(40)
    rk = fd.FamilyCreate.NewReferencePlane(XYZ(xl - MM(200), y0, zk), XYZ(xr + MM(200), y0, zk), XYZ(0, 1, 0), view)
    rk.Name = u"Жалюзи_Карниз"
    fd.Regenerate()
    ra = ReferenceArray(); ra.Append(rps[u"Верх"].GetReference()); ra.Append(rk.GetReference())
    dim = fd.FamilyCreate.NewDimension(view, Line.CreateBound(XYZ(xl - MM(100), y0, zk), XYZ(xl - MM(100), y0, zt)), ra)
    dim.FamilyLabel = p_kz
    fd.Regenerate()
    lvl = [l for l in FilteredElementCollector(fd).OfClass(Level)]
    sp = SketchPlane.Create(fd, rpc.Id)

    def box(zb_, zt_, bottom_ref, top_ref, start_p, end_p, mat_p):
        pts = [XYZ(xl, y0, zb_), XYZ(xr, y0, zb_), XYZ(xr, y0, zt_), XYZ(xl, y0, zt_)]
        ca = CurveArray()
        for i in range(4):
            ca.Append(Line.CreateBound(pts[i], pts[(i + 1) % 4]))
        caa = CurveArrArray(); caa.Append(ca)
        ex = fd.FamilyCreate.NewExtrusion(True, caa, sp, MM(10))
        fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM), start_p)
        fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.EXTRUSION_END_PARAM), end_p)
        fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM), p_vis)
        fm.AssociateElementParameterToFamilyParameter(ex.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM), mat_p)
        fd.Regenerate()
        al = []
        for arr in ex.Sketch.Profile:
            for c in arr:
                a, b = c.GetEndPoint(0), c.GetEndPoint(1)
                if abs(a.X - b.X) < 1e-6:
                    tg = rps[u"Слева"].GetReference() if abs(a.X - xl) < 1e-6 else rps[u"Справа"].GetReference()
                elif abs(a.Z - zt_) < 1e-6:
                    tg = top_ref
                else:
                    tg = bottom_ref
                try:
                    fd.FamilyCreate.NewAlignment(view, tg, c.Reference); al.append(True)
                except Exception as e:
                    al.append(str(e)[:60])
        return ex, al
    e1, a1 = box(0.0, zk, lvl[0].GetPlaneReference(), rk.GetReference(), p_hn, p_h, p_ml)
    e2, a2 = box(zk, zt, rk.GetReference(), rps[u"Верх"].GetReference(), p_kn, p_kh, p_mk)
    res["aligned"] = [a1, a2]
    # галочка по умолчанию выключена (иначе при загрузке в проект включится у всех панелей)
    for ty in fm.Types:
        fm.CurrentType = ty
        fm.Set(p_on, 0)
    # отдельные ламели («Высокая») добавляет второй шаг: make_blinds_lamels.py с mode=array
    t.Commit()
    # проверка гибкости: высота/ширина панели при смене типоразмера (параметры шаблона панели — только в проекте), здесь — что тело живое
    res["types"] = [ty.Name for ty in fm.Types]
    if not os.path.isdir(args["out_dir"]):
        os.makedirs(args["out_dir"])
    so = SaveAsOptions(); so.OverwriteExistingFile = True
    rfa = os.path.join(args["out_dir"], fd.Title.replace(u".rfa", u"") + u".rfa")
    fd.SaveAs(rfa, so)
    res["rfa"] = rfa
finally:
    try:
        fd.Close(False)
    except Exception:
        pass
ok = all(x is True for x in res.get("aligned", [[False]])[0] + res.get("aligned", [[], [False]])[1])
__output__ = {"status": "completed_unverified" if ok else "partial", "summary": u"семейство сохранено копией; выравниваний %s" % res.get("aligned"), "result": res}
