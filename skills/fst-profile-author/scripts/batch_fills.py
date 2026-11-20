# -*- coding: utf-8 -*-
# Пакетный расчёт заливок «алюминий» (fill_mask.py) для всех выгруженных профилей + лист превью для проверки глазами.
# python batch_fills.py <curves_dir> <fills_dir> <preview_dir>
import json, io, os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
CD, FD, PD = sys.argv[1:4]
FM = r"C:\Users\user\Desktop\Фристайл\_bim\batches\M2_C\fill_mask.py"
for d in (FD, PD):
    os.makedirs(d, exist_ok=True)
names = [f[:-5] for f in os.listdir(CD) if f.endswith(".json") and not f.startswith("_")]


def run(n):
    a = {"curves_json": os.path.join(CD, n + ".json"), "out_json": os.path.join(FD, n + ".json"), "preview_png": os.path.join(PD, n + ".png"),
         "px_mm": 20, "thick_r_mm": 1.2, "line_w_px": 7, "grow_px": 4, "resample_mm": 0.9, "min_perimeter_mm": 9}
    ap = os.path.join(FD, n + ".args.json")
    io.open(ap, "w", encoding="utf-8").write(json.dumps(a, ensure_ascii=False))
    p = subprocess.run([sys.executable, FM, ap], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return n, p.returncode, (p.stdout.strip() or p.stderr.strip()[-200:])


with ThreadPoolExecutor(6) as ex:
    res = list(ex.map(run, names))
bad = [r for r in res if r[1] != 0]
io.open(os.path.join(FD, "_report.json"), "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
# лист превью: сетка 6 колонок
ok = sorted(r[0] for r in res if r[1] == 0)
W = 420; cols = 6
try:
    font = ImageFont.truetype("arial.ttf", 14)
except Exception:
    font = ImageFont.load_default()
pages = [ok[i:i + 36] for i in range(0, len(ok), 36)]
for pi, page in enumerate(pages):
    rows = (len(page) + cols - 1) // cols
    sh = Image.new("RGB", (cols * W, rows * (W + 40)), "white")
    for k, n in enumerate(page):
        im = Image.open(os.path.join(PD, n + ".png")).convert("RGB"); im.thumbnail((W, W))
        x, y = (k % cols) * W, (k // cols) * (W + 40)
        sh.paste(im, (x, y + 36))
        ImageDraw.Draw(sh).text((x + 4, y + 4), n.replace("BIMLIB_Профиль_", "").replace("_ФристайлТехнолоджи", "")[:52], fill="black", font=font)
    sh.save(os.path.join(PD, "_лист_%02d.jpg" % (pi + 1)), quality=85)
print("ok", len(ok), "bad", len(bad), "pages", len(pages))
for b in bad[:20]:
    print(b)
