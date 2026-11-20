# -*- coding: utf-8 -*-
# Цветные варианты одного узла: заливки из сечения Revit (node_section_loops.py: алюминий/стекло/уплотнитель)
# + линии графики узла из curves JSON профиля (batches\color\curves). Варианты палитры — в JSON.
# py -P -E node_palette_png.py section.json curves.json palettes.json out.png [--win=-60,-45,60,45] [--flip_y] [--title=..]
import sys, json, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.family"] = "Segoe UI"
sec = json.load(open(sys.argv[1], encoding="utf-8"))
crv = json.load(open(sys.argv[2], encoding="utf-8"))
pals = json.load(open(sys.argv[3], encoding="utf-8-sig"))
out = sys.argv[4]
opt = dict(a.lstrip("-").split("=", 1) if "=" in a else (a.lstrip("-"), "1") for a in sys.argv[5:])
x0, y0, x1, y1 = [float(v) for v in opt.get("win", "-60,-45,60,45").split(",")]
ky = -1 if "flip_y" in opt else 1


def kind(m):
    m = m.lower()
    if u"стекл" in m: return "glass"
    if u"уплотн" in m or "epdm" in m: return "seal"
    if u"гкл" in m or u"гипс" in m: return "gkl"
    return "alu"


def path_of(loops):
    v, c = [], []
    for l in loops:
        if len(l) < 3: continue
        v += [tuple(p) for p in l] + [tuple(l[0])]
        c += [MPath.MOVETO] + [MPath.LINETO] * (len(l) - 1) + [MPath.CLOSEPOLY]
    return MPath(v, c)


def arc_pts(a, b, m, n=24):
    # дуга через три точки
    ax, ay = a; bx, by = m; cx, cy = b
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9: return [a, b]
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    t0 = math.atan2(ay - uy, ax - ux); tm = math.atan2(by - uy, bx - ux); t1 = math.atan2(cy - uy, cx - ux)
    def norm(t): return (t - t0) % (2 * math.pi)
    sweep = norm(t1)
    if norm(tm) > sweep: sweep -= 2 * math.pi
    return [(ux + r * math.cos(t0 + sweep * i / n), uy + r * math.sin(t0 + sweep * i / n)) for i in range(n + 1)]


segs = []
for g in crv["groups"]:
    for c in g["curves"]:
        if c[0] == "L":
            segs.append([(c[1], c[2] * ky), (c[3], c[4] * ky)])
        elif c[0] == "A":
            segs.append([(p[0], p[1] * ky) for p in arc_pts((c[1], c[2]), (c[5], c[6]), (c[3], c[4]))])
order = {"glass": 0, "gkl": 0, "alu": 1, "seal": 2}
items = sec["items"]
if opt.get("fills"):
    # алюминий — из заливки по линиям графики (fill_parity.py), а не из 3D-тела
    fr = json.load(open(opt["fills"], encoding="utf-8"))["regions"]
    items = [it for it in items if kind(it["mat"]) != "alu"]
    items += [{"mat": u"алюминий", "loops": [[[p[0], p[1] * ky] for p in l] for l in [r["outer"]] + r["holes"]]} for r in fr]
items = sorted(items, key=lambda it: order[kind(it["mat"])])
fig, axs = plt.subplots(1, len(pals), figsize=(5.6 * len(pals), 5.2))
if len(pals) == 1: axs = [axs]
for ax, pl in zip(axs, pals):
    ax.set_facecolor(pl.get("bg", "#ffffff"))
    for it in items:
        k = kind(it["mat"])
        ax.add_patch(PathPatch(path_of(it["loops"]), fc=pl[k], ec=pl.get(k + "_edge", "none"),
                               lw=pl.get("lw_edge", 0.6), alpha=pl.get(k + "_alpha", 1), zorder=order[k] + 1))
    for s in segs:
        xs, ys = zip(*s)
        ax.plot(xs, ys, color=pl["line"], lw=pl.get("lw", 0.5), zorder=5, solid_capstyle="round")
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#d5d9e0")
    ax.set_title(pl["name"], fontsize=13, loc="left", color="#1f2933", fontweight="bold")
    ax.text(0, -0.04, pl.get("note", ""), transform=ax.transAxes, fontsize=9.5, color="#4b5563", va="top", wrap=True)
    sw = [("alu", u"алюминий"), ("seal", u"уплотнитель"), ("glass", u"стекло")]
    for i, (k, lab) in enumerate(sw):
        ax.add_patch(plt.Rectangle((0.02 + i * 0.32, 0.92), 0.05, 0.05, transform=ax.transAxes, fc=pl[k], ec="#6b7280", lw=0.4, zorder=9))
        ax.text(0.085 + i * 0.32, 0.945, lab, transform=ax.transAxes, fontsize=9, va="center", color="#1f2933", zorder=9)
if opt.get("title"):
    fig.suptitle(opt["title"], fontsize=15, x=0.01, ha="left", color="#1f2933")
fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
print("ok", out, len(items), len(segs))
