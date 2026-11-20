# -*- coding: utf-8 -*-
# Только чтение: (1) все импосты витражей (тип, длина мм, все FT_*_Артикул/_Расход типа) -> mullions.csv;
# (2) ячейки тела спецификации (по имени) -> schedule_cells.csv (как показано в Revit).
# Аргументы: out_dir, schedule_name, only_m23 (true)
import json, io, os, re, csv
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
OUT = args["out_dir"]
rows = []; keys = set()
for m in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType():
    t = doc.GetElement(m.GetTypeId())
    n = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() if t else u""
    if args.get("only_m23", True) and not re.match(u"М[23] ", n or u""):
        continue
    lp = m.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)
    L = lp.AsDouble() * FT if lp else (m.LocationCurve.Curve.Length * FT if m.LocationCurve else 0)
    r = {"id": str(m.Id.Value), "type": n, "length_mm": "%.1f" % L}
    for p in t.Parameters:
        k = p.Definition.Name
        if k.startswith(u"FT_") and (k.endswith(u"_Артикул") or k.endswith(u"_Расход")):
            r[k] = (p.AsString() or u"") if p.StorageType == StorageType.String else ("%.4f" % p.AsDouble() if p.StorageType == StorageType.Double else str(p.AsInteger()))
            keys.add(k)
    rows.append(r)
cols = ["id", "type", "length_mm"] + sorted(keys)
with io.open(os.path.join(OUT, "mullions.csv"), "w", encoding="utf-8-sig", newline="") as f:
    f.write(u";".join(cols) + u"\n")
    for r in rows:
        f.write(u";".join((r.get(c) or u"").replace(u";", u",") for c in cols) + u"\n")
sch = [v for v in FilteredElementCollector(doc).OfClass(ViewSchedule) if v.Name == args["schedule_name"]][0]
td = sch.GetTableData(); body = td.GetSectionData(SectionType.Body); head = td.GetSectionData(SectionType.Header)
nr, nc = body.NumberOfRows, body.NumberOfColumns
with io.open(os.path.join(OUT, "schedule_cells.csv"), "w", encoding="utf-8-sig", newline="") as f:
    for i in range(nr):
        f.write(u";".join((sch.GetCellText(SectionType.Body, i, j) or u"").replace(u";", u",") for j in range(nc)) + u"\n")
__output__ = {"status": "completed_unverified", "summary": u"импостов М2/М3: %d; ячеек спецификации: %d×%d" % (len(rows), nr, nc), "cols": cols}
