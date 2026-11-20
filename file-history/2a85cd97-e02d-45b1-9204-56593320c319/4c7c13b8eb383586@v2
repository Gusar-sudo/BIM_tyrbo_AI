# -*- coding: utf-8 -*-
# Пары «левый / правый» в НАЧАЛЕ стены (план, стена идёт слева направо, стекло справа от импоста).
# Проверено 14.11 по стенам библиотеки (край FSC21 «правый» в начале стены, зазор 3 мм): у вертикального импоста
# Revit кладёт профиль БЕЗ зеркала (+X профиля — по направлению стены): к стеклу в начале стены смотрит сторона +X («правый»), в конце — −X.
# py -P -E compose_left_right.py <pocket.json> <pairs.json> <out.png>
# pairs.json: [{"title", "left": тип, "right": тип, "note": подпись}]
import json, io, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams["font.family"] = "Segoe UI"
D = json.load(io.open(sys.argv[1], encoding="utf-8-sig"))
P = json.load(io.open(sys.argv[2], encoding="utf-8-sig"))
INK, MUT, GL, BODY, REAL = "#283040", "#6b7280", "#9fd3ef", "#d23c3c", "#8a8f98"
fig, axs = plt.subplots(len(P), 2, figsize=(12, 3.9 * len(P)), squeeze=False)
for ri, p in enumerate(P):
    face = 35.7 if p["left"].startswith(u"М3") else 30.6
    for ci, key in enumerate(("left", "right")):
        ax = axs[ri][ci]; r = D[p[key]]
        for s in r["nested"]: ax.plot([s[0], s[2]], [s[1], s[3]], color=REAL, lw=0.8)
        for s in r["own"]: ax.plot([s[0], s[2]], [s[1], s[3]], color=BODY, lw=1.5)
        xmax = max(v for s in r["own"] for v in (s[0], s[2]))
        x0 = xmax - 25
        for y0 in (-face, face - 8):
            ax.add_patch(Rectangle((x0, y0), 140 - x0, 8, color=GL, alpha=0.55, lw=0))
        ax.text(135, face + 4, u"стекло стены →", color="#3a86b8", fontsize=10, ha="right")
        ax.set_xlim(-110, 140); ax.set_ylim(-75, 70); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(u"%s «%s» в начале стены" % (p["title"], u"левый" if key == "left" else u"правый"), fontsize=12, color=INK, loc="left", fontweight="bold")
    if p.get("note"):
        axs[ri][0].text(-108, -73, p["note"], fontsize=10.5, color=INK, va="bottom")
fig.suptitle(u"Начало стены: какой тип смотрит пазом на стекло (план, стена идёт слева направо; в конце стены — наоборот)", fontsize=14, color=INK, x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.975))
fig.savefig(sys.argv[3], dpi=105, facecolor="white")
print("ok")

