# -*- coding: utf-8 -*-
# Схема «откуда считать 3 мм» по сторонам прочих столбов: сторона поворачивается так, что стекло входит слева.
# Серое — паз (графика узла), красное — 3D-тело, голубое — стекло 8 мм (пунктир 10 мм), зелёное — точка отсчёта и торец по правилу.
# Точка отсчёта — самое мелкое касание паза в полосе стекла 10 мм (без кромки держателя).
# py -P -E compose_pocket_sides.py <pocket.json> <sides.json> <out.png>
# sides.json: [{"type": имя, "side": "-X|+X|-Y|+Y", "title": подпись, "also": "где ещё так же"}]
import json, io, sys, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams["font.family"] = "Segoe UI"
D = json.load(io.open(sys.argv[1], encoding="utf-8"))
S = json.load(io.open(sys.argv[2], encoding="utf-8-sig"))
INK, MUT, GL, BODY, REAL, OK = "#283040", "#6b7280", "#9fd3ef", "#d23c3c", "#8a8f98", "#16a34a"
MAP = {"-X": lambda x, y: (x, y), "+X": lambda x, y: (-x, y), "-Y": lambda x, y: (y, x), "+Y": lambda x, y: (-y, x)}


def tr(segs, f):
    out = []
    for s in segs:
        a = f(s[0], s[1]); b = f(s[2], s[3]); out.append((a[0], a[1], b[0], b[1]))
    return out


def hit(segs, lat):
    best = None
    for s in segs:
        if (s[1] - lat) * (s[3] - lat) > 0 or s[1] == s[3]:
            continue
        v = s[0] + (lat - s[1]) / (s[3] - s[1]) * (s[2] - s[0])
        if v < 0 and (best is None or v < best):
            best = v
    return best


res = []
cols = 3; rows = int(math.ceil(len(S) / float(cols)))
fig, axs = plt.subplots(rows, cols, figsize=(cols * 6.4, rows * 6.6))
axs = [a for r in axs for a in r] if rows > 1 else list(axs)
for ax in axs: ax.axis("off")
for ax, it in zip(axs, S):
    r = D[it["type"]]; f = MAP[it["side"]]
    face = 35.7 if it["type"].startswith(u"М3") else 30.6
    nest = tr(r["nested"], f); own = tr(r["own"], f)
    outer = -min(min(s[0], s[2]) for s in own)
    best = None
    for k in range(41):
        lat = -face + k * 0.25
        v = hit(nest, lat)
        if v is None or -v > outer - 1.0: continue
        if best is None or -v > best[0] + 1e-6: best = (-v, lat)
    ref, rl = best; ex = ref + 3.0
    res.append({"type": it["type"], "side": it["side"], "ref_mm": round(ref, 2), "ref_lat": round(rl, 2), "glass_end_mm": round(ex, 2)})
    ax.axis("on")
    for s in nest: ax.plot([s[0], s[2]], [s[1], s[3]], color=REAL, lw=1.0)
    for s in own: ax.plot([s[0], s[2]], [s[1], s[3]], color=BODY, lw=1.8)
    x0, x1 = -(ex + 22), -(ref - 9); y0, y1 = -face - 7, -face + 15
    ax.add_patch(Rectangle((x0, -face), (-ex) - x0, 8, color=GL, alpha=0.55, lw=0))
    ax.add_patch(Rectangle((x0, -face), (-ex) - x0, 10, fill=False, ls="--", ec="#4a9cc8", lw=1.0))
    ax.plot([-ref], [rl], "o", color=OK, ms=10, zorder=5)
    ax.plot([-ex, -ex], [-face - 1.5, -face + 11.5], color=OK, lw=2.6, zorder=4)
    ax.annotate("", xy=(-ref, -face - 2.5), xytext=(-ex, -face - 2.5), arrowprops=dict(arrowstyle="<->", color=OK, lw=1.8))
    ax.text(-(ref + ex) / 2, -face - 3.4, "3", color=OK, fontsize=14, ha="center", va="top", fontweight="bold")
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.grid(lw=0.25, color="#e5e7eb")
    ax.tick_params(labelsize=8, colors=MUT)
    ax.set_title(it["title"], fontsize=13, color=INK, loc="left", fontweight="bold")
    ax.text(x0 + 0.6, y1 - 0.6, (u"Точка отсчёта %s мм от оси столба\nТорец стекла по правилу %s мм\n%s" % (
        (u"%.2f" % ref).replace(".", ","), (u"%.2f" % ex).replace(".", ","), it.get("also", u""))).strip(),
        fontsize=10, color=INK, va="top", bbox=dict(fc="white", ec="#d1d5db"))
fig.suptitle(u"Прочие столбы: откуда считаем 3 мм (двухслойные, одно стекло стороны, стекло входит слева; мм от оси столба)", fontsize=16, color=INK, x=0.02, ha="left")
h = [plt.Line2D([], [], color=OK, lw=2.6, label=u"торец стекла по правилу 3 мм"), plt.Line2D([], [], color=OK, marker="o", ls="", label=u"где паз начинает менять форму"),
     plt.Line2D([], [], color=BODY, lw=2, label=u"3D-тело профиля"), plt.Line2D([], [], color=REAL, lw=1, label=u"паз (графика узла)"),
     Rectangle((0, 0), 1, 1, color=GL, alpha=0.55, label=u"стекло 8 мм (пунктир — 10 мм)")]
fig.legend(handles=h, loc="lower left", ncol=5, fontsize=11, frameon=False, bbox_to_anchor=(0.02, 0.0))
fig.tight_layout(rect=(0, 0.04, 1, 0.96))
fig.savefig(sys.argv[3], dpi=120, facecolor="white")
io.open(sys.argv[3][:-4] + ".json", "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
for x in res: print(x["type"], x["side"], x["ref_mm"], x["ref_lat"], x["glass_end_mm"])
