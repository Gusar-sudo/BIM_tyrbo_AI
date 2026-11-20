# -*- coding: utf-8 -*-
# Чтение: куски ГКЛ всех панелей ГКЛ проекта -> CSV для раскроя (gkl_cut.py).
# Кусок = FT_Стекло_Ширина × FT_Стекло_Высота (ячейка + заход в паз), кусков на панель = FT_ГКЛ_Кусков (2 слоя).
# Пропускает панели нулевого размера. Аргументы: out_csv.
import json, io
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
rows = []; skipped = 0
for p in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
    k = p.LookupParameter(u"FT_ГКЛ_Кусков")
    if k is None or k.AsInteger() <= 0:
        continue
    pw = p.get_Parameter(BuiltInParameter.CURTAIN_WALL_PANELS_WIDTH)
    if pw is not None and pw.AsDouble() <= 0:
        skipped += 1; continue
    w = int(round(p.LookupParameter(u"FT_Стекло_Ширина").AsDouble() * FT))
    h = int(round(p.LookupParameter(u"FT_Стекло_Высота").AsDouble() * FT))
    host = p.Host
    for i in range(k.AsInteger()):
        rows.append((p.Id.Value, host.Id.Value if host else -1, i + 1, w, h))
import os
if not os.path.isdir(os.path.dirname(a["out_csv"])):
    os.makedirs(os.path.dirname(a["out_csv"]))
# одной записью: IronPython с utf-8-sig ставит BOM на каждый write
txt = u"panel_id;wall_id;layer;w_mm;h_mm\n" + u"".join(u"%d;%d;%d;%d;%d\n" % r for r in rows)
with io.open(a["out_csv"], "w", encoding="utf-8-sig") as f:
    f.write(txt)
__output__ = {"status": "completed_unverified", "summary": u"%s: кусков ГКЛ %d (панелей %d), пропущено нулевых %d" % (
    doc.Title, len(rows), len(set(r[0] for r in rows)), skipped), "out_csv": a["out_csv"]}
