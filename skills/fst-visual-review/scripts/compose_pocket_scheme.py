# -*- coding: utf-8 -*-
# Схема «откуда считать 3 мм» у центральных столбов: настоящий паз (вложенная графика узла), 3D-тело профиля,
# полоса стекла 8 мм (пунктир — 10 мм), точка начала изменения паза, торец стекла по правилу 3 мм и сейчас.
# py compose_pocket_scheme.py <pocket_posts.json> <out.png>
import json, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams["font.family"] = "Segoe UI"
D = json.load(open(sys.argv[1], encoding="utf-8"))
INK, MUT = "#283040", "#6b7280"
GL, BODY, REAL, OK, NOW1, NOW2, BAD = "#9fd3ef", "#d23c3c", "#8a8f98", "#16a34a", "#ea8a00", "#7c3aed", "#d23c3c"
# тип, заголовок, грань стекла y, точка начала изменения (x, y), где паз меняется по высоте, торцы сейчас, окно
P = [
    (u"М2 FSC17 центральный с двухслойным остеклением", u"М2 FSC17 · столб три грани", -30.6, (17.9, None), u"дно паза ровное до y −17,9 (выше стекла 10 мм)",
     [(25.42, u"сейчас, стена со стойкой узкой", NOW1), (20.12, u"сейчас, стена со стойкой обычной", NOW2)], (10, 40, -42, -12)),
    (u"М2 FSC18 центральный с двухслойным остеклением", u"М2 FSC18 · столб универсальный", -30.6, (35.05, -31.09), u"паз клином: ножки держателя под 45°",
     [(38.26, u"сейчас, стена со стойкой узкой", NOW1), (32.96, u"сейчас, стена со стойкой обычной", NOW2)], (20, 52, -42, -12)),
    (u"М2 FSC22 центральный с двухслойным остеклением", u"М2 FSC22 · стойка усиленная", -30.6, (0.704, None), u"дно паза ровное до y −17,9",
     [(5.92, u"сейчас, стена со стойкой узкой", NOW1), (0.62, u"сейчас, стена со стойкой обычной", NOW2)], (-4, 22, -42, -12)),
    (u"М3 FSC04 центральный с двухслойным остеклением", u"М3 FSC04 · столб три грани", -35.7, (24.706, None), u"дно паза ровное до y −24,7 (выше стекла 10 мм)",
     [(34.62, u"сейчас, стена со стойкой узкой", NOW1), (27.8, u"сейчас, стена с нащельником Т", NOW2)], (18, 48, -46, -16)),
]
fig, axs = plt.subplots(2, 2, figsize=(16, 15))
fig.suptitle(u"Столбы: откуда считаем 3 мм (центральные, двухслойные; план у фасадного стекла, мм от оси столба)", fontsize=17, color=INK, x=0.04, ha="left", y=0.985)
fig.text(0.04, 0.95, u"Серое — настоящий паз (графика узла, как DWG). Красное — 3D-тело профиля. Голубое — стекло 8 мм, пунктир — 10 мм.\n"
         u"Зелёная точка — где паз начинает менять форму; зелёная линия — торец стекла по правилу 3 мм. Красная штриховка — стекло 8 мм заходит в 3D-тело.", fontsize=11, color=MUT)
HATCH = {u"М2 FSC17 центральный с двухслойным остеклением": (36.6, -25.6), u"М3 FSC04 центральный с двухслойным остеклением": (44.3, -30.7)}
for ax, (tn, title, face, (rx, ry), note, now, (x0, x1, y0, y1)) in zip(axs.ravel(), P):
    r = D[tn]
    for s in r["nested"]: ax.plot([s[0], s[2]], [s[1], s[3]], color=REAL, lw=1.0)
    for s in r["own"]: ax.plot([s[0], s[2]], [s[1], s[3]], color=BODY, lw=2.0)
    ex = rx + 3.0
    ax.add_patch(Rectangle((ex, face), x1 - ex, 8, color=GL, alpha=0.55, lw=0))
    ax.add_patch(Rectangle((ex, face), x1 - ex, 10, fill=False, ls="--", ec="#4a9cc8", lw=1.0))
    if tn in HATCH:
        hx, hy = HATCH[tn]
        ax.add_patch(Rectangle((ex, hy), hx - ex, face + 8 - hy, fill=False, hatch="////", ec=BAD, lw=0))
        ax.text((ex + hx) / 2, face + 8.6, u"3D-тело: паз только 5 мм — стекло 8/10 мм в теле", color=BAD, fontsize=9.5, ha="center")
    py = ry if ry is not None else face + 4
    ax.plot([rx], [py], "o", color=OK, ms=11, zorder=5)
    ax.plot([ex, ex], [face - 1.5, face + 11.5], color=OK, lw=2.6, zorder=4)
    ax.annotate("", xy=(rx, face - 2.5), xytext=(ex, face - 2.5), arrowprops=dict(arrowstyle="<->", color=OK, lw=1.8))
    ax.text((rx + ex) / 2, face - 3.6, u"3", color=OK, fontsize=14, ha="center", va="top", fontweight="bold")
    for k, (xv, lab, c) in enumerate(now):
        ax.plot([xv, xv], [face - 0.5, face + 10.5], color=c, lw=1.8, ls=(0, (4, 2)))
        ax.text(xv, face + 11 + k * 1.6, (u"%.1f" % xv).replace(".", ","), color=c, fontsize=10, ha="center")
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.grid(lw=0.25, color="#e5e7eb"); ax.tick_params(labelsize=8, colors=MUT)
    for sp in ax.spines.values(): sp.set_color("#d1d5db")
    ax.set_title(title, fontsize=14, color=INK, loc="left", fontweight="bold")
    ax.text(x0 + 0.5, y0 + 0.8, u"Точка отсчёта: x = %s мм от оси. %s.\nТорец стекла по правилу: %s мм от оси." %
            ((u"%.2f" % rx).replace(".", ","), note, (u"%.2f" % ex).replace(".", ",")), fontsize=10, color=INK, va="bottom",
            bbox=dict(fc="white", ec="#d1d5db"))
h = [plt.Line2D([], [], color=NOW1, ls="--", lw=1.8, label=u"торец стекла сейчас: стена со стойкой узкой"),
     plt.Line2D([], [], color=NOW2, ls="--", lw=1.8, label=u"торец стекла сейчас: стена со стойкой обычной / нащельник Т (М3)"),
     plt.Line2D([], [], color=OK, lw=2.6, label=u"торец стекла по правилу 3 мм от точки отсчёта"),
     plt.Line2D([], [], color=BODY, lw=2, label=u"3D-тело профиля"), plt.Line2D([], [], color=REAL, lw=1, label=u"настоящий паз (графика узла)")]
fig.legend(handles=h, loc="lower left", ncol=2, fontsize=11, frameon=False, bbox_to_anchor=(0.04, 0.0))
fig.tight_layout(rect=(0.02, 0.05, 1, 0.94))
fig.savefig(sys.argv[2], dpi=150)
print("ok")
