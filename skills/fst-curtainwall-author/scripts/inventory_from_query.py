"""Инвентаризация импостов Фристайл из ответа horizun_query_model (только чтение модели).

Вход: JSON-ответ horizun_query_model по OST_CurtainWallMullions с include_types=true,
      parameter_format=compact, return_fields [type, type_id, is_element_type] и return_parameters
      (Длина, FT_*_Артикул/Расход, ADSK_*, Толщина). Если ответ большой, клиент сохраняет его в файл —
      этот файл и передаётся.
      profiles.csv из fst-docs-intake.
Выход в папку out:
  types.csv          — по типу: имя, FSC, система, все FT_* и ADSK_*, число экземпляров, сумма длин
  mullions.csv       — по экземпляру: type; length_mm; пары FT_*_Артикул/FT_*_Расход (вход для spec_calc.py)
  catalog_check.csv  — каждый артикул из модели: найден ли в profiles.csv той же системы / любой системы
  summary.txt        — короткая сводка
Без сети. Запуск:
  py -P -E inventory_from_query.py <query.json|txt> <profiles.csv> <out_dir> [система M2]
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PARTS = ["Основание", "Витраж", "Нащельник", "Рейка", "Держатель", "Заглушка", "Уплотнитель"]


def load_json(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    start = text.find("{")
    return json.loads(text[start:])


def norm_code(c):
    c = (c or "").strip().upper().replace("М", "M")  # кириллическая М → латинская
    return re.sub(r"\s+", "", c)


def main(src, profiles_path, out_dir, system=None):
    data = load_json(src)
    rows = data.get("rows", [])
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    catalog = defaultdict(set)  # code -> {systems}
    with open(profiles_path, encoding="utf-8-sig") as f:
        for p in csv.DictReader(f, delimiter=";"):
            for k in ("code", "alt_code"):
                if p.get(k):
                    catalog[norm_code(p[k])].add(p["system"])

    types, inst = {}, []
    for r in rows:
        params = r.get("parameters") or {}
        if r.get("is_element_type"):
            types[r["element_id"]] = {"type_id": r["element_id"], "type": r.get("type") or r.get("name"), **params}
        else:
            inst.append(r)

    count, length = defaultdict(int), defaultdict(float)
    mrows = []
    for r in inst:
        t = types.get(r.get("type_id"), {})
        p = r.get("parameters") or {}
        ln = p.get("Длина")
        ln = float(ln) if isinstance(ln, (int, float)) else None
        count[r.get("type_id")] += 1
        if ln is not None:
            length[r.get("type_id")] += ln
        row = {"element_id": r["element_id"], "type": r.get("type"), "length_mm": "" if ln is None else f"{ln:.1f}"}
        for part in PARTS:
            row[f"FT_{part}_Артикул"] = t.get(f"FT_{part}_Артикул") or p.get(f"FT_{part}_Артикул") or ""
            v = t.get(f"FT_{part}_Расход", p.get(f"FT_{part}_Расход"))
            row[f"FT_{part}_Расход"] = "" if v is None else v
        v = t.get("FT_Клипса_Расход", p.get("FT_Клипса_Расход"))
        row["FT_Клипса_Расход"] = "" if v is None else v
        mrows.append(row)

    tcols = ["type_id", "type", "fsc", "system", "instances", "length_total_m"] + \
        [f"FT_Основание_Наименование"] + [f"FT_{p}_{k}" for p in PARTS for k in ("Артикул", "Расход")] + \
        ["FT_Клипса_Расход", "ADSK_Наименование", "ADSK_Код изделия", "ADSK_Обозначение",
         "ADSK_Завод-изготовитель", "ADSK_Масса", "Толщина"]
    trows = []
    for tid, t in sorted(types.items(), key=lambda kv: str(kv[1].get("type"))):
        name = t.get("type") or ""
        m = re.search(r"FSC\s*(\d+К?)", name)
        sysm = re.match(r"\s*[MМ](\d)", name)
        row = {c: t.get(c, "") for c in tcols}
        row.update(type_id=tid, type=name, fsc=("FSC" + m.group(1)) if m else "",
                   system=("M" + sysm.group(1)) if sysm else "", instances=count[tid],
                   length_total_m=f"{length[tid] / 1000:.3f}")
        trows.append({k: ("" if v is None else v) for k, v in row.items()})

    checks = []
    seen = set()
    for t in trows:
        for part in PARTS:
            code = t.get(f"FT_{part}_Артикул")
            if not code or (t["type"], part) in seen:
                continue
            seen.add((t["type"], part))
            systems = catalog.get(norm_code(code), set())
            status = "OK" if t["system"] in systems else ("OTHER_SYSTEM" if systems else "NOT_IN_CATALOG")
            checks.append({"type": t["type"], "part": part, "article": code, "status": status,
                           "catalog_systems": ",".join(sorted(systems))})

    def write(name, rows_, cols):
        with open(out / name, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
            w.writeheader(); w.writerows(rows_)

    write("types.csv", trows, tcols)
    write("mullions.csv", mrows, list(mrows[0].keys()) if mrows else ["type"])
    write("catalog_check.csv", checks, ["type", "part", "article", "status", "catalog_systems"])

    st = defaultdict(int)
    for c in checks:
        st[c["status"]] += 1
    bad = sorted({(c["article"], c["status"], c["catalog_systems"]) for c in checks if c["status"] != "OK"})
    empty_mass = sum(1 for t in trows if str(t.get("ADSK_Масса")) in ("", "0", "0.0"))
    empty_design = sum(1 for t in trows if not t.get("ADSK_Обозначение"))
    lines = [
        f"источник: {src}",
        f"matched_total: {data.get('matched_total')}  строк в файле: {len(rows)}  усечено: {data.get('truncated')}",
        f"типов: {len(trows)}  экземпляров: {len(mrows)}",
        f"FSC: " + ", ".join(sorted({t['fsc'] for t in trows if t['fsc']})),
        f"проверка артикулов: {dict(st)}",
        "не OK: " + ("; ".join(f"{a} ({s}{' → ' + cs if cs else ''})" for a, s, cs in bad) or "нет"),
        f"ADSK_Масса пусто/0: {empty_mass} из {len(trows)};  ADSK_Обозначение пусто: {empty_design} из {len(trows)}",
        "Толщина (мм): " + ", ".join(sorted({str(t.get('Толщина')) for t in trows})),
        "ADSK_Завод-изготовитель: " + " | ".join(sorted({str(t.get('ADSK_Завод-изготовитель')) for t in trows})),
    ]
    (out / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        sys.exit("usage: inventory_from_query.py <query.json> <profiles.csv> <out_dir> [system]")
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:])
