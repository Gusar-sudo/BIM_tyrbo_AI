"""Раскрой ГКЛ на листы (без Revit). Вход: CSV кусков от gkl_pieces.py (panel_id;wall_id;layer;w_mm;h_mm).
Листы: ширина 1100, длина 2500 или 3000 (аргументы). Кусок ставится шириной поперёк листа, высотой вдоль (без поворота).
Укладка «колонками»: в листе кусок встаёт в колонку под предыдущий (если хватает длины) или новой колонкой рядом
(если хватает ширины); узкие куски — по два по ширине, короткие — по два по высоте. Сортировка по высоте убыв.,
лист выбирается с наименьшим остатком; новый лист — 2500, если кусок ≤ 2500, иначе 3000. Пропил — kerf_mm.
Кусок больше листа (шире 1100 или выше 3000) в раскрой не идёт — список «не помещается».
Выход: <out>_sheets.csv, <out>_pieces.csv, <out>_map.png, сводка в stdout.
Запуск: python -I gkl_cut.py pieces.csv out_prefix [sheet_w=1100] [lengths=2500,3000] [kerf_mm=0]
"""
import csv, io, sys

src, out = sys.argv[1], sys.argv[2]
SW = float(sys.argv[3]) if len(sys.argv) > 3 else 1100.0
LENS = [float(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "2500,3000").split(",")]
KERF = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
pieces = [dict(r, w=float(r["w_mm"]), h=float(r["h_mm"])) for r in csv.DictReader(io.open(src, encoding="utf-8-sig"), delimiter=";")]
big = [p for p in pieces if p["w"] > SW or p["h"] > max(LENS)]
ok = sorted([p for p in pieces if p not in big], key=lambda p: (-p["h"], -p["w"]))


class Sheet:
    def __init__(self, L):
        self.L = L; self.cols = []  # [x, width, used_h, [pieces]]

    def try_place(self, p, commit):
        best = None
        x_next = 0.0
        for c in self.cols:
            x_next = max(x_next, c[0] + c[1] + KERF)
            if p["w"] <= c[1] and c[2] + KERF + p["h"] <= self.L:
                waste = self.L - (c[2] + KERF + p["h"])
                if best is None or waste < best[0]:
                    best = (waste, "stack", c)
        if best is None and x_next + p["w"] <= SW and p["h"] <= self.L:
            best = (SW - x_next - p["w"], "col", x_next)
        if best and commit:
            if best[1] == "stack":
                c = best[2]; y = c[2] + KERF
                c[2] = y + p["h"]; c[3].append((p, c[0], y))
            else:
                self.cols.append([best[2], p["w"], p["h"], [(p, best[2], 0.0)]])
        return best

    def area_used(self):
        return sum(p["w"] * p["h"] for c in self.cols for (p, _, _) in c[3])


sheets = []
for p in ok:
    cand = [(s.try_place(p, False), s) for s in sheets]
    cand = [(b[0], s) for b, s in cand if b]
    if cand:
        min(cand, key=lambda t: t[0])[1].try_place(p, True)
    else:
        L = min([l for l in LENS if p["h"] <= l])
        s = Sheet(L); s.try_place(p, True); sheets.append(s)

by = {}
for s in sheets:
    by[s.L] = by.get(s.L, 0) + 1
area_pieces = sum(p["w"] * p["h"] for p in ok) / 1e6
area_sheets = sum(SW * s.L for s in sheets) / 1e6
with io.open(out + "_sheets.csv", "w", encoding="utf-8-sig") as f:
    f.write(u"sheet;length_mm;pieces;used_pct\n")
    for i, s in enumerate(sheets, 1):
        f.write(u"%d;%d;%d;%.1f\n" % (i, s.L, sum(len(c[3]) for c in s.cols), 100 * s.area_used() / (SW * s.L)))
with io.open(out + "_pieces.csv", "w", encoding="utf-8-sig") as f:
    f.write(u"panel_id;wall_id;layer;w_mm;h_mm;sheet;x_mm;y_mm\n")
    for i, s in enumerate(sheets, 1):
        for c in s.cols:
            for (p, x, y) in c[3]:
                f.write(u"%s;%s;%s;%d;%d;%d;%d;%d\n" % (p["panel_id"], p["wall_id"], p["layer"], p["w"], p["h"], i, x, y))
    for p in big:
        f.write(u"%s;%s;%s;%d;%d;НЕ ПОМЕЩАЕТСЯ;;\n" % (p["panel_id"], p["wall_id"], p["layer"], p["w"], p["h"]))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    n = len(sheets)
    fig, axs = plt.subplots(1, max(n, 1) + (1 if big else 0), figsize=(2.2 * (max(n, 1) + (1 if big else 0)), 6.4))
    axs = list(axs) if hasattr(axs, "__len__") else [axs]
    pal = ["#5DCAA5", "#85B7EB", "#F0997B", "#AFA9EC", "#FAC775", "#ED93B1", "#97C459", "#B4B2A9"]
    walls = sorted(set(p["wall_id"] for p in pieces))
    col_of = dict((w, pal[i % len(pal)]) for i, w in enumerate(walls))
    for i, s in enumerate(sheets):
        ax = axs[i]
        ax.add_patch(Rectangle((0, 0), SW, s.L, fc="#F1EFE8", ec="#444441", lw=1.5))
        for c in s.cols:
            for (p, x, y) in c[3]:
                ax.add_patch(Rectangle((x, y), p["w"], p["h"], fc=col_of[p["wall_id"]], ec="#2C2C2A", lw=0.8))
                ax.text(x + p["w"] / 2, y + p["h"] / 2, "%d×%d" % (p["w"], p["h"]), ha="center", va="center", fontsize=7, rotation=90 if p["w"] < 600 else 0)
        ax.set_xlim(-50, SW + 50); ax.set_ylim(-50, 3050); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("Лист %d\n1100×%d, %d%%" % (i + 1, s.L, round(100 * s.area_used() / (SW * s.L))), fontsize=9)
    if big:
        ax = axs[-1]; ax.axis("off")
        ax.text(0.5, 0.95, "Не помещается\nна лист:", ha="center", va="top", fontsize=9, color="#A32D2D", transform=ax.transAxes)
        for j, p in enumerate(big[:12]):
            ax.text(0.5, 0.82 - j * 0.06, "%d×%d" % (p["w"], p["h"]), ha="center", fontsize=8, color="#A32D2D", transform=ax.transAxes)
    fig.suptitle("Раскрой ГКЛ: листов %s; кусков %d (+%d не помещается); ГКЛ %.2f м² на листах %.2f м²" % (
        ", ".join("1100×%d — %d" % (L, by[L]) for L in sorted(by)), len(ok), len(big), area_pieces, area_sheets), fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out + "_map.png", dpi=130)
except ImportError:
    pass

print("листов:", ", ".join("1100x%d: %d" % (L, by[L]) for L in sorted(by)) or "0")
print("кусков в раскрое: %d; не помещается: %d" % (len(ok), len(big)))
print("площадь кусков %.2f м2, листов %.2f м2, отход %.1f%%" % (area_pieces, area_sheets, 100 * (1 - area_pieces / area_sheets) if area_sheets else 0))
