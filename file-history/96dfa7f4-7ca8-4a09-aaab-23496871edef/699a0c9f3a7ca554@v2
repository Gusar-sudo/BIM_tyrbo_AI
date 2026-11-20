"""Строит каталог из текстов альбомов технических решений (после extract_docs.py).

Выход (UTF-8 с BOM, чтобы Excel открыл кириллицу):
  profiles.csv     — профили: система, название, обозначение, доп. обозначение, назначение,
                     вес кг/м, периметр мм, сопрягаемые, стыкуемые, источник (файл:строка)
  glass_rules.csv  — правила размера стекла: система, условие, рисунок, формула, источник

Только локально, без сети. Запуск:
  py -P -E parse_albums.py <папка extract> <папка catalog>
"""
import csv
import hashlib
import re
import sys
from pathlib import Path

LABELS = {
    "Назначение": "purpose",
    "Вес 1п.м.": "weight_kg_m",
    "Внешний периметр": "perimeter_mm",
    "Сопрягаемые элементы*": "mates",
    "Стыкуемые элементы**": "joins",
}
NAME_LABEL = "Название / Обозначение"
# обозначения: FS.C-21, FS.C-U5, FS.М2-Ug, П-25, ФСТ-81 (М может быть кириллической)
CODE_RE = re.compile(r"((?:FS\.[A-Za-zА-Яа-я0-9]+-[\w-]+)|(?:П-\d+)|(?:ФСТ-\d+))")


def system_of(fname: str) -> str:
    m = re.search(r"М(\d)|M(\d)", fname)
    return f"M{m.group(1) or m.group(2)}" if m else "?"


def cells_with_lines(lines):
    """Склеивает строки в ячейки таблиц: новая ячейка начинается с ' | '."""
    cells, cur, start = [], None, 0
    for i, line in enumerate(lines, 1):
        if line.startswith(" | "):
            if cur is not None:
                cells.append((cur.strip(), start))
            cur, start = line[3:], i
        elif cur is not None and line.strip() and not line.startswith("\t"):
            cur += "\n" + line
        else:
            if cur is not None:
                cells.append((cur.strip(), start))
            cur = None
    if cur is not None:
        cells.append((cur.strip(), start))
    return cells


def parse_profiles(lines, src, system):
    rows, cells = [], cells_with_lines(lines)
    i = 0
    while i < len(cells):
        text, ln = cells[i]
        if text == NAME_LABEL and i + 1 < len(cells):
            value = " ".join(cells[i + 1][0].split())
            cm = CODE_RE.search(value)
            if cm:
                name = value[:cm.start()].rstrip(" /")
                code = cm.group(1)
                alt = re.search(r"\(([^)]+)\)", value[cm.end():])
            else:  # обозначения нет — берём только название, код уйдёт в вопросы
                name, code, alt = value, "", None
            row = {"system": system, "name": name.strip() or value,
                   "code": code, "alt_code": alt.group(1) if alt else "",
                   "source": f"{src}:{ln}"}
            j = i + 2
            while j + 1 < len(cells) and cells[j][0] != NAME_LABEL:
                label = cells[j][0]
                if label in LABELS:
                    row[LABELS[label]] = cells[j + 1][0].replace("\n", "; ")
                    j += 2
                else:
                    j += 1
            for k in ("weight_kg_m", "perimeter_mm"):
                v = row.get(k, "")
                num = re.search(r"\d+(?:[.,]\d+)?", v)
                row[k] = num.group(0).replace(",", ".") if num else ""
            rows.append(row)
            i = j
        else:
            i += 1
    return rows


def parse_glass(lines, src, system):
    rows, title, fig, tline = [], None, "", 0
    for i, line in enumerate(lines, 1):
        s = line.strip(" |\t")
        if "размеров стекла" in s and not s.lower().startswith("l=") and "PAGEREF" not in s \
                and len(s) > len("Расчет размеров стекла") + 3:
            title, fig, tline = s, "", i
        elif re.match(r"Рис\.?\s*\d+", s):
            fig = s
        elif title and re.match(r"^l\s*=|^L\d?\s*\+", s.replace(" ", ""), re.I) or (title and s.startswith("l=")):
            rows.append({"system": system, "condition": title, "figure": fig,
                         "formula": s, "source": f"{src}:{i}", "condition_source": f"{src}:{tline}"})
    return rows


def main(extract_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    seen, profiles, glass = set(), [], []
    for txt in sorted(extract_dir.glob("*Альбом технических решений*.txt")):
        digest = hashlib.sha256(txt.read_bytes()).hexdigest()
        if digest in seen:  # одинаковые копии альбома в разных папках
            continue
        seen.add(digest)
        lines = txt.read_text(encoding="utf-8").splitlines()
        system = system_of(txt.name)
        profiles += parse_profiles(lines, txt.name, system)
        glass += parse_glass(lines, txt.name, system)
    pf = ["system", "name", "code", "alt_code", "purpose", "weight_kg_m", "perimeter_mm", "mates", "joins", "source"]
    with (out_dir / "profiles.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pf, delimiter=";", extrasaction="ignore")
        w.writeheader(); w.writerows(profiles)
    gf = ["system", "condition", "figure", "formula", "source", "condition_source"]
    with (out_dir / "glass_rules.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=gf, delimiter=";")
        w.writeheader(); w.writerows(glass)
    by_sys = {}
    for p in profiles:
        by_sys[p["system"]] = by_sys.get(p["system"], 0) + 1
    print("profiles:", len(profiles), by_sys, " glass rules:", len(glass))
    missing = [p["code"] for p in profiles if not p.get("weight_kg_m")]
    if missing:
        print("без веса:", ", ".join(missing))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: parse_albums.py <extract_dir> <catalog_dir>")
    sys.stdout.reconfigure(encoding="utf-8")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
