# -*- coding: utf-8 -*-
# Чтение: требования заполнения (fst-requirements F1.6, F3.5, F3.6) в документе:
# F1.6 — ADSK_Наименование/единица панелей М2/М3: стекло «Стекло N мм» (N = Толщина стекла), «м2»; ГКЛ — «Панель глухая ГКЛ 12,5 мм с утеплителем»;
# F3.5 — типы стен «…Глухое заполнение ГКЛ…»: панель ГКЛ, все автоимпосты «… глухой ГКЛ»; размещённые панели ГКЛ: FT_ГКЛ_Больше_листа = нет;
#        стены ГКЛ: все импосты на стенах — ГКЛ;
# F3.6 — панели нулевого размера (INFO). Аргументы: document_title (необязательно; иначе активный).
import json
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
if a.get("document_title"):
    doc = [d for d in app.Documents if d.Title == a["document_title"]][0]
FT = 304.8
res = {"doc": doc.Title, "F1_6_bad": [], "F3_5_types_bad": [], "F3_5_panels_big": [], "F3_5_wall_mullions_bad": [], "F3_6_zero_panels": 0, "counts": {}}
GKL_NAME = u"Панель глухая ГКЛ 12,5 мм с утеплителем"
n_glass = n_gkl = 0
for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsElementType():
    fam = getattr(s, "FamilyName", "")
    if not fam.startswith(u"BIMLIB_ПанельВитража_"):
        continue
    tn = s.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    if u"(М1)" in tn:
        continue
    nm = (s.LookupParameter(u"ADSK_Наименование").AsString() or u"") if s.LookupParameter(u"ADSK_Наименование") else u""
    un = (s.LookupParameter(u"ADSK_Единица измерения").AsString() or u"") if s.LookupParameter(u"ADSK_Единица измерения") else u""
    if u"Глухая" in fam:
        n_gkl += 1; exp = GKL_NAME
    else:
        n_glass += 1
        th = s.LookupParameter(u"Толщина стекла")
        exp = u"Стекло %g мм" % round(th.AsDouble() * FT, 1) if th else u"?"
    if nm != exp or un != u"м2":
        res["F1_6_bad"].append([tn, nm, un, exp])
res["counts"]["panel_types_glass"] = n_glass; res["counts"]["panel_types_gkl"] = n_gkl
P = [BuiltInParameter.AUTO_MULLION_BORDER1_HORIZ, BuiltInParameter.AUTO_MULLION_BORDER2_HORIZ, BuiltInParameter.AUTO_MULLION_INTERIOR_HORIZ,
     BuiltInParameter.AUTO_MULLION_BORDER1_VERT, BuiltInParameter.AUTO_MULLION_BORDER2_VERT, BuiltInParameter.AUTO_MULLION_INTERIOR_VERT]
gkl_wt = 0
for w in FilteredElementCollector(doc).OfClass(WallType):
    if u"Глухое заполнение ГКЛ" not in w.Name:
        continue
    gkl_wt += 1
    pan = doc.GetElement(w.get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).AsElementId())
    if pan is None or u"ГКЛ" not in pan.Name:
        res["F3_5_types_bad"].append([w.Name[-50:], u"панель", pan.Name if pan else None])
    for bp in P:
        m = doc.GetElement(w.get_Parameter(bp).AsElementId())
        if m is None or u"глухой ГКЛ" not in m.Name:
            res["F3_5_types_bad"].append([w.Name[-50:], str(bp)[14:], m.Name if m else None])
res["counts"]["gkl_wall_types"] = gkl_wt
n_pan = n_zero = n_gkl_inst = 0
for p in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
    pw = p.get_Parameter(BuiltInParameter.CURTAIN_WALL_PANELS_WIDTH)
    if pw is not None and pw.AsDouble() <= 0:
        n_zero += 1; continue
    b = p.LookupParameter(u"FT_ГКЛ_Больше_листа")
    if b is not None:
        n_gkl_inst += 1
        if b.AsInteger() == 1:
            res["F3_5_panels_big"].append(p.Id.Value)
res["F3_6_zero_panels"] = n_zero; res["counts"]["gkl_panels_placed"] = n_gkl_inst
n_gw = 0
for w in FilteredElementCollector(doc).OfClass(Wall):
    if u"Глухое заполнение ГКЛ" not in w.Name or w.CurtainGrid is None:
        continue
    n_gw += 1
    for mid in w.CurtainGrid.GetMullionIds():
        n = doc.GetElement(mid).Name
        if u"ГКЛ" not in n:
            res["F3_5_wall_mullions_bad"].append([w.Id.Value, n])
res["counts"]["gkl_walls_placed"] = n_gw
bad = len(res["F1_6_bad"]) + len(res["F3_5_types_bad"]) + len(res["F3_5_wall_mullions_bad"])
res["status"] = "completed_unverified"
res["summary"] = u"%s: F1.6 ошибок %d (стекло %d, ГКЛ %d типов); F3.5 типов стен ГКЛ %d, ошибок %d, панелей ГКЛ %d, больше листа %d, стен ГКЛ %d; нулевых панелей %d" % (
    doc.Title[:20], len(res["F1_6_bad"]), n_glass, n_gkl, gkl_wt, len(res["F3_5_types_bad"]) + len(res["F3_5_wall_mullions_bad"]),
    n_gkl_inst, len(res["F3_5_panels_big"]), n_gw, n_zero)
for k in ("F1_6_bad", "F3_5_types_bad", "F3_5_wall_mullions_bad", "F3_5_panels_big"):
    res[k] = res[k][:15]
__output__ = res
