# -*- coding: utf-8 -*-
# Только чтение: стороны панелей BIMLIB (кроме М1) у вертикальных импостов-столбов — тип импоста, с какой стороны его
# профиля подходит стекло (направление «от оси к панели» в осях экземпляра), расстояние от оси до края панели и до торца стекла.
# Аргументы: codes [FSC17, FSC04, FSC05 …], out_json
import json, io, re
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
CODES = set(args.get("codes", []))


def glass_u(pn, d_):
    us = []
    def walk(ge):
        for g in ge:
            if isinstance(g, Solid) and g.Volume > 1e-9 and g.Faces.Size:
                m = doc.GetElement(g.Faces.get_Item(0).MaterialElementId)
                if m is not None and u"Стекло" in m.Name:
                    for e in g.Edges:
                        for q in e.Tessellate():
                            us.append(q.X * d_.X + q.Y * d_.Y)
            elif isinstance(g, GeometryInstance):
                walk(g.GetInstanceGeometry())
    o = Options(); o.DetailLevel = ViewDetailLevel.Fine
    walk(pn.get_Geometry(o))
    return (min(us), max(us)) if us else None


mulls = []
for m in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType():
    try:
        c = m.LocationCurve
    except Exception:
        c = None
    if c is None:
        continue
    d0 = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize()
    if abs(d0.Z) < 0.9:
        continue
    mt = doc.GetElement(m.GetTypeId()); sym = doc.GetElement(mt.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId()) if mt else None
    fn = sym.FamilyName if sym else u""
    mm = re.search(u"Профиль_(М\\d)_(FSC\\d+К?)_(\\w+?)_Фристайл", fn)
    tr = m.GetTransform()
    mulls.append({"m": m, "c": c, "code": mm.group(2) if mm else None, "kind": mm.group(3) if mm else None, "type": Element.Name.GetValue(mt),
                  "bx": tr.BasisX, "by": tr.BasisY, "hf": m.HandFlipped if hasattr(m, "HandFlipped") else None, "ff": m.FacingFlipped if hasattr(m, "FacingFlipped") else None})


def near(P, tol=150 / FT):
    best, bd = None, tol
    for k in mulls:
        r = k["c"].Project(P)
        if r is not None and r.Distance < bd:
            best, bd = k, r.Distance
    return best, bd


rows = []
for pn in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
    st = doc.GetElement(pn.GetTypeId())
    if not isinstance(st, FamilySymbol) or not st.Family.Name.startswith(u"BIMLIB_ПанельВитража") or u"М1" in st.Name:
        continue
    bb = pn.get_BoundingBox(None); w = pn.Host
    if bb is None or w is None or not isinstance(w.Location, LocationCurve):
        continue
    d_ = w.Location.Curve.Direction; c = (bb.Min + bb.Max) * 0.5
    pr = w.Location.Curve.Project(XYZ(c.X, c.Y, w.Location.Curve.GetEndPoint(0).Z))
    if pr is not None:
        c = XYZ(pr.XYZPoint.X, pr.XYZPoint.Y, c.Z)
    hw = abs((bb.Max - bb.Min).DotProduct(d_)) / 2.0
    g = None
    for side, P, sg in ((u"L", c - d_ * hw, 1.0), (u"R", c + d_ * hw, -1.0)):
        k, dist = near(P)
        if k is None or k["code"] not in CODES:
            continue
        if g is None:
            g = glass_u(pn, d_)
        p0 = k["c"].GetEndPoint(0)
        to_panel = d_ * sg   # от столба к панели
        lx = to_panel.DotProduct(k["bx"]); ly = to_panel.DotProduct(k["by"])
        # смещение оси столба от линии края панели поперёк (вдоль нормали стены)
        nrm = XYZ(-d_.Y, d_.X, 0)
        au = p0.X * d_.X + p0.Y * d_.Y
        edge = ((P.X * d_.X + P.Y * d_.Y) - au) * sg * FT
        gend = None if g is None else (((g[0] - au) if side == u"L" else (au - g[1])) * FT)
        off = ((P - XYZ(p0.X, p0.Y, P.Z)).DotProduct(nrm)) * FT
        q = pn.LookupParameter(u"FT_Стекло_Поправка_Слева" if side == u"L" else u"FT_Стекло_Поправка_Справа")
        rows.append({"panel": int(pn.Id.Value), "ptype": st.Name, "wall": int(w.Id.Value), "side": side, "mull": int(k["m"].Id.Value), "mtype": k["type"],
                     "code": k["code"], "kind": k["kind"], "lx": round(lx, 3), "ly": round(ly, 3), "hf": k["hf"], "ff": k["ff"],
                     "edge": round(edge, 2), "glass_end": None if gend is None else round(gend, 2), "off_norm": round(off, 2),
                     "dist": round(dist * FT, 1), "corr_side": None if q is None else round(q.AsDouble() * FT, 3),
                     "corr_w": round(pn.LookupParameter(u"FT_Стекло_Поправка_Ширина").AsDouble() * FT, 3) if pn.LookupParameter(u"FT_Стекло_Поправка_Ширина") else None})
if args.get("out_json"):
    io.open(args["out_json"], "w", encoding="utf-8").write(json.dumps(rows, ensure_ascii=False, indent=1))
grp = {}
for r in rows:
    key = u"%s | lx %+.0f ly %+.0f | край %.1f | стекло %s | смещ %.0f" % (r["mtype"], r["lx"], r["ly"], r["edge"], r["glass_end"], r["off_norm"])
    grp[key] = grp.get(key, 0) + 1
__output__ = {"status": "completed_unverified", "summary": u"только чтение: сторон %d, групп %d" % (len(rows), len(grp)), "groups": sorted(grp.items())[:120]}
