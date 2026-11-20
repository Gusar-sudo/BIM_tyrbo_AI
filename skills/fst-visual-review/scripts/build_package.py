# -*- coding: utf-8 -*-
# Сборка пакета визуальной приёмки М2/М3: картинки -> pkg\img (JPG/PNG уменьшенные), data.json, package.sha256.
# Запуск: py -P -E build_package.py <config.json>
# config: {pkg_dir, types:[{tag,name,short,system,stand,cover,fill,center_ref,edge_ref,flex:{c3d,f3d,fac,plan},nodes:{center,edge}}],
#          extra:[{key,title,files:[...]}], checks:{...}, questions:[...]}
import json, sys, os, hashlib, shutil
from PIL import Image
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
PKG = cfg["pkg_dir"]; IMG = os.path.join(PKG, "img")
os.makedirs(IMG, exist_ok=True)
done = {}


def put(src, key, maxw=1400):
    if not src:
        return None
    if src in done:
        return done[src]
    im = Image.open(src)
    if im.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", im.size, "white"); im = im.convert("RGBA"); bg.paste(im, mask=im.split()[-1]); im = bg
    else:
        im = im.convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    name = key + ".png"
    im.save(os.path.join(IMG, name), optimize=True)
    done[src] = "img/" + name
    return done[src]


data = {"types": [], "extra": [], "checks": cfg["checks"], "questions": cfg["questions"], "meta": cfg.get("meta", {})}
for t in cfg["types"]:
    r = dict((k, t[k]) for k in t if k not in ("flex", "nodes", "center_ref", "edge_ref"))
    r["flex"] = dict((k, put(v, "t%s_%s" % (t["tag"], k))) for k, v in t["flex"].items())
    r["nodes"] = dict((k, put(v, "t%s_node_%s" % (t["tag"], k), 1000)) for k, v in t["nodes"].items())
    r["center_ref"] = put(t.get("center_ref"), "album_" + os.path.splitext(os.path.basename(t["center_ref"]))[0] if t.get("center_ref") else "", 900) if t.get("center_ref") else None
    r["edge_ref"] = put(t.get("edge_ref"), "album_" + os.path.splitext(os.path.basename(t["edge_ref"]))[0], 900) if t.get("edge_ref") else None
    data["types"].append(r)
for e in cfg.get("extra", []):
    data["extra"].append({"key": e["key"], "title": e["title"], "items": [{"cap": c, "img": put(f, "x_%s_%d" % (e["key"], i))} for i, (c, f) in enumerate(e["files"])]})
# отпечаток: все картинки пакета + данные проверок
h = hashlib.sha256()
for f in sorted(os.listdir(IMG)):
    h.update(f.encode("utf-8")); h.update(open(os.path.join(IMG, f), "rb").read())
h.update(json.dumps(cfg["checks"], ensure_ascii=False, sort_keys=True).encode("utf-8"))
fp = h.hexdigest()
data["fingerprint"] = fp
json.dump(data, open(os.path.join(PKG, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(PKG, "package.sha256"), "w", encoding="utf-8").write(fp + "\n")
tot = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("images", len(os.listdir(IMG)), "MB", round(tot / 1e6, 2), "fp", fp[:16])
