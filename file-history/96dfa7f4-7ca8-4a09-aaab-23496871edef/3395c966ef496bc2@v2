# -*- coding: utf-8 -*-
# Поправки размера стекла по альбому: для каждой стеклянной панели найти импост с каждой стороны (любой стены),
# определить стойку по профилю и записать FT_Стекло_Поправка_Ширина/Высота = сумма добавок сторон − 2·FT_Стекло_Добавка.
# Неизвестные профили (нет формулы в альбоме) — добавка = база, панель в списке «нет данных». Аргументы: families, dry_run, tol_mm.
import json, re
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
DRY = bool(args.get("dry_run", True))
TOL = float(args.get("tol_mm", 120)) / FT
SIDE = {u"М2": {u"FSC21": 10.5, u"FSC139": 17.0, u"FSC22": 14.5, u"FSC18": 12.5, u"FSC17": 16.0, u"FSC144": 11.5},
        u"М3": {u"FSC01": 12.5, u"FSC01К": 12.5, u"FSC111": 17.0, u"FSC08": 14.5, u"FSC04": 14.25}}
PAIR = {(u"М2", u"FSC139", u"FSC21"): 28.5, (u"М2", u"FSC139", u"FSC22"): 30.0, (u"М2", u"FSC21", u"FSC22"): 25.0}

# импосты: кривая, вертикальный?, система и код профиля
mulls = []
for m in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType():
    try:
        c = m.LocationCurve
    except Exception:
        c = None
    if c is None:
        continue
    mt = doc.GetElement(m.GetTypeId())
    pp = mt.get_Parameter(BuiltInParameter.MULLION_PROFILE) if mt else None
    sym = doc.GetElement(pp.AsElementId()) if pp else None
    fam = sym.FamilyName if sym else u""
    mm = re.search(u"Профиль_(М\\d)_(FSC\\d+К?)", fam)
    d = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize()
    mulls.append({"c": c, "vert": abs(d.Z) > 0.9, "sys": mm.group(1) if mm else None, "code": mm.group(2) if mm else None,
                  "fam": fam.replace(u"BIMLIB_Профиль_", u"").replace(u"_ФристайлТехнолоджи", u"")[:45]})


def near(P, vert):
    best, bd = None, TOL
    for m in mulls:
        if m["vert"] != vert:
            continue
        try:
            r = m["c"].Project(P)
        except Exception:
            r = None
        if r is not None and r.Distance < bd:
            best, bd = m, r.Distance
    return best


def sides_sum(sysn, a, b, base):
    ca, cb = (a["code"] if a else None), (b["code"] if b else None)
    if a and b and a["sys"] == sysn and b["sys"] == sysn:
        k = tuple([sysn] + sorted([ca, cb]))
        if k in PAIR:
            return PAIR[k], []
    tot, unk = 0.0, []
    for m in (a, b):
        v = SIDE.get(sysn, {}).get(m["code"]) if (m and m["sys"] == sysn) else None
        if v is None:
            unk.append(m["fam"] if m else u"нет импоста")
            v = base
        tot += v
    return tot, unk


