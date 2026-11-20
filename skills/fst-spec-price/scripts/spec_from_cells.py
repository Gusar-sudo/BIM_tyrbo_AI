"""Итог спецификации деталей по выгрузке ячеек (spec_dump.py -> schedule_cells.csv) -> revit_spec.csv (article;qty).
Пары колонок находит по шапке: «Артикул», за которой идёт «Кол»/«Кол.» — так новые группы (Заглушка, Держатель) подхватываются сами.
Запуск: py -P -E spec_from_cells.py schedule_cells.csv revit_spec.csv
"""
import csv, sys, io, collections

src, dst = sys.argv[1], sys.argv[2]
rows = [[c.replace("﻿", "").strip() for c in r] for r in csv.reader(io.open(src, encoding="utf-8-sig"), delimiter=";")]
hi = next(i for i, r in enumerate(rows[:5]) if r.count("Артикул") >= 2)
H = rows[hi]
pairs = [(i, i + 1) for i in range(len(H) - 1) if H[i] == "Артикул" and H[i + 1].rstrip(".") == "Кол"]
num = lambda v: float((v or "0").replace(",", ".").replace(" ", "") or 0)
q = collections.defaultdict(float)
for r in rows[hi + 1:]:
    for a, k in pairs:
        if a < len(r) and r[a]:
            try:
                q[r[a]] += num(r[k])
            except ValueError:
                pass
with io.open(dst, "w", encoding="utf-8-sig") as f:
    f.write("article;qty\n")
    for a in sorted(q):
        f.write("%s;%.3f\n" % (a, q[a]))
print("пар колонок:", len(pairs), "артикулов:", len(q))
