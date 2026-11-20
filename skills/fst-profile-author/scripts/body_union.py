# -*- coding: utf-8 -*-
# Тело (собственный контур) углового профиля с держателем — объединение контуров вне Revit.
# Вход: дамп контуров групп вложенной графики (nested_loops.py) для 90° левого + контур держателя из DWG.
# Для каждого угла: держатель и рейка стены B поворачиваются на (угол-90)° вокруг центра круга,
# всё растеризуется (px_mm точек на мм), объединяется, обводится (marching squares), упрощается
# (Дуглас-Пекер + отрезки >= min_seg), крайние точки стороны A прижимаются к исходным.
# Выход: JSON {angle: [loops]} + PNG-превью (части тонко, итог толсто).
import json, math, sys, io
import numpy as np
from PIL import Image, ImageDraw
import contourpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

a = json.load(io.open(sys.argv[1], encoding="utf-8-sig"))
loops_dump = json.load(io.open(a["loops_json"], encoding="utf-8"))
H = json.load(io.open(a["holder_json"], encoding="utf-8"))["segs"] if a.get("holder_json") else []
PX = float(a.get("px_mm", 40)); MINS = float(a.get("min_seg_mm", 0.85)); DP = float(a.get("dp_mm", 0.03))


def arc3(p1, pm, p2, step=3.0):
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


def holder_loop():
    segs = []
    for s in H:
        if s[0] == "L":
            segs.append(((s[1], s[2]), (s[3], s[4])))
        else:
            ps = arc3(s[1:3], s[3:5], s[5:7]); segs += [(ps[i], ps[i+1]) for i in range(len(ps)-1)]
    rest = segs[1:]; ch = [segs[0][0], segs[0][1]]
    while rest:
        for i, (p, q) in enumerate(rest):
            if math.hypot(p[0]-ch[-1][0], p[1]-ch[-1][1]) < 0.005:
                ch.append(q); rest.pop(i); break
            if math.hypot(q[0]-ch[-1][0], q[1]-ch[-1][1]) < 0.005:
                ch.append(p); rest.pop(i); break
        else:
            break
    return ch[:-1]


g = {}
for grp in loops_dump["groups"]:
    g.setdefault(grp["name"], []).append(grp)


def outer(grp):
    cl = [l for l in grp["loops"] if l["closed"]]
    return max(cl, key=lambda l: l["area"])["pts"]


vit = [outer(x) for x in g[a.get("vitr_group", "FS.C-24")]]
# рейка B — та, что ниже (по -y), рейка A — по -x
vB = min(vit, key=lambda L: np.mean([p[1] for p in L])); vA = [L for L in vit if L is not vB]
# неподвижные детали (сторона A) и поворачиваемые вместе со стеной B
fixed = [outer(x) for n in a.get("fixed_groups", ["FS.C-05"]) for x in g[n]] + vA
rotp = [outer(x) for n in a.get("rot_groups", []) for x in g[n]] + [vB]
if a.get("holder_json"):
    rotp.append(holder_loop())        # М3: держатель FS.C-06 из DWG (во вложенной графике он не замкнут)
A_minx = min(p[0] for L in fixed for p in L)


def rot(L, t):
    c, s = math.cos(t), math.sin(t); return [(x*c-y*s, x*s+y*c) for x, y in L]


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


def minseg(pts, dirs=()):
    """слить отрезки короче MINS; точки на крайних позициях по направлениям dirs (край стены — подрезка стекла)
    не двигаются: при слиянии остаётся защищённая точка, а не середина."""
    out = list(pts)
    def prot_set(o):
        s = set()
        for d in dirs:
            pr = [p[0]*d[0]+p[1]*d[1] for p in o]; m = max(pr)
            s |= set(i for i, v in enumerate(pr) if v > m - 0.02)
        return s
    changed = True
    while changed and len(out) > 4:
        changed = False; prot = prot_set(out)
        for i in range(len(out)):
            j = (i+1) % len(out); p, q = out[i], out[j]
            if math.hypot(q[0]-p[0], q[1]-p[1]) < MINS:
                out[i] = p if i in prot else (q if j in prot else ((p[0]+q[0])/2, (p[1]+q[1])/2))
                out.pop(j); changed = True; break
    return out


