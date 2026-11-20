# -*- coding: utf-8 -*-
# Лист-строка из картинок: python sheet_row.py out.png "подпись1=путь1" "подпись2=путь2" ...  (каждая обрезается по рисунку)
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
out = sys.argv[1]; items = [a.split("=", 1) for a in sys.argv[2:]]
W = 900
try:
    font = ImageFont.truetype("arial.ttf", 34)
except Exception:
    font = ImageFont.load_default()
tiles = []
for cap, p in items:
    im = Image.open(p).convert("L")
    bb = ImageOps.invert(im).getbbox()
    if bb:
        pad = 30; im = im.crop((max(0, bb[0]-pad), max(0, bb[1]-pad), min(im.width, bb[2]+pad), min(im.height, bb[3]+pad)))
    im.thumbnail((W, W)); t = Image.new("RGB", (W, W + 60), "white"); t.paste(im, ((W-im.width)//2, 60 + (W-im.height)//2))
    ImageDraw.Draw(t).text((10, 10), cap, fill="black", font=font); tiles.append(t)
sheet = Image.new("RGB", (W*len(tiles) + 10*(len(tiles)-1), W + 60), (200, 200, 200))
for i, t in enumerate(tiles):
    sheet.paste(t, (i*(W+10), 0))
sheet.save(out, quality=90)
