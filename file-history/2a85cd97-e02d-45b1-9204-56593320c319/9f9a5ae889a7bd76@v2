# -*- coding: utf-8 -*-
# Сборка PNG flex-теста в PDF: страница на тип стены, 4 вида 2x2 + подпись типа и итог.
import json, os, sys, glob
from PIL import Image, ImageDraw, ImageFont

D = sys.argv[1]
types = []
for f in sorted(glob.glob(os.path.join(D, "result_*.json"))):
    with open(f, encoding="utf-8") as fh:
        types += json.load(fh)["types"]
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
W, H = 3508, 2480  # A4 альбом 300 dpi
pages = []
labels = [u"3D «Низкая»", u"3D «Высокая»", u"Фасад 1:50", u"План 1:20 (типовая 3000)"]
for i, t in enumerate(types):
    tag = "%02d" % (i + 1)
    pg = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(pg)
    note = u"PASS" if t.get("pass") else u"FAIL"
    if all(s.get("panels") == [u"Пусто"] for s in t["sizes"]):
        note = u"не применимо (пустые панели, без импостов)"
    dr.text((80, 50), u"%s  %s" % (tag, t["wall_type"]), fill="black", font=font)
    dr.text((80, 100), u"Итог: %s;  размеры: %s" % (note, ", ".join(s["size"] for s in t["sizes"])), fill="black", font=small)
    files = sorted(glob.glob(os.path.join(D, tag + "_*.png")))
    cw, ch = (W - 240) // 2, (H - 260) // 2
    for k, fp in enumerate(files[:4]):
        im = Image.open(fp).convert("RGB"); im.thumbnail((cw, ch - 50))
        x = 80 + (k % 2) * (cw + 80); y = 160 + (k // 2) * (ch + 20)
        dr.text((x, y), labels[k], fill="black", font=small)
        pg.paste(im, (x, y + 40))
        dr.rectangle([x - 4, y + 36, x + cw, y + ch - 10], outline=(200, 200, 200))
    pages.append(pg)
out = os.path.join(D, "flex_M2M3.pdf")
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=300)
print(out, len(pages))
