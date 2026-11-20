# -*- coding: utf-8 -*-
# Чтение модели -> файл правок для set_type_params.py: ADSK_Наименование «Стекло N мм» у стеклянных панелей М2/М3
# (N = «Толщина стекла»), пустая ADSK_Единица измерения -> «м2». Глухие (ГКЛ) и типы с «(М1)» пропускаются.
# Аргументы: out_file
import json, io
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
writes, skipped = [], []
for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsElementType():
    fam = getattr(s, "FamilyName", "")
    name = s.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    if not fam.startswith("BIMLIB_ПанельВитража_"):
        continue
    if u"Глухая" in fam or u"(М1)" in name:
        skipped.append(name); continue
    th = s.LookupParameter(u"Толщина стекла")
    mm = round(th.AsDouble() * 304.8, 1)
    key = u"P:%s:%s" % (fam, name)
    writes.append({"key": key, "param": u"ADSK_Наименование", "value": u"Стекло %g мм" % mm})
    u = s.LookupParameter(u"ADSK_Единица измерения")
    if u is not None and not (u.AsString() or ""):
        writes.append({"key": key, "param": u"ADSK_Единица измерения", "value": u"м2"})
io.open(a["out_file"], "w", encoding="utf-8").write(json.dumps(
    {"transaction_name": u"FT: наименование стекла панелей", "writes": writes}, ensure_ascii=False, indent=1))
__output__ = {"status": "completed_unverified", "summary": u"правок %d (типов %d), пропущено %d" % (
    len(writes), len([w for w in writes if w["param"] == u"ADSK_Наименование"]), len(skipped)), "skipped": skipped}
