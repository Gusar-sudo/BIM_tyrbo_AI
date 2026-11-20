# -*- coding: utf-8 -*-
# Чтение: стены-витражи с панелями нулевого размера — сетка (линии U/V, удалённые сегменты),
# панели по ячейкам (позиция вдоль стены, размер, нулевая ли). Аргументы: нет. Документ — активный.
from Autodesk.Revit.DB import *
doc = __revit__.ActiveUIDocument.Document
MM = 304.8
def zero(p):
    w = p.get_Parameter(BuiltInParameter.CURTAIN_WALL_PANELS_WIDTH)
    return w is not None and w.AsDouble() <= 0
walls = {}
for p in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
    if zero(p) and p.Host is not None:
        walls[p.Host.Id.Value] = p.Host
rows = []
for w in walls.values():
    g = w.CurtainGrid; lc = w.Location.Curve; o = lc.GetEndPoint(0); d = (lc.GetEndPoint(1) - o).Normalize()
    def along(pt): return round((pt - o).DotProduct(d) * MM)
    lines = []
    for gid, kind in [(i, "U") for i in g.GetUGridLineIds()] + [(i, "V") for i in g.GetVGridLineIds()]:
        gl = doc.GetElement(gid)
        c = gl.FullCurve
        pos = along(c.GetEndPoint(0)) if kind == "U" else round(c.GetEndPoint(0).Z * MM)
        lines.append({"kind": kind, "pos": pos, "segments_all": gl.AllSegmentCurves.Size, "segments_exist": gl.ExistingSegmentCurves.Size})
    panels = []
    for pid in g.GetPanelIds():
        p = doc.GetElement(pid)
        bb = p.get_BoundingBox(None)
        tr = p.GetTransform() if hasattr(p, "GetTransform") else None
        panels.append({"id": pid.Value, "zero": zero(p), "type": p.Name,
                       "x": along(tr.Origin) if tr else None, "z": round(tr.Origin.Z * MM) if tr else None,
                       "w": round(p.get_Parameter(BuiltInParameter.CURTAIN_WALL_PANELS_WIDTH).AsDouble() * MM),
                       "h": round(p.get_Parameter(BuiltInParameter.CURTAIN_WALL_PANELS_HEIGHT).AsDouble() * MM),
                       "glass": [q.AsValueString() if q else None for q in (p.LookupParameter(u"FT_Стекло_Ширина"), p.LookupParameter(u"FT_Стекло_Высота"))],
                       "cat": p.Category.Name if p.Category else None,
                       "bb": [along(bb.Min), along(bb.Max), round(bb.Min.Z*MM), round(bb.Max.Z*MM)] if bb else None})
    rows.append({"wall_id": w.Id.Value, "type": w.WallType.Name, "length": round(lc.Length * MM),
                 "height": round(w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble() * MM),
                 "lines": lines, "panels": panels})
__output__ = {"status": "completed_unverified", "summary": u"стен с нулевыми панелями: %d" % len(rows), "walls": rows}
