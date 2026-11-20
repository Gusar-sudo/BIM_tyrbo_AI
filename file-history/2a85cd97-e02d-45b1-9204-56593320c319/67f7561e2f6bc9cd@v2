# -*- coding: utf-8 -*-
# Только чтение: разобрать профили импостов на части для сравнения (например «открытый» и «Закрытый» боковой).
# По каждому профилю: внешний габарит собственных линий (3D-тело), контуры собственных линий и замкнутые контуры
# вложенной графики (рейки, держатели) с габаритом x0..x1, y0..y1 в мм координат профиля, число заливок.
# EditFamily -> чтение -> Close без сохранения. Модель не меняется. Аргументы: profiles [короткие имена без «BIMLIB_Профиль_»], min_h_mm
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MIN_H = float(args.get("min_h_mm", 3.0))
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))


def key(p):
    return (round(p.X * FT, 2), round(p.Y * FT, 2))


def loops_of(d, T):
    curves = []
    for ce in FilteredElementCollector(d).OfClass(CurveElement):
        c = ce.GeometryCurve
        if c is not None and c.IsBound:
            curves.append((key(T.OfPoint(c.GetEndPoint(0))), key(T.OfPoint(c.GetEndPoint(1))), [T.OfPoint(q) for q in c.Tessellate()]))
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for a, b, _ in curves:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups = {}
    for a, b, pts in curves:
        groups.setdefault(find(a), []).append(pts)
    out = []
    for g in groups.values():
        xs = [p.X * FT for ps in g for p in ps]; ys = [p.Y * FT for ps in g for p in ps]
        if max(ys) - min(ys) >= MIN_H or max(xs) - min(xs) >= MIN_H:
            out.append([round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1), len(g)])
    return sorted(out)


res = {}
for short in args["profiles"]:
    fn = u"BIMLIB_Профиль_%s_ФристайлТехнолоджи" % short
    if fn not in fams:
        res[short] = None; continue
    pd = doc.EditFamily(fams[fn])
    r = {}
    try:
        own = loops_of(pd, Transform.Identity)
        r["own"] = own
        if own:
            r["ext"] = [min(o[0] for o in own), max(o[1] for o in own), min(o[2] for o in own), max(o[3] for o in own)]
        nested = []
        for fi in FilteredElementCollector(pd).OfClass(FamilyInstance):
            nf = fi.Symbol.Family
            T = fi.GetTransform()
            nd = pd.EditFamily(nf)
            try:
                nested.append({"family": nf.Name.replace(u"BIMLIB_ЭлементыУзлов_", u""), "mirrored": fi.Mirrored,
                               "loops": loops_of(nd, T), "fills": FilteredElementCollector(nd).OfClass(FilledRegion).GetElementCount(),
                               "groups": FilteredElementCollector(nd).OfClass(Group).GetElementCount()})
            finally:
                nd.Close(False)
        r["nested"] = nested
    finally:
        pd.Close(False)
    res[short] = r
__output__ = {"status": "completed_unverified", "summary": u"профилей %d" % len(res), "result": res}
