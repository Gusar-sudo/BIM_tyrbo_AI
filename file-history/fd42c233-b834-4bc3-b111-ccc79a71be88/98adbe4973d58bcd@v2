"""Артикулы профилей из всех DWG (texts.txt после dxf_extract) против каталога альбомов (profiles.csv).

Для каждого кода: подписи из DWG (самая частая — как имя), в каких DWG встречается и сколько раз,
есть ли в каталоге альбомов (и в какой системе), и статус:
  в_альбоме — код есть в profiles.csv;
  новый     — кода нет в альбомах (кандидат в каталог, вопрос производству о весе/назначении).
Только локально. Запуск:
  py -P -E dwg_profiles.py <папка _bim\\dxf> <profiles.csv> <выход profiles_dwg.csv>
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

CODE = re.compile(r"FS\.C-\s?(\d{1,3}[A-Za-zА-Яа-я]?|U[XХ0-9]*)\b")
NAME_AFTER = re.compile(r"FS\.C-\s?[\wХ]+\s*[-–—]?\s*(.+)$")


def norm_code(c):
    return "FS.C-" + c.replace(" ", "").upper().replace("Х", "X")


def main(dxf_dir, profiles_csv, out_csv):
    catalog = {}
    with open(profiles_csv, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            for k in ("code", "alt_code"):
                c = (r.get(k) or "").strip()
                if c.startswith("FS.C-"):
                    catalog.setdefault(norm_code(c[5:]), set()).add(r["system"])
    names, where = defaultdict(Counter), defaultdict(Counter)
    for txt in sorted(Path(dxf_dir).glob("*.texts.txt")):
        src = txt.name.replace(".texts.txt", "")
        lines = [l.strip() for l in txt.read_text(encoding="utf-8").splitlines()]
        for i, line in enumerate(lines):
            for m in CODE.finditer(line):
                code = norm_code(m.group(1))
                where[code][src] += 1
                tail = NAME_AFTER.search(line[m.start():])
                nm = (tail.group(1).strip() if tail else "")
                nm = re.split(r"\s+FS\.C-", nm)[0].strip(" .,;")
                if len(nm) >= 3 and "?" not in nm:
                    names[code][nm] += 1
    rows = []
    for code in sorted(where, key=lambda c: (not re.match(r"FS\.C-\d", c), int(re.sub(r"\D", "", c) or 0), c)):
        systems = sorted(catalog.get(code, []))
        rows.append({"code": code,
                     "name_dwg": names[code].most_common(1)[0][0] if names[code] else "",
                     "names_other": " | ".join(n for n, _ in names[code].most_common(4)[1:]),
                     "dwg_files": "; ".join(f"{k}×{v}" for k, v in where[code].most_common()),
                     "album_systems": ",".join(systems),
                     "status": "в_альбоме" if systems else "новый"})
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(rows)
    new = [r for r in rows if r["status"] == "новый"]
    print(f"кодов в DWG: {len(rows)}; в альбомах: {len(rows) - len(new)}; новых: {len(new)}")
    for r in new:
        print(f"  НОВЫЙ {r['code']:10} {r['name_dwg'][:50]:50} [{r['dwg_files']}]")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: dwg_profiles.py <dxf_dir> <profiles.csv> <out.csv>")
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:])
