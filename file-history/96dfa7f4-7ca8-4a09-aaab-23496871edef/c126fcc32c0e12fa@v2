# -*- coding: utf-8 -*-
# Локально: сопоставить картинки docx с подписями «Рис.N» (по порядку в документе). Аргумент: папка с _document.xml и _rels.xml
import re, json, sys
o = sys.argv[1]
x = open(o + r"\_document.xml", encoding="utf-8").read()
rx = open(o + r"\_rels.xml", encoding="utf-8").read()
rels = {}
for rel in re.findall(r"<Relationship [^>]*>", rx):
    i = re.search(r'Id="([^"]+)"', rel); t = re.search(r'Target="media/([^"]+)"', rel)
    if i and t:
        rels[i.group(1)] = t.group(1)
fig, pend, order = {}, [], []
for p in re.findall(r"<w:p[ >].*?</w:p>", x, flags=re.S):
    txt = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).strip()
    imgs = [rels.get(r) for r in re.findall(r'r:embed="([^"]+)"', p)]
    imgs = [i for i in imgs if i and not i.endswith(".wdp")]
    pend += imgs
    m = re.findall(r"Рис\.?\s*(\d+)", txt)
    if m and pend:
        for n in m:
            fig.setdefault(int(n), []).extend(pend)
        pend = []
json.dump(fig, open(o + r"\_fig_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for k in sorted(fig):
    print(k, fig[k])
