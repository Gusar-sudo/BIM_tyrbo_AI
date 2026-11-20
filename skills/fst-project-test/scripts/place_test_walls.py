# -*- coding: utf-8 -*-
# Тестовый проект: поставить пробные витражи заданного типа (длина × высота) в ряд, без сетки, и прочитать панели.
# Аргументы: wall_type, walls [[длина_мм, высота_мм], ...], origin_mm [x, y], gap_mm, comment, dry_run.
import json
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8; DRY = bool(a.get("dry_run", True))
wt = [w for w in FilteredElementCollector(doc).OfClass(WallType) if w.Name == a["wall_type"]][0]
lvl = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: l.Elevation)[0]
x, y = a["origin_mm"]; gap = a.get("gap_mm", 1000)
t = Transaction(doc, u"FT: пробные стены"); t.Start()
rows = []
try:
    for L, H in a["walls"]:
        ln = Line.CreateBound(XYZ(x / FT, y / FT, 0), XYZ((x + L) / FT, y / FT, 0))
        w = Wall.Create(doc, ln, wt.Id, lvl.Id, H / FT, 0, False, False)
        c = w.LookupParameter(u"Комментарии")
        if c and a.get("comment"):
            c.Set(a["comment"])
        rows.append((w, L, H)); x += L + gap
    doc.Regenerate()
    out = []
    for w, L, H in rows:
        for pid in w.CurtainGrid.GetPanelIds():
            p = doc.GetElement(pid)
            g = lambda n: p.LookupParameter(n)
            out.append({"wall": w.Id.Value, "L": L, "H": H, "panel": p.Id.Value, "type": p.Name,
                        "кусок": [round(g(u"FT_Стекло_Ширина").AsDouble() * FT), round(g(u"FT_Стекло_Высота").AsDouble() * FT)],
                        "ГКЛ_м2": round(g(u"FT_ГКЛ_Площадь").AsDouble() * 0.09290304, 3),
                        "утепл_м2": round(g(u"FT_Утеплитель_Площадь").AsDouble() * 0.09290304, 3),
                        "кусков": g(u"FT_ГКЛ_Кусков").AsInteger(), "больше_листа": g(u"FT_ГКЛ_Больше_листа").AsInteger()})
    warn = [m.GetDescriptionText() for m in doc.GetWarnings()]
    if DRY:
        t.RollBack()
    else:
        t.Commit()
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
__output__ = {"status": "completed_unverified", "summary": u"%sстен %d, панелей %d, предупреждений %d" % (
    u"ПРОБА (откат): " if DRY else u"", len(rows), len(out), len(warn)), "panels": out, "warnings": warn[:10], "level": lvl.Name}
