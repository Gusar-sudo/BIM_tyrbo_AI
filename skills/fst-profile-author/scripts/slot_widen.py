# Найти в силуэтах пазы под стекло (две параллельные осевые линии на расстоянии ~5 мм + торцевая перемычка ~5 мм)
# и рассчитать перенос внутренней стороны паза к оси профиля на WIDEN мм (место под уплотнитель панели).
# Вход: silhouettes18.json, список профилей; выход: moves.json {profile: [[x,y,nx,ny],...]} и картинка до/после.
import json, sys, math
from PIL import Image, ImageDraw, ImageFont
src, names_csv, out_json, out_png = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
WIDEN = 10.1; GAP = 5.0; TOL = 0.35
data = json.load(open(src, encoding="utf-8"))
names = [n for n in names_csv.split("|") if n]


def key(p):
    return (round(p[0], 2), round(p[1], 2))


res = {}
for n in names:
    lines = [c["p"] for c in data[n]["curves"] if c["t"] == "line"]
    segs = []
    for a, b in lines:
        if abs(a[1] - b[1]) < 0.05:
            segs.append(("h", a[1], min(a[0], b[0]), max(a[0], b[0]), a, b))
        elif abs(a[0] - b[0]) < 0.05:
            segs.append(("v", a[0], min(a[1], b[1]), max(a[1], b[1]), a, b))
    moves = {}
    slots = []
    for i, s in enumerate(segs):
        for j, t in enumerate(segs):
            if j <= i or s[0] != t[0] or abs(abs(s[1] - t[1]) - GAP) > TOL:
                continue
            ov = min(s[3], t[3]) - max(s[2], t[2])
            if ov < 8:
                continue
            # перемычка: перпендикулярный отрезок длиной ~GAP, соединяющий концы s и t
            ends_s = [key(s[4]), key(s[5])]; ends_t = [key(t[4]), key(t[5])]
            closer = None
            for u in segs:
                if u[0] == s[0] or abs((u[3] - u[2]) - GAP) > TOL:
                    continue
                ue = [key(u[4]), key(u[5])]
                if any(e in ends_s for e in ue) and any(e in ends_t for e in ue):
                    closer = u
            if closer is None:
                continue
            inner, outer = (s, t) if abs(s[1]) < abs(t[1]) else (t, s)
            sgn = -1 if inner[1] > 0 else 1
            for p in (inner[4], inner[5]):
                k = key(p)
                if inner[0] == "h":
                    moves[k] = [p[0], p[1], p[0], p[1] + sgn * WIDEN]
                else:
                    moves[k] = [p[0], p[1], p[0] + sgn * WIDEN, p[1]]
            slots.append([inner[0], round(inner[1], 2), round(outer[1], 2), round(inner[2], 1), round(inner[3], 1)])
    res[n] = {"moves": list(moves.values()), "slots": slots}

# картинка до/после
S = 4.0; cells = []
F = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 13)
for n in names:
    r = data[n]; mv = dict((key(m[:2]), m[2:]) for m in res[n]["moves"])
    pts = [p for c in r["curves"] for p in c["p"]]
    x0 = min(p[0] for p in pts) - 5; x1 = max(p[0] for p in pts) + 5; y0 = min(p[1] for p in pts) - 5; y1 = max(p[1] for p in pts) + 5
    im = Image.new("RGB", (int((x1 - x0) * S), int((y1 - y0) * S) + 20), "white"); d = ImageDraw.Draw(im)
    tr = lambda p: ((p[0] - x0) * S, 20 + (y1 - p[1]) * S)
    for c in r["curves"]:
        d.line([tr(p) for p in c["p"]], fill=(200, 200, 200), width=1)
        d.line([tr(mv.get(key(p), p)) for p in c["p"]], fill="black", width=2)
    for s in r["seals"]:
        d.rectangle([tr((s[0], s[3])), tr((s[2], s[1]))], outline="red", width=2)
    d.text((3, 2), n.replace("_ФристайлТехнолоджи", "") + "  пазов %d" % len(res[n]["slots"]), fill=(0, 0, 160), font=F)
    cells.append(im)
cw = max(c.width for c in cells); ch = max(c.height for c in cells); k = 4
sheet = Image.new("RGB", (k * cw, ((len(cells) + k - 1) // k) * ch), "white")
for i, c in enumerate(cells):
    sheet.paste(c, ((i % k) * cw, (i // k) * ch))
sheet.save(out_png)
json.dump(res, open(out_json, "w", encoding="utf-8"), ensure_ascii=False)
for n in names:
    print(len(res[n]["slots"]), len(res[n]["moves"]), n)
