# -*- coding: utf-8 -*-
# Контуры заливок «алюминий» для графики узла: для каждой группы — стенки профиля
# (чётно-нечётное объединение всех замкнутых контуров группы: внешний минус полости), в координатах ВЛОЖЕННОГО, мм.
# Группа без замкнутых контуров (держатель FC.C-06) — контур из DWG (профиль -> вложенный: y * sign).
# Выход: {"fills": [{"group", "loops": [...]}]} + превью PNG.
import json, io, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageChops
import contourpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

a = json.load(io.open(sys.argv[1], encoding="utf-8-sig"))
C = json.load(io.open(a["curves_json"], encoding="utf-8"))
PX = float(a.get("px_mm", 50)); MINS = float(a.get("min_seg_mm", 0.85)); DPE = float(a.get("dp_mm", 0.02))
ysg = -1.0 if C.get("mirrored") else 1.0


def arc3(p1, pm, p2, step=2.0):
    ax, ay = p1; bx, by = pm; cx, cy = p2
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [tuple(p1), tuple(p2)]
    ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    R = math.hypot(ax-ux, ay-uy); a1 = math.atan2(ay-uy, ax-ux); am = math.atan2(by-uy, bx-ux); a2 = math.atan2(cy-uy, cx-ux)
    n_ = lambda t: t % (2*math.pi)
    sw = n_(a2-a1)
    if n_(am-a1) > sw:
        sw -= 2*math.pi
    n = max(1, int(abs(math.degrees(sw))/step))
    return [(ux+R*math.cos(a1+sw*k/n), uy+R*math.sin(a1+sw*k/n)) for k in range(n)] + [tuple(p2)]


def segs_of(curves):
    out = []
    for c in curves:
        if c[0] == "L":
            out.append(((c[1], c[2]), (c[3], c[4])))
        elif c[0] == "A":
            ps = arc3(c[1:3], c[3:5], c[5:7]); out += [(ps[i], ps[i+1]) for i in range(len(ps)-1)]
        elif c[0] == "C":
            ps = [(c[1]+c[3]*math.cos(2*math.pi*k/180), c[2]+c[3]*math.sin(2*math.pi*k/180)) for k in range(181)]
            out += [(ps[i], ps[i+1]) for i in range(len(ps)-1)]
        else:
            ps = c[1]; out += [(tuple(ps[i]), tuple(ps[i+1])) for i in range(len(ps)-1)]
    return out


def chain(segs, tol):
    loops = []; rest = list(segs); opened = 0
    while rest:
        a0, b0 = rest.pop(0); ch = [a0, b0]; grown = True
        while grown:
            grown = False
            for i, (p, q) in enumerate(rest):
                if math.hypot(p[0]-ch[-1][0], p[1]-ch[-1][1]) < tol:
                    ch.append(q); rest.pop(i); grown = True; break
                if math.hypot(q[0]-ch[-1][0], q[1]-ch[-1][1]) < tol:
                    ch.append(p); rest.pop(i); grown = True; break
        if len(ch) > 3 and math.hypot(ch[0][0]-ch[-1][0], ch[0][1]-ch[-1][1]) < tol:
            loops.append(ch[:-1])
        else:
            opened += 1
    return loops, opened


def holder_dwg():
    H = json.load(io.open(a["holder_json"], encoding="utf-8"))["segs"]
    segs = []
    for s in H:
        if s[0] == "L":
            segs.append(((s[1], ysg*s[2]), (s[3], ysg*s[4])))
        else:
            ps = arc3((s[1], ysg*s[2]), (s[3], ysg*s[4]), (s[5], ysg*s[6]), step=6.0); segs += [(ps[i], ps[i+1]) for i in range(len(ps)-1)]
    l, _ = chain(segs, 0.005)
    return [max(l, key=lambda L: len(L))]


def dp(pts, eps):
    if len(pts) < 3:
        return pts
    P = np.array(pts); st = [(0, len(P)-1)]; keep = np.zeros(len(P), bool); keep[0] = keep[-1] = True
    while st:
        i, j = st.pop()
        if j <= i+1:
            continue
        d = P[j]-P[i]; L = np.hypot(*d) or 1e-12
        dist = np.abs(d[0]*(P[i+1:j, 1]-P[i, 1]) - d[1]*(P[i+1:j, 0]-P[i, 0]))/L
        k = int(np.argmax(dist))
        if dist[k] > eps:
            m = i+1+k; keep[m] = True; st += [(i, m), (m, j)]
    return [tuple(p) for p in P[keep]]


def minseg(pts):
    out = list(pts); ch = True
    while ch and len(out) > 3:
        ch = False
        for i in range(len(out)):
            j = (i+1) % len(out); p, q = out[i], out[j]
            if math.hypot(q[0]-p[0], q[1]-p[1]) < MINS:
                out[i] = ((p[0]+q[0])/2, (p[1]+q[1])/2); out.pop(j); ch = True; break
    return out


fills = []; report = []
for g in C["groups"]:
    loops, opened = chain(segs_of(g["curves"]), float(a.get("chain_tol_mm", 0.3)))
    src = "nested"
    if not loops or opened > 2:
        if g["name"] in a.get("dwg_groups", []):
            loops = holder_dwg(); src = "dwg"
    report.append([g["name"], len(loops), opened, src])
    if not loops:
        continue
    allp = np.array([p for L in loops for p in L]); x0, y0 = allp.min(0) - 1; x1, y1 = allp.max(0) + 1
    W = int((x1-x0)*PX)+1; Hh = int((y1-y0)*PX)+1
    acc = Image.new("1", (W, Hh), 0)
    for L in loops:          # чётно-нечётно: полости вычитаются
        im = Image.new("1", (W, Hh), 0); ImageDraw.Draw(im).polygon([((x-x0)*PX, (y-y0)*PX) for x, y in L], fill=1)
        acc = ImageChops.logical_xor(acc, im)
    M = np.array(acc, dtype=float)
    out = []
    for ln in contourpy.contour_generator(z=M).lines(0.5):
        pts = [(x0 + c/PX, y0 + r/PX) for c, r in ln]
        if len(pts) > 2 and math.hypot(pts[0][0]-pts[-1][0], pts[0][1]-pts[-1][1]) < 1e-6:
            pts = pts[:-1]
        if len(pts) < 4:
            continue
        ar = 0.5*abs(sum(pts[i][0]*pts[(i+1) % len(pts)][1]-pts[(i+1) % len(pts)][0]*pts[i][1] for i in range(len(pts))))
        if ar < 0.5:
            continue
        P0 = np.array(pts); far = int(np.argmax(np.hypot(P0[:, 0]-P0[0, 0], P0[:, 1]-P0[0, 1])))
        s = minseg(dp(pts[:far+1], DPE)[:-1] + dp(pts[far:] + [pts[0]], DPE)[:-1])
        if len(s) >= 3:
            out.append([[round(x, 4), round(y, 4)] for x, y in s])
    fills.append({"group": g["name"], "loops": out})
io.open(a["out_json"], "w", encoding="utf-8").write(json.dumps({"fills": fills, "mirrored": C.get("mirrored")}))
fig, ax = plt.subplots(figsize=(8, 8))
for f in fills:
    for L in f["loops"]:
        P = np.array(L + [L[0]]); ax.fill(P[:, 0], P[:, 1], color="#b8c4d0", alpha=0.8); ax.plot(P[:, 0], P[:, 1], lw=0.4, color="#333")
ax.set_aspect("equal"); fig.savefig(a["preview_png"], dpi=150)
print(json.dumps(report), [len(f["loops"]) for f in fills])