res = {}; previews = []
for ang in a["angles"]:
    t = math.radians(ang-90)
    # точный круг столба: дуги в выгрузке вложенной графики разбиты грубо (хорды внутри круга)
    R = float(a.get("circle_r_mm", 41.7))
    disc = [(R*math.cos(2*math.pi*k/720), R*math.sin(2*math.pi*k/720)) for k in range(720)]
    # со стороны A столб плоский (грань под рейку A): круг дальше этой грани не выходит, иначе лишняя дуга
    XC = float(a.get("disc_min_x_mm", -1e9))
    disc = [(max(x, XC), y) for x, y in disc]
    parts = [disc] + fixed + [rot(L, t) for L in rotp]
    allp = np.array([p for L in parts for p in L])
    x0, y0 = allp.min(0) - 1.0; x1, y1 = allp.max(0) + 1.0
    W = int((x1-x0)*PX)+1; Hh = int((y1-y0)*PX)+1
    img = Image.new("1", (W, Hh), 0); dr = ImageDraw.Draw(img)
    for L in parts:
        dr.polygon([((x-x0)*PX, (y-y0)*PX) for x, y in L], fill=1, outline=1)
    M = np.array(img, dtype=float)
    gen = contourpy.contour_generator(z=M, line_type="SeparateCode" if False else "Separate")
    lines = gen.lines(0.5)
    loops = []
    for ln in lines:
        pts = [(x0 + c/PX, y0 + r/PX) for c, r in ln]
        if len(pts) > 2 and math.hypot(pts[0][0]-pts[-1][0], pts[0][1]-pts[-1][1]) < 1e-6:
            pts = pts[:-1]
        ar = 0.5*abs(sum(pts[i][0]*pts[(i+1) % len(pts)][1]-pts[(i+1) % len(pts)][0]*pts[i][1] for i in range(len(pts))))
        if ar < 1.0:
            continue
        # замкнутый контур: делим на две ветви по самой дальней от первой точке, упрощаем каждую
        P0 = np.array(pts); far = int(np.argmax(np.hypot(P0[:, 0]-P0[0, 0], P0[:, 1]-P0[0, 1])))
        dB = (math.sin(t), -math.cos(t))       # направление стены B: (0,-1), повёрнутое на t
        s = minseg(dp(pts[:far+1], DP)[:-1] + dp(pts[far:] + [pts[0]], DP)[:-1], [(-1, 0), dB])
        # прижать сторону A к исходному краю (от него зависит подрезка стекла)
        s = [(A_minx if abs(x-A_minx) < 0.1 else x, y) for x, y in s]
        loops.append([[round(x, 4), round(y, 4)] for x, y in s])
    res[str(ang)] = loops
    previews.append((ang, parts, loops))

io.open(a["out_json"], "w", encoding="utf-8").write(json.dumps(res))
fig, axs = plt.subplots(1, len(previews), figsize=(5*len(previews), 5))
axs = np.atleast_1d(axs)
for ax, (ang, parts, loops) in zip(axs, previews):
    for L in parts:
        P = np.array(L + [L[0]]); ax.plot(P[:, 0], P[:, 1], lw=0.4, color="#888")
    for L in loops:
        P = np.array(L + [L[0]]); ax.plot(P[:, 0], P[:, 1], lw=1.2, color="#c0392b")
    ax.set_aspect("equal"); ax.set_title(u"%d°: контуров %d, точек %s" % (ang, len(loops), [len(l) for l in loops]))
fig.tight_layout(); fig.savefig(a["preview_png"], dpi=150)
print(json.dumps({k: [len(l) for l in v] for k, v in res.items()}), "A_minx", A_minx)
