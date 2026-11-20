# -*- coding: utf-8 -*-
# Разбор описи: что держать (skills — единственный источник), что продвинуть из batches в skills, что в архив, что синхронизировать в plugin.
# py scripts_classify.py <scripts.csv> <plan.md> <plan.csv>
import csv, sys, os, re
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig"), delimiter=";"))
by = {}
for r in rows:
    by.setdefault(r["name"], []).append(r)
plan = []
for name, v in sorted(by.items()):
    sk = [r for r in v if r["root"] == "skills"]
    ba = [r for r in v if r["root"] == "batches"]
    pl = [r for r in v if r["root"] == "plugin"]
    for b in ba:
        if not sk:
            act = u"только batches — разовая партия → архив"
        elif any(s["md5"] == b["md5"] for s in sk):
            act = u"копия skills (одинаковая) → архив"
        elif max(s["mtime"] for s in sk) >= b["mtime"]:
            act = u"СТАРАЯ копия (в skills новее) → архив"
        else:
            act = u"НОВЕЕ skills → перенести в skills, потом архив"
        plan.append([name, "batches", b["rel"], b["mtime"], act])
    for p in pl:
        if not sk:
            act = u"нет в skills → проверить вручную"
        elif any(s["md5"] == p["md5"] for s in sk):
            act = u"совпадает со skills"
        else:
            act = u"устарела → обновить из skills"
        plan.append([name, "plugin", p["rel"], p["mtime"], act])
    if len(sk) > 1 and len(set(s["md5"] for s in sk)) > 1:
        for s in sk:
            plan.append([name, "skills", s["rel"], s["mtime"], u"ДВА РАЗНЫХ в skills → свести в один"])
with open(sys.argv[3], "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh, delimiter=";"); w.writerow(["имя", "где", "путь", "дата", "действие"]); w.writerows(plan)
from collections import Counter
c = Counter((p[1], p[4]) for p in plan)
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    fh.write(u"# План по скриптам (черновик)\n\nИсточник правды — `~\\.claude\\skills\\fst-*\\scripts`. `_bim\\plugin\\fst-bim` — снимок skills для выпуска, `_bim\\batches` — рабочие партии.\n\n## Сводка\n")
    for (where, act), n in sorted(c.items()):
        fh.write(u"- %s: %s — %d\n" % (where, act, n))
    for key in (u"НОВЕЕ skills", u"СТАРАЯ копия", u"ДВА РАЗНЫХ", u"нет в skills"):
        sel = [p for p in plan if key in p[4]]
        if sel:
            fh.write(u"\n## %s\n" % key)
            for p in sel:
                fh.write(u"- %s · %s\\%s · %s\n" % (p[0], p[1], p[2], p[3]))
print(dict(c))
