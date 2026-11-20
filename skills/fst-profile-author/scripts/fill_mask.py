# -*- coding: utf-8 -*-
# Заливка «алюминий» для графики узла по ЛИНИЯМ (без сцепки контуров — она рвётся на Т-стыках):
# 1) все кривые групп растрируются линией 2 px; 2) снаружи = заливка от края; замкнутые области = остальное;
# 3) «толстые» области (полости, внутренность круга) — открытие (эрозия/дилатация на r) + восстановление
#    внутри замкнутых; 4) материал = замкнутые минус толстые — это тонкие стенки профилей;
# 5) контуры материала с вложенностью (внешний + его дыры) -> упрощение (отрезки >= min_seg).
# Координаты — вложенного семейства, мм. Выход: {"regions": [{"outer": [...], "holes": [[...]]}]} + превью.
import json, io, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import contourpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path

a = json.load(io.open(sys.argv[1], encoding="utf-8-sig"))
C = json.load(io.open(a["curves_json"], encoding="utf-8"))
PX = float(a.get("px_mm", 20)); MINS = float(a.get("min_seg_mm", 0.85)); DPE = float(a.get("dp_mm", 0.03))
RT = float(a.get("thick_r_mm", 1.4)); LW = int(a.get("line_w_px", 2)); GROW = int(a.get("grow_px", 1))


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


polys = []
for g in C["groups"]:
    for c in g["curves"]:
        if c[0] == "L":
            polys.append([(c[1], c[2]), (c[3], c[4])])
        elif c[0] == "A":
            polys.append(arc3(c[1:3], c[3:5], c[5:7]))
        elif c[0] == "C":
            polys.append([(c[1]+c[3]*math.cos(2*math.pi*k/180), c[2]+c[3]*math.sin(2*math.pi*k/180)) for k in range(181)])
        else:
            polys.append([tuple(p) for p in c[1]])
allp = np.array([p for P in polys for p in P]); x0, y0 = allp.min(0) - 2; x1, y1 = allp.max(0) + 2
W = int((x1-x0)*PX)+1; H = int((y1-y0)*PX)+1
img = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(img)
for P in polys:
    dr.line([((x-x0)*PX, (y-y0)*PX) for x, y in P], fill=255, width=LW)
line = np.array(img) > 0
# снаружи
ff = img.copy(); ImageDraw.floodfill(ff, (0, 0), 128)
outside = np.array(ff) == 128
enclosed = ~line & ~outside
# толстые области: открытие + геодезическое восстановление
k = max(1, int(round(RT*PX)))
E = Image.fromarray((enclosed*255).astype(np.uint8))
er = E
for _ in range(k):
    er = er.filter(ImageFilter.MinFilter(3))
