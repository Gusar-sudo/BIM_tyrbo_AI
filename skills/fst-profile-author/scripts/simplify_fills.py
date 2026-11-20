# -*- coding: utf-8 -*-
# Локально: упростить контуры заливок (fill_parity.py) — Дуглас–Пекер (eps_mm) + удаление отрезков короче min_seg_mm
# (с проверкой, что хорда не пересекает контур). Сильно уменьшает число линий и размер семейств.
# py -P -E simplify_fills.py <fills_dir> <out_dir> [--eps=0.03] [--min_seg=0.8]
import json, io, os, sys, math
IN, OUT = sys.argv[1:3]
opt = dict(a.lstrip("-").split("=", 1) for a in sys.argv[3:] if "=" in a)
EPS = float(opt.get("eps", 0.03)); MINS = float(opt.get("min_seg", 0.8))
os.makedirs(OUT, exist_ok=True)


def dp(pts, eps):
    if len(pts) < 3: return pts
    ax, ay = pts[0]; bx, by = pts[-1]; L = math.hypot(bx - ax, by - ay) or 1e-12; dmax, k = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs((bx - ax) * (ay - pts[i][1]) - (ax - pts[i][0]) * (by - ay)) / L
        if d > dmax: dmax, k = d, i
    return dp(pts[:k + 1], eps)[:-1] + dp(pts[k:], eps) if dmax > eps else [pts[0], pts[-1]]


def cross(p, q, r, s):
    o = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if p in (r, s) or q in (r, s): return False
    return o(r, s, p) * o(r, s, q) < 0 and o(p, q, r) * o(p, q, s) < 0


def simp(loop):
    pts = [tuple(p) for p in loop]
    if len(pts) > 1 and pts[0] == pts[-1]: pts = pts[:-1]
    if len(pts) < 4: return pts
    i1 = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
    s = dp(pts[:i1 + 1], EPS)[:-1] + dp(pts[i1:] + [pts[0]], EPS)[:-1]
    s = [(round(p[0], 4), round(p[1], 4)) for p in s]
    ch = True; stuck = set()
    while ch and len(s) > 3:
        ch = False
        for i in range(len(s)):
            j = (i + 1) % len(s)
            if math.hypot(s[j][0] - s[i][0], s[j][1] - s[i][1]) < MINS and (s[i], s[j]) not in stuck:
                for k in (j, i):
                    n = len(s); p = s[k - 1]; q = s[(k + 1) % n]
                    if not any(cross(p, q, s[m], s[(m + 1) % n]) for m in range(n) if m not in ((k - 2) % n, (k - 1) % n, k % n, (k + 1) % n)):
                        del s[k]; ch = True; break
                else:
                    stuck.add((s[i], s[j]))
                if ch: break
    return s


tot0 = tot1 = 0
for f in os.listdir(IN):
    if not f.endswith(".json") or f.startswith("_"): continue
    d = json.load(io.open(os.path.join(IN, f), encoding="utf-8"))
    regs = []
    for r in d["regions"]:
        tot0 += len(r["outer"]) + sum(len(h) for h in r["holes"])
        o = simp(r["outer"])
        hs = [simp(h) for h in r["holes"]]
        hs = [h for h in hs if len(h) >= 3]
        if len(o) >= 3:
            regs.append({"outer": [list(p) for p in o], "holes": [[list(p) for p in h] for h in hs]})
            tot1 += len(o) + sum(len(h) for h in hs)
    io.open(os.path.join(OUT, f), "w", encoding="utf-8").write(json.dumps({"regions": regs}, ensure_ascii=False))
print(json.dumps({"points_before": tot0, "points_after": tot1, "ratio": round(tot1 / max(1, tot0), 3)}))
