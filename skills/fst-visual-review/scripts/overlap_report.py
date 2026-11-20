# -*- coding: utf-8 -*-
# Локально: по сечениям (node_section_loops.py) — наложение стекла/уплотнителя на металл импоста:
# площадь, «глубина» (толщина наложения = 2 × число шагов эрозии до исчезновения), место; картинка: общий вид + крупно.
# py -P -E overlap_report.py <out.png> <title> sec1.json[=Подпись] sec2.json[=Подпись] ...
import json, io, sys, math
import numpy as np
from PIL import Image, ImageDraw
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Segoe UI"
OUT, TITLE = sys.argv[1:3]
items = [a.split("=", 1) if "=" in a else (a, a) for a in sys.argv[3:]]
PX = 50; X0, Y0, X1, Y1 = -70, -50, 70, 50; W = (X1 - X0) * PX; H = (Y1 - Y0) * PX
tp = lambda p: ((p[0] - X0) * PX, (Y1 - p[1]) * PX)


def mk(d, sel):
    A = np.zeros((H, W), bool)
    for it in d["items"]:
        if not sel(it["mat"]): continue
        B = np.zeros((H, W), np.uint8)
        for l in it["loops"]:
            t = Image.new("1", (W, H), 0); ImageDraw.Draw(t).polygon([tp(p) for p in l], fill=1); B ^= np.asarray(t, np.uint8)
        A |= B.astype(bool)
    return A


def depth(M):
    k = 0
    while M.any() and k < 500:
        E = M.copy(); E[1:, :] &= M[:-1, :]; E[:-1, :] &= M[1:, :]; E[:, 1:] &= M[:, :-1]; E[:, :-1] &= M[:, 1:]; M = E; k += 1
    return 2.0 * k / PX


rows = []
fig, axs = plt.subplots(len(items), 2, figsize=(14, 6.2 * len(items)))
axs = np.atleast_2d(axs)
for row, (path, label) in zip(axs, items):
    d = json.load(io.open(path, encoding="utf-8"))
    A = mk(d, lambda m: u"Алюм" in m); G = mk(d, lambda m: u"Стекл" in m); S = mk(d, lambda m: u"Уплотн" in m)
    og, os_ = A & G, A & S
    a = 1.0 / PX / PX
    r = {"label": label, "glass_mm2": round(og.sum() * a, 2), "glass_depth_mm": round(depth(og), 2), "seal_mm2": round(os_.sum() * a, 2), "seal_depth_mm": round(depth(os_), 2)}
    ys, xs = np.nonzero(og | os_)
    img = np.full((H, W, 3), 255, np.uint8)
    img[A] = (169, 184, 199); img[G] = (169, 220, 239); img[S] = (40, 44, 52); img[og] = (220, 30, 30); img[os_] = (245, 130, 20)
    ext = [X0, X1, Y0, Y1]
    ax = row[0]; ax.imshow(img, extent=ext); ax.set_xlim(-45, 45); ax.set_ylim(-42, 42); ax.set_aspect("equal"); ax.grid(lw=0.3)
    ax.set_title(u"%s — общий вид" % label, loc="left", fontsize=11)
    ax = row[1]; ax.imshow(img, extent=ext); ax.set_aspect("equal"); ax.grid(lw=0.3)
    ys, xs = np.nonzero(og)
    if len(xs):
        # самое большое пятно наложения стекла: размеры по X и Y = насколько стекло заходит в металл
        im_ = Image.fromarray(og.astype(np.int32), mode="I"); lab = 2; best = None
        while True:
            arr = np.asarray(im_); z = np.flatnonzero(arr == 1)
            if not len(z) or lab > 300: break
            y_, x_ = divmod(int(z[0]), W); ImageDraw.floodfill(im_, (x_, y_), lab, thresh=0)
            c = np.asarray(im_) == lab; n = c.sum()
            if best is None or n > best[0]: best = (n, c)
            lab += 1
        cy_, cx_ = np.nonzero(best[1])
        bx0, bx1 = X0 + cx_.min() / PX, X0 + (cx_.max() + 1) / PX; by0, by1 = Y1 - (cy_.max() + 1) / PX, Y1 - cy_.min() / PX
        r["spot_mm"] = [round(bx1 - bx0, 2), round(by1 - by0, 2)]
        cx = (bx0 + bx1) / 2; cy = (by0 + by1) / 2; hw = max(3.0, (bx1 - bx0), (by1 - by0)) * 1.2
        ax.set_xlim(cx - hw, cx + hw); ax.set_ylim(cy - hw, cy + hw)
        ax.add_patch(plt.Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, ec="#b91c1c", lw=1.5))
        ax.annotate(u"%.2f × %.2f мм" % (bx1 - bx0, by1 - by0), (bx1, by1), xytext=(cx + hw * 0.15, cy + hw * 0.75), fontsize=13, color="#b91c1c",
                    arrowprops=dict(arrowstyle="->", color="#b91c1c"))
        row[0].add_patch(plt.Rectangle((cx - hw, cy - hw), 2 * hw, 2 * hw, fill=False, ec="#c0392b", lw=1.5))
        ax.set_title(u"крупно: стекло заходит в металл на %.2f мм (пятно %.2f × %.2f мм)" % (min(bx1 - bx0, by1 - by0), bx1 - bx0, by1 - by0), loc="left", fontsize=12)
    else:
        ax.set_title(u"стекло в металл не заходит", loc="left", fontsize=12)
    rows.append(r)
fig.suptitle(TITLE + u"\nсерое — металл (новое тело), голубое — стекло, чёрное — уплотнитель, КРАСНОЕ — стекло в металле, оранжевое — уплотнитель в металле", fontsize=12, x=0.01, ha="left")
fig.savefig(OUT, dpi=110, bbox_inches="tight", facecolor="white")
print(json.dumps(rows, ensure_ascii=False))
