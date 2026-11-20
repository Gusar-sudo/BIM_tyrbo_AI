# -*- coding: utf-8 -*-
# Лист «было / стало»: строки — before / after, колонки — набор картинок (по имени). Обрезает белые поля.
# py -P -E before_after_grid.py <dir> <out.png> "<title>" tag1=Подпись1 tag2=Подпись2 ...
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageChops
D, OUT, TITLE = sys.argv[1:4]
cols = [a.split("=", 1) for a in sys.argv[4:]]
F = lambda s: ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", s)
FB = lambda s: ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", s)
CW, CH, PAD, LW = 520, 440, 16, 110


def load(p):
    im = Image.open(p).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bb = ImageChops.difference(im, bg).getbbox()
    if bb: im = im.crop((max(0, bb[0] - 10), max(0, bb[1] - 10), min(im.width, bb[2] + 10), min(im.height, bb[3] + 10)))
    im.thumbnail((CW - 2 * PAD, CH - 2 * PAD), Image.LANCZOS)
    return im


W = LW + CW * len(cols); H = 90 + 40 + CH * 2
sheet = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(sheet)
dr.text((PAD, 20), TITLE, font=F(30), fill=(31, 41, 51))
for j, (tag, lab) in enumerate(cols):
    dr.text((LW + j * CW + PAD, 92), lab, font=FB(20), fill=(31, 41, 51))
for i, (pre, lab) in enumerate((("before", u"было"), ("after", u"стало"))):
    y = 130 + i * CH
    dr.text((PAD, y + CH // 2 - 16), lab, font=FB(26), fill=(36, 57, 77) if i else (110, 117, 128))
    for j, (tag, _) in enumerate(cols):
        x = LW + j * CW
        dr.rectangle([x + 4, y + 4, x + CW - 4, y + CH - 4], outline=(213, 217, 224), width=2)
        p = os.path.join(D, pre + "_" + tag + ".png")
        if os.path.exists(p):
            im = load(p); sheet.paste(im, (x + (CW - im.width) // 2, y + (CH - im.height) // 2))
sheet.save(OUT)
print(OUT, sheet.size)
