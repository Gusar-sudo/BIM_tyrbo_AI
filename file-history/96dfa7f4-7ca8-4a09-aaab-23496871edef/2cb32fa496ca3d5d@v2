"""Независимый пересчёт деталей витражей Фристайл и сверка со спецификацией Revit.

Вход (CSV, разделитель «;», UTF-8):
  mullions.csv — выгрузка импостов из модели: колонки type; length_mm и пары
                 FT_<Деталь>_Артикул / FT_<Деталь>_Расход (как в семействах; расход — на 1 п.м.)
  revit_spec.csv (необязательно) — итог спецификации Revit: article; qty
  prices.csv   (необязательно) — article; unit; price_rub; source  (только из Excel/подтверждённых источников)
Выход: spec_calc.csv (article; qty; unit; price_rub; sum_rub; price_source) и diff.csv (если дана revit_spec).
Без сети. Запуск:
  py -P -E spec_calc.py mullions.csv [revit_spec.csv|-] [prices.csv|-] [допуск_относит=0.005]
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


def num(v):
    v = (v or "").strip().replace(",", ".").replace(" ", "")
    return float(v) if v else 0.0


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main(mullions, revit_spec=None, prices=None, rtol=0.005):
    qty = defaultdict(float)
    problems = []
    for r in read(mullions):
        length_m = num(r.get("length_mm")) / 1000
        parts = {}
        for k, v in r.items():
            m = re.match(r"FT_\s*(.+?)_(Артикул|Расход)$", (k or "").strip())
            if m:
                parts.setdefault(m.group(1).strip(), {})[m.group(2)] = v
        for part, d in parts.items():
            art, rate = (d.get("Артикул") or "").strip(), num(d.get("Расход"))
            if art and rate > 0:
                qty[art] += length_m * rate
            elif art or rate:
                problems.append(f'{r.get("type")}: {part} — артикул «{art}», расход {rate} (пара неполная)')
    price = {p["article"]: p for p in read(prices)} if prices else {}
    base = Path(mullions).with_name
    rows = []
    for art in sorted(qty):
        p = price.get(art)
        pr = num(p["price_rub"]) if p else None
        rows.append({"article": art, "qty": f"{qty[art]:.3f}", "unit": p["unit"] if p else "",
                     "price_rub": f"{pr:.2f}" if pr is not None else "",
                     "sum_rub": f"{pr * qty[art]:.2f}" if pr is not None else "",
                     "price_source": p["source"] if p else "НЕТ ЦЕНЫ"})
    with open(base("spec_calc.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["article", "qty", "unit", "price_rub", "sum_rub", "price_source"], delimiter=";")
        w.writeheader(); w.writerows(rows)
    print(f"артикулов: {len(rows)}; без цены: {sum(1 for r in rows if r['price_source'] == 'НЕТ ЦЕНЫ')}")
    for p in problems:
        print("ПРОБЛЕМА", p)
    if revit_spec:
        rv = {r["article"].strip(): num(r["qty"]) for r in read(revit_spec)}
        diff = []
        for art in sorted(set(rv) | set(qty)):
            a, b = qty.get(art, 0.0), rv.get(art, 0.0)
            ok = abs(a - b) <= rtol * max(abs(a), abs(b), 1e-9)
            diff.append({"article": art, "calc": f"{a:.3f}", "revit": f"{b:.3f}", "status": "OK" if ok else "DIFF"})
        with open(base("diff.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["article", "calc", "revit", "status"], delimiter=";")
            w.writeheader(); w.writerows(diff)
        bad = [d for d in diff if d["status"] == "DIFF"]
        print(f"сверка с Revit: OK {len(diff) - len(bad)}, DIFF {len(bad)}")
        for d in bad:
            print(f'DIFF {d["article"]}: пересчёт {d["calc"]} / Revit {d["revit"]}')


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit("usage: spec_calc.py mullions.csv [revit_spec.csv|-] [prices.csv|-] [rtol]")
    sys.stdout.reconfigure(encoding="utf-8")
    opt = lambda i: a[i] if len(a) > i and a[i] != "-" else None
    main(a[0], opt(1), opt(2), float(a[3]) if len(a) > 3 else 0.005)
