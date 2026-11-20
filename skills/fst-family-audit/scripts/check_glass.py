"""Сверяет размеры стекла в модели с правилами альбомов Фристайл.

Вход:
  panels.csv  — выгрузка из модели (спецификация панелей), колонки:
                id; system; orientation (H|V); side_a; side_b; measured_mm; kind (L|L1); glass_mm
                side_a/side_b — обозначения профилей по краям (FS.C-21 …),
                measured_mm — измеренный в модели размер L или L1, glass_mm — размер стекла в модели.
  pairs.csv   — сопоставление пар профилей правилам (готовит Claude из glass_rules.csv,
                один раз подтверждается человеком визуально), колонки:
                system; orientation; side_a; side_b; k_L; k_L1; figure; source
Выход: таблица PASS/FAIL/NO_RULE в stdout и results.csv рядом с panels.csv.
Допуск по умолчанию 0,5 мм. Только локально, без сети.
  py -P -E check_glass.py panels.csv pairs.csv [допуск_мм]
"""
import csv
import sys
from pathlib import Path


def num(v):
    v = (v or "").strip().replace(",", ".")
    return float(v) if v else None


def load_pairs(path):
    rules = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            key = (r["system"], r["orientation"], frozenset({r["side_a"], r["side_b"]}))
            rules[key] = r
    return rules


def main(panels_path, pairs_path, tol):
    rules = load_pairs(pairs_path)
    out, counts = [], {"PASS": 0, "FAIL": 0, "NO_RULE": 0}
    with open(panels_path, encoding="utf-8-sig") as f:
        for p in csv.DictReader(f, delimiter=";"):
            key = (p["system"], p["orientation"], frozenset({p["side_a"], p["side_b"]}))
            rule = rules.get(key)
            res = {"id": p["id"], "pair": f'{p["side_a"]} / {p["side_b"]}', "orientation": p["orientation"],
                   "glass_model": p["glass_mm"], "expected": "", "delta": "", "status": "NO_RULE",
                   "figure": "", "source": ""}
            if rule:
                k = num(rule["k_L"] if p["kind"] == "L" else rule["k_L1"])
                m, g = num(p["measured_mm"]), num(p["glass_mm"])
                if k is not None and m is not None and g is not None:
                    exp = m + k
                    res.update(expected=f"{exp:.1f}", delta=f"{g - exp:+.1f}",
                               status="PASS" if abs(g - exp) <= tol else "FAIL",
                               figure=rule["figure"], source=rule["source"])
            counts[res["status"]] += 1
            out.append(res)
    dst = Path(panels_path).with_name("results.csv")
    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["id"], delimiter=";")
        w.writeheader(); w.writerows(out)
    for r in out:
        if r["status"] != "PASS":
            print(f'{r["status"]:7} панель {r["id"]}: {r["pair"]} {r["orientation"]} стекло {r["glass_model"]} ожидалось {r["expected"]} ({r["figure"]})')
    print("итого:", counts, "->", dst)


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: check_glass.py panels.csv pairs.csv [tol_mm]")
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) == 4 else 0.5)
