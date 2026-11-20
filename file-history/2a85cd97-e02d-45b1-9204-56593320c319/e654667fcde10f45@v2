# -*- coding: utf-8 -*-
# Только чтение: факты для аудита «после» (М2/М3, без М1 и дверей) -> JSON.
# Типы импостов (профиль, ADSK, все FT_*), типы панелей витража (ADSK, FT_*, толщина), типы витражей (ADSK, назначенные
# импосты/панель), предупреждения, ADSK общие ли (GUID), семейства «...0001»/не BIMLIB, количество экземпляров.
# Аргументы: out_json
import json, io, re
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
ADSK = [u"ADSK_Наименование", u"ADSK_Код изделия", u"ADSK_Обозначение", u"ADSK_Завод-изготовитель", u"ADSK_Единица измерения", u"ADSK_Марка"]


def pv(p):
    if p is None:
        return None
    st = p.StorageType
    if st == StorageType.String:
        return p.AsString()
    if st == StorageType.Double:
        return round(p.AsDouble() * FT, 3) if p.Definition.GetDataType() == SpecTypeId.Length else round(p.AsDouble(), 6)
    if st == StorageType.Integer:
        return p.AsInteger()
    if st == StorageType.ElementId:
        e = doc.GetElement(p.AsElementId())
        return e.Name if e is not None else None
    return None


def params(el):
    out = {}
    for p in el.Parameters:
        n = p.Definition.Name
        if n.startswith(u"ADSK_") or n.startswith(u"FT_") or n.startswith(u"FT "):
            out[n] = pv(p)
    return out


def m23(name):
    return re.search(u"(^|[ _])М[23]([ _]|$)", name or u"") is not None or u"Система М2" in (name or u"") or u"Система М3" in (name or u"")


res = {"doc": doc.Title, "mullion_types": [], "panel_types": [], "wall_types": [], "shared": {}, "families_odd": []}
# предупреждения
ws = doc.GetWarnings()
res["warnings"] = [w.GetDescriptionText() for w in ws]
# экземпляры импостов по типу
cnt = {}
for m in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType():
    cnt[m.GetTypeId().Value] = cnt.get(m.GetTypeId().Value, 0) + 1
for mt in FilteredElementCollector(doc).OfClass(MullionType):
    n = mt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    s = doc.GetElement(mt.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
    prof = s.Family.Name if s is not None and hasattr(s, "Family") else None
    if not (m23(n) or (prof and (u"_М2_" in prof or u"_М3_" in prof))):
        continue
    res["mullion_types"].append({"id": int(mt.Id.Value), "name": n, "profile": prof, "n": cnt.get(mt.Id.Value, 0), "p": params(mt)})
# панели витража (типы семейств категории панелей)
pcnt = {}
for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
    pcnt[e.GetTypeId().Value] = pcnt.get(e.GetTypeId().Value, 0) + 1
for fs in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsElementType():
    fam = fs.FamilyName if hasattr(fs, "FamilyName") else u""
    n = fs.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() if fs.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM) else fs.Name
    res["panel_types"].append({"id": int(fs.Id.Value), "family": fam, "name": n, "n": pcnt.get(fs.Id.Value, 0), "p": params(fs)})
# витражи
wcnt = {}
for w in FilteredElementCollector(doc).OfClass(Wall):
    wcnt[w.GetTypeId().Value] = wcnt.get(w.GetTypeId().Value, 0) + 1
BIPS = {"interior1": BuiltInParameter.AUTO_MULLION_INTERIOR_GRID1, "interior2": BuiltInParameter.AUTO_MULLION_INTERIOR_GRID2,
        "border1_1": BuiltInParameter.AUTO_MULLION_BORDER1_GRID1, "border2_1": BuiltInParameter.AUTO_MULLION_BORDER2_GRID1,
        "border1_2": BuiltInParameter.AUTO_MULLION_BORDER1_GRID2, "border2_2": BuiltInParameter.AUTO_MULLION_BORDER2_GRID2,
        "panel": BuiltInParameter.AUTO_PANEL_WALL}
for wt in FilteredElementCollector(doc).OfClass(WallType):
    if wt.Kind != WallKind.Curtain or not m23(wt.Name):
        continue
    d = {"id": int(wt.Id.Value), "name": wt.Name, "n": wcnt.get(wt.Id.Value, 0), "p": params(wt)}
    for k, b in BIPS.items():
        p = wt.get_Parameter(b)
        d[k] = pv(p) if p else None
    res["wall_types"].append(d)
# ADSK общие?
seen = set()
for col in (res["mullion_types"][:1], res["panel_types"][:3], res["wall_types"][:1]):
    for it in col:
        el = doc.GetElement(ElementId(it["id"]))
        for p in el.Parameters:
            n = p.Definition.Name
            if n.startswith(u"ADSK_") and n not in seen:
                seen.add(n)
                res["shared"][n] = str(p.GUID) if p.IsShared else None
# семейства
for f in FilteredElementCollector(doc).OfClass(Family):
    n = f.Name
    if re.search(u"\\d{4}$", n) or (f.FamilyCategory and f.FamilyCategory.Id.Value in (int(BuiltInCategory.OST_CurtainWallPanels), int(BuiltInCategory.OST_ProfileFamilies)) and not n.startswith(u"BIMLIB_")):
        res["families_odd"].append([n, f.FamilyCategory.Name if f.FamilyCategory else None])
io.open(args["out_json"], "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
__output__ = {"status": "completed_unverified", "summary": u"%s: импостов М2/М3 %d типов, панелей %d, витражей %d, предупреждений %d" % (doc.Title, len(res["mullion_types"]), len(res["panel_types"]), len(res["wall_types"]), len(res["warnings"])),
              "warnings_sample": res["warnings"][:10], "shared": res["shared"], "families_odd": res["families_odd"][:30]}