res = {"set": 0, "nonzero": 0, "unknown": {}, "pairs": {}, "samples": []}
tg = TransactionGroup(doc, u"Поправки размера стекла по альбому"); tg.Start()
try:
    t = Transaction(doc, u"Поправки размера стекла по альбому"); t.Start()
    for pn in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
        st = doc.GetElement(pn.GetTypeId())
        if st is None or not hasattr(st, "FamilyName") or st.FamilyName not in args["families"]:
            continue
        m1 = st.LookupParameter(u"FT_Система_М1")
        base = st.LookupParameter(u"FT_Стекло_Добавка").AsDouble() * FT
        if (m1 and m1.AsInteger() == 1) or base < 0:
            continue
        sysn = u"М3" if abs(base - 12.5) < 0.01 else u"М2"
        w = pn.Host
        if w is None or not isinstance(w.Location, LocationCurve) or not isinstance(w.Location.Curve, Line):
            continue
        d = w.Location.Curve.Direction
        pts = []

        def walk(ge, tr):
            for g in ge:
                if isinstance(g, Solid) and g.Volume > 1e-9:
                    for e in g.Edges:
                        for q in e.Tessellate():
                            pts.append(tr.OfPoint(q) if tr else q)
                elif isinstance(g, GeometryInstance):
                    walk(g.GetSymbolGeometry(), tr.Multiply(g.Transform) if tr else g.Transform)
        walk(pn.get_Geometry(Options()), None)
        if not pts:
            continue
        us = [p.X * d.X + p.Y * d.Y for p in pts]; zs = [p.Z for p in pts]
        cx = sum(p.X for p in pts) / len(pts); cy = sum(p.Y for p in pts) / len(pts)
        uc = cx * d.X + cy * d.Y
        vs = st.LookupParameter(u"Выступ сбоку").AsDouble(); vt = st.LookupParameter(u"Выступ сверху").AsDouble(); vb = st.LookupParameter(u"Выступ снизу").AsDouble()
        zm = (min(zs) + max(zs)) / 2.0
        PL = XYZ(cx + d.X * (min(us) + vs - uc), cy + d.Y * (min(us) + vs - uc), zm)
        PR = XYZ(cx + d.X * (max(us) - vs - uc), cy + d.Y * (max(us) - vs - uc), zm)
        PB = XYZ(cx, cy, min(zs) + vb); PT = XYZ(cx, cy, max(zs) - vt)
        mL, mR, mB, mT = near(PL, True), near(PR, True), near(PB, False), near(PT, False)
        sw, uw = sides_sum(sysn, mL, mR, base)
        sh, uh = sides_sum(sysn, mB, mT, base)
        cw = round(sw - 2 * base, 2); ch = round(sh - 2 * base, 2)
        pn.LookupParameter(u"FT_Стекло_Поправка_Ширина").Set(cw / FT)
        pn.LookupParameter(u"FT_Стекло_Поправка_Высота").Set(ch / FT)
        res["set"] += 1
        if cw or ch:
            res["nonzero"] += 1
        key = u"%s Ш:%s|%s В:%s|%s" % (sysn, mL["code"] if mL else u"-", mR["code"] if mR else u"-", mB["code"] if mB else u"-", mT["code"] if mT else u"-")
        res["pairs"][key] = res["pairs"].get(key, 0) + 1
        for u in uw + uh:
            res["unknown"][u] = res["unknown"].get(u, 0) + 1
        if (cw or ch) and len(res["samples"]) < 12:
            res["samples"].append([int(pn.Id.Value), key, cw, ch])
    t.Commit()
    # проверка: перечитать итоговые размеры у примеров
    for s in res["samples"]:
        pn = doc.GetElement(ElementId(s[0]))
        s.append([round(pn.LookupParameter(u"FT_Стекло_Ширина").AsDouble() * FT, 1), round(pn.LookupParameter(u"FT_Стекло_Высота").AsDouble() * FT, 1),
                  round(pn.LookupParameter(u"ADSK_Размер_Ширина").AsDouble() * FT, 1), round(pn.LookupParameter(u"ADSK_Размер_Высота").AsDouble() * FT, 1)])
    res["warnings"] = len(doc.GetWarnings())
finally:
    if DRY:
        tg.RollBack()
    else:
        tg.Assimilate()
res["dry_run"] = DRY
res["status"] = "completed_unverified"
res["summary"] = u"%sпанелей %d, с поправкой %d, сторон без данных альбома %d, предупреждений %s" % (
    u"ПРОБНЫЙ ПРОГОН (откат): " if DRY else u"", res["set"], res["nonzero"], sum(res["unknown"].values()), res.get("warnings"))
__output__ = res
