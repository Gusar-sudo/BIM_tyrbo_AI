# -*- coding: utf-8 -*-
# Только чтение: в профиле (семейство профиля импоста) разобрать группы вложенной графики («Элементы узлов»)
# на замкнутые контуры: для каждой группы — контуры (точки в координатах ПРОФИЛЯ, мм), площадь, габарит.
# Аргументы: family (имя семейства профиля), tol_mm (0.05), dump_path (JSON с контурами, необяз.)
import json, io, math
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
TOL = float(args.get("tol_mm", 0.05)) / FT
fam = [f for f in FilteredElementCollector(doc).OfClass(Family) if f.Name == args["family"]][0]
pd = doc.EditFamily(fam)
res = {"groups": []}
try:
    fi = list(FilteredElementCollector(pd).OfClass(FamilyInstance))[0]
    T = fi.GetTotalTransform()
    ysg = -1 if fi.Mirrored else 1
    nd = pd.EditFamily(fi.Symbol.Family)
    try:
        def to_prof(p):
            q = T.OfPoint(p); return (q.X * FT, ysg * q.Y * FT)
        for g in FilteredElementCollector(nd).OfClass(Group):
            segs = []
            for mid in g.GetMemberIds():
                el = nd.GetElement(mid)
                if not isinstance(el, CurveElement):
                    continue
                c = el.GeometryCurve
                pts = [to_prof(p) for p in c.Tessellate()]
                for i in range(len(pts) - 1):
                    segs.append((pts[i], pts[i + 1]))
            # сцепить отрезки в контуры
            t = TOL * FT
            loops = []; rest = list(segs)
            while rest:
                a, b = rest.pop(0); chain = [a, b]; grown = True
                while grown:
                    grown = False
                    for i, (p, q) in enumerate(rest):
                        if math.hypot(p[0] - chain[-1][0], p[1] - chain[-1][1]) < t:
                            chain.append(q); rest.pop(i); grown = True; break
                        if math.hypot(q[0] - chain[-1][0], q[1] - chain[-1][1]) < t:
                            chain.append(p); rest.pop(i); grown = True; break
                closed = math.hypot(chain[0][0] - chain[-1][0], chain[0][1] - chain[-1][1]) < t
                area = 0.5 * abs(sum(chain[i][0] * chain[i + 1][1] - chain[i + 1][0] * chain[i][1] for i in range(len(chain) - 1)))
                xs = [p[0] for p in chain]; ys = [p[1] for p in chain]
                loops.append({"closed": closed, "n": len(chain), "area": round(area, 1), "bbox": [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)], "pts": [[round(p[0], 3), round(p[1], 3)] for p in chain]})
            loops.sort(key=lambda l: -l["area"])
            res["groups"].append({"name": g.GroupType.Name, "segs": len(segs), "loops": loops})
    finally:
        nd.Close(False)
finally:
    pd.Close(False)
if args.get("dump_path"):
    io.open(args["dump_path"], "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False))
short = [{"name": g["name"], "segs": g["segs"], "loops": [{k: l[k] for k in ("closed", "n", "area", "bbox")} for l in g["loops"][:6]]} for g in res["groups"]]
__output__ = {"status": "completed_unverified", "summary": u"групп %d" % len(res["groups"]), "result": short}
