# -*- coding: utf-8 -*-
# Точка отсчёта 3 мм по сторонам столба (из дампа probe_pocket.py): луч снаружи к оси по линиям внутри полосы стекла,
# первое касание графики узла (паз) и 3D-тела. Точка отсчёта — самое мелкое касание паза в полосе (где дно паза начинает меняться).
# py -P -E pocket_reference.py <pocket.json> <out.json> [--face_m2=30.6] [--face_m3=35.7] [--glass=10]
import json, io, sys
D = json.load(io.open(sys.argv[1], encoding="utf-8"))
opt = dict(a.lstrip("-").split("=", 1) for a in sys.argv[3:] if "=" in a)
FACE = {u"М2": float(opt.get("face_m2", 30.6)), u"М3": float(opt.get("face_m3", 35.7))}
G = float(opt.get("glass", 10))
# сторона: (ось движения, знак наружу)
SIDES = {"-X": (0, -1), "+X": (0, 1), "-Y": (1, -1), "+Y": (1, 1)}


def first_hit(segs, axis, sign, lat):
    # луч по линии lat (вторая координата) от sign*inf к 0; вернуть |координату| первого пересечения (наибольшую)
    best = None
    o = 1 - axis
    for s in segs:
        a = (s[0], s[1]); b = (s[2], s[3])
        la, lb = a[o], b[o]
        if (la - lat) * (lb - lat) > 0 or la == lb:
            continue
        t = (lat - la) / (lb - la); v = a[axis] + t * (b[axis] - a[axis])
        if v * sign <= 0:
            continue
        if best is None or v * sign > best:
            best = v * sign
    return best


out = {}
for n, r in D.items():
    if not isinstance(r, dict):
        continue
    face = FACE[u"М3" if n.startswith(u"М3") else u"М2"]
    res = {}
    for sd, (ax, sg) in SIDES.items():
        band = {}
        for half in (-1, 1):
            lats = [half * (face - k * 0.25) for k in range(int(G / 0.25) + 1)]
            nest = [first_hit(r["nested"], ax, sg, l) for l in lats]
            own = [first_hit(r["own"], ax, sg, l) for l in lats]
            band[str(half)] = {"nested": nest, "own": own, "lat": lats}
        # есть ли паз: тело в полосе глубже наружной грани тела
        allown = [v for h in band.values() for v in h["own"] if v is not None]
        outer = max([max(s[0] * sg, s[2] * sg) if ax == 0 else max(s[1] * sg, s[3] * sg) for s in r["own"]] or [0])
        nn = [v for h in band.values() for v in h["nested"] if v is not None]
        res[sd] = {"outer_body": round(outer, 2),
                   "groove": bool(allown) and min(allown) < outer - 3,
                   "ref_nested_max": round(max(nn), 2) if nn else None,
                   "nested_min": round(min(nn), 2) if nn else None,
                   "own_max": round(max(allown), 2) if allown else None, "own_min": round(min(allown), 2) if allown else None,
                   "per_half": dict((h, {"nested": [None if v is None else round(v, 2) for v in band[h]["nested"]][::4],
                                          "own": [None if v is None else round(v, 2) for v in band[h]["own"]][::4]}) for h in band)}
    out[n] = res
io.open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
for n, res in out.items():
    print(n)
    for sd, v in res.items():
        if v["groove"]:
            print("  %s outer %.1f  nested %s..%s  own %s..%s" % (sd, v["outer_body"], v["nested_min"], v["ref_nested_max"], v["own_min"], v["own_max"]))