seed = np.array(er) > 0
encl = enclosed
for it in range(4000):
    nxt = (np.array(Image.fromarray((seed*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0) & encl
    if (nxt == seed).all():
        break
    seed = nxt
thick = seed
mat = enclosed & ~thick
# материал чуть шире — под линии (линии рисуются поверх)
mimg = Image.fromarray((mat*255).astype(np.uint8))
for _ in range(GROW):
    mimg = mimg.filter(ImageFilter.MaxFilter(3))
M = (np.array(mimg) > 0) & ~outside | (np.array(mimg) > 0) & line
M = M.astype(float)


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
        kk = int(np.argmax(dist))
        if dist[kk] > eps:
            m = i+1+kk; keep[m] = True; st += [(i, m), (m, j)]
    return [tuple(p) for p in P[keep]]


def minseg(pts):
    out = list(pts); ch = True
    while ch and len(out) > 3:
        ch = False
        for i in range(len(out)):
            j = (i+1) % len(out); p, q = out[i], out[j]
            if math.hypot(q[0]-p[0], q[1]-p[1]) < MINS:
                # убрать ту из двух точек, чьё удаление меньше искажает контур (площадь треугольника с соседями)
                def tri(k):
                    a_, b_, c_ = out[k-1], out[k], out[(k+1) % len(out)]
                    return abs((b_[0]-a_[0])*(c_[1]-a_[1]) - (b_[1]-a_[1])*(c_[0]-a_[0]))
                out.pop(i if tri(i) <= tri(j) else j); ch = True; break
    return out


def resample(pts, step):
    """равномерно по длине замкнутого контура (все отрезки ~step), затем убрать точки на прямой"""
    P = list(pts) + [pts[0]]
    L = [0.0]
    for i in range(1, len(P)):
        L.append(L[-1] + math.hypot(P[i][0]-P[i-1][0], P[i][1]-P[i-1][1]))
    tot = L[-1]; n = max(4, int(tot / step))
    out = []; j = 0
    for k in range(n):
        s = tot * k / n
        while L[j+1] < s:
            j += 1
        t = (s - L[j]) / ((L[j+1] - L[j]) or 1e-12)
        out.append((P[j][0] + t*(P[j+1][0]-P[j][0]), P[j][1] + t*(P[j+1][1]-P[j][1])))
    k = 0
    while k < len(out) and len(out) > 4:
        a_, b_, c_ = out[k-1], out[k], out[(k+1) % len(out)]
        d = math.hypot(c_[0]-a_[0], c_[1]-a_[1]) or 1e-12
        if abs((b_[0]-a_[0])*(c_[1]-a_[1]) - (b_[1]-a_[1])*(c_[0]-a_[0])) / d < 0.015:
            out.pop(k)
        else:
            k += 1
    return out


def area(L):
    return 0.5*(sum(L[i][0]*L[(i+1) % len(L)][1]-L[(i+1) % len(L)][0]*L[i][1] for i in range(len(L))))


loops = []
for ln in contourpy.contour_generator(z=M).lines(0.5):
    pts = [(x0 + c/PX, y0 + r/PX) for c, r in ln]
    if len(pts) > 2 and math.hypot(pts[0][0]-pts[-1][0], pts[0][1]-pts[-1][1]) < 1e-6:
        pts = pts[:-1]
    if len(pts) < 4 or abs(area(pts)) < 0.3:
        continue
    P0 = np.array(pts); far = int(np.argmax(np.hypot(P0[:, 0]-P0[0, 0], P0[:, 1]-P0[0, 1])))
    if a.get("resample_mm"):
        s = minseg(resample(pts, float(a["resample_mm"])))   # на острых концах хорды короче шага — добрать
    else:
        s = minseg(dp(pts[:far+1], DPE)[:-1] + dp(pts[far:] + [pts[0]], DPE)[:-1])
    per = sum(math.hypot(s[(i+1) % len(s)][0]-s[i][0], s[(i+1) % len(s)][1]-s[i][1]) for i in range(len(s))) if len(s) > 2 else 0
    shortest = min(math.hypot(s[(i+1) % len(s)][0]-s[i][0], s[(i+1) % len(s)][1]-s[i][1]) for i in range(len(s))) if len(s) > 2 else 0
    if len(s) >= 3 and abs(area(s)) > 0.3 and per >= float(a.get("min_perimeter_mm", 5.0)) and shortest >= 0.8:
        loops.append(s)
# вложенность: глубина = сколько других контуров содержат точку контура
paths = [Path(np.array(L)) for L in loops]
depth = []
for i, L in enumerate(loops):
    pt = L[0]
    depth.append(sum(1 for j, p in enumerate(paths) if j != i and p.contains_point(pt)))
regions = []
for i, L in enumerate(loops):
    if depth[i] % 2 == 0:
        holes = [loops[j] for j in range(len(loops)) if depth[j] == depth[i] + 1 and paths[i].contains_point(loops[j][0])]
        # полость, пересекающая внешний контур или другую полость (после упрощения) — убрать
        ok = []
        for h in holes:
            hp = Path(np.array(h + [h[0]]))
            if Path(np.array(L + [L[0]])).intersects_path(hp, filled=False) or any(Path(np.array(o + [o[0]])).intersects_path(hp, filled=False) for o in ok):
                continue
            ok.append(h)
        holes = ok
        regions.append({"outer": [[round(x, 4), round(y, 4)] for x, y in L], "holes": [[[round(x, 4), round(y, 4)] for x, y in h] for h in holes]})
io.open(a["out_json"], "w", encoding="utf-8").write(json.dumps({"regions": regions}))
fig, ax = plt.subplots(figsize=(9, 9))
for P in polys:
    P = np.array(P); ax.plot(P[:, 0], P[:, 1], lw=0.3, color="#222")
for r in regions:
    verts = r["outer"] + [r["outer"][0]]; codes = [Path.MOVETO] + [Path.LINETO]*(len(r["outer"])-1) + [Path.CLOSEPOLY]
    for h in r["holes"]:
        verts += h + [h[0]]; codes += [Path.MOVETO] + [Path.LINETO]*(len(h)-1) + [Path.CLOSEPOLY]
    from matplotlib.patches import PathPatch
    ax.add_patch(PathPatch(Path(np.array(verts), codes), facecolor="#b8c4d0", edgecolor="none"))
ax.set_aspect("equal"); fig.savefig(a["preview_png"], dpi=160)
print("regions", len(regions), "loops", len(loops), "iters", it)
