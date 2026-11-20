# -*- coding: utf-8 -*-
# Аудит «после» по фактам collect_after.py (без Revit): F1 ADSK, F2 детали и артикулы, соответствие имени типа /
# наименования / профиля (система, одно-/двухслойный, левый/правый), панели, витражи, сверка теста с библиотекой.
# Запуск: python analyze_after.py facts_lib.json facts_test.json profiles.csv album_dir out_dir
import json, csv, re, sys, os, glob, collections, io

lib, test, cat_path, album_dir, out = sys.argv[1:6]
L = json.load(open(lib, encoding="utf-8")); T = json.load(open(test, encoding="utf-8"))
codes = set()
for r in csv.DictReader(open(cat_path, encoding="utf-8-sig"), delimiter=";"):
    for k in ("code", "alt_code"):
        for c in re.split(r"[,;/ ]+", r.get(k) or ""):
            if c.strip():
                codes.add(c.strip().replace("С", "C").replace("М", "M").upper())
album = ""
for p in glob.glob(os.path.join(album_dir, "*.txt")):
    album += io.open(p, encoding="utf-8", errors="ignore").read()
album_n = album.replace("С", "C").replace("М", "M").upper()
CODE_RE = re.compile(r"F[SC]\.?\s?[CС]?-?\s?[\wА-Яа-я\-]+", re.I)
rows = []   # severity, kind, where, what


def add(sev, kind, where, what):
    rows.append([sev, kind, where, what])


def sysof(s):
    m = re.search(r"М([123])", s or "")
    return m.group(1) if m else None


def layer(s):
    s = (s or "").lower()
    if "однослойн" in s or "одинарн" in s:
        return "1"
    if "двухслойн" in s or "двуслойн" in s or "двойн" in s:
        return "2"
    return None


def hand(s):
    s = (s or "").lower()
    if "левый" in s:
        return "L"
    if "правый" in s:
        return "R"
    return None


stat = collections.Counter()
# ---------- импосты
for m in L["mullion_types"]:
    n, p, prof = m["name"], m["p"], m["profile"] or ""
    w = "импост «%s»" % n
    stat["mullions"] += 1
    if not p.get("ADSK_Наименование"):
        add("FAIL", "F1.5 ADSK_Наименование пусто", w, "")
    else:
        an = p["ADSK_Наименование"]
        if layer(n) and layer(an) and layer(n) != layer(an):
            add("FAIL", "наименование ≠ тип (слой)", w, "ADSK_Наименование: «%s»" % an)
        mm = re.search(r"MODEL\s*(\d)", an)
        if mm and sysof(n) and mm.group(1) != sysof(n):
            add("FAIL", "наименование ≠ тип (система)", w, "ADSK_Наименование: «%s»" % an)
    if (p.get("ADSK_Код изделия") or "").replace("M", "М") not in ("М" + (sysof(n) or "?"),):
        add("WARN", "ADSK_Код изделия ≠ система", w, "«%s»" % p.get("ADSK_Код изделия"))
    if sysof(prof) and sysof(n) and sysof(prof) != sysof(n):
        add("FAIL", "профиль другой системы", w, prof)
    if layer(prof) and layer(n) and layer(prof) != layer(n):
        add("FAIL", "профиль другого слоя", w, prof)
    if hand(n) and hand(prof.replace("Левый", "левый").replace("Правый", "правый")) and hand(n) != hand(prof.replace("Левый", "левый").replace("Правый", "правый")):
        add("FAIL", "профиль другой руки (левый/правый)", w, prof)
    if not prof.startswith("BIMLIB_"):
        add("FAIL", "профиль не библиотеки", w, prof or "—")
    for k, v in p.items():
        if k.startswith("FT_") and k.endswith("_Артикул"):
            base = k[:-len("_Артикул")]
            r = p.get(base + "_Расход")
            if v and (r is None or r <= 0):
                add("FAIL", "F2.3 артикул без расхода", w, "%s=%s, расход=%s" % (k, v, r))
            if (not v) and r and r > 0:
                add("FAIL", "F2.3 расход без артикула", w, "%s пусто, расход=%s" % (k, r))
            if v:
                for c in CODE_RE.findall(v):
                    cn = re.sub(r"\s", "", c).replace("С", "C").replace("М", "M").upper().rstrip(".,")
                    stat["codes"] += 1
                    if cn in codes:
                        stat["codes_cat"] += 1
                    elif cn in album_n:
                        stat["codes_album"] += 1
                        add("INFO", "F2.2 артикул только в тексте альбома", w, "%s: %s" % (k, cn))
                    else:
                        add("FAIL", "F2.2 артикул нет в каталоге и альбоме", w, "%s: %s" % (k, cn))
                if not CODE_RE.search(v):
                    stat["noncode"] += 1
    for k in ("ADSK_Завод-изготовитель", "ADSK_Версия Revit", "ADSK_Единица измерения"):
        stat["%s=%s" % (k, p.get(k))] += 1
# ---------- панели
for pt in L["panel_types"]:
    p = pt["p"]; w = "панель «%s : %s»" % (pt["family"], pt["name"])
    if not pt["family"].startswith("BIMLIB_"):
        add("INFO", "системная панель", w, "экз. %d" % pt["n"]); continue
    stat["panels"] += 1
    if not p.get("ADSK_Наименование"):
        add("FAIL", "F1.5 ADSK_Наименование пусто", w, "")
    stat["panel %s=%s" % ("ADSK_Версия Revit", p.get("ADSK_Версия Revit"))] += 1
    stat["panel Завод=%s" % p.get("ADSK_Завод-изготовитель")] += 1
    m = re.search(r"(\d+)\s*мм", pt["name"])
# ---------- витражи
ptn = set(pt["family"] + ":" + pt["name"] for pt in L["panel_types"]) | set(pt["name"] for pt in L["panel_types"])
for wt in L["wall_types"]:
    p = wt["p"]; w = "витраж «%s»" % wt["name"]
    stat["walls"] += 1
    if not p.get("ADSK_Наименование"):
        add("FAIL", "F1.5 ADSK_Наименование пусто", w, "")
    else:
        if layer(wt["name"]) and layer(p["ADSK_Наименование"]) and layer(wt["name"]) != layer(p["ADSK_Наименование"]) and "цельностекл" not in wt["name"].lower():
            add("FAIL", "наименование ≠ тип (слой)", w, p["ADSK_Наименование"])
        if sysof(wt["name"]) and sysof(p["ADSK_Наименование"]) and sysof(wt["name"]) != sysof(p["ADSK_Наименование"]):
            add("FAIL", "наименование ≠ тип (система)", w, p["ADSK_Наименование"])
    if wt.get("panel") and wt["panel"] not in ptn and not any(wt["panel"].endswith(x) for x in ptn):
        add("WARN", "панель витража не найдена", w, wt["panel"])
    stat["wall Версия=%s" % p.get("ADSK_Версия Revit")] += 1
# ---------- тест ↔ библиотека
def idx(d):
    o = {}
    for m in d["mullion_types"]:
        o["M:" + m["name"]] = (m["profile"], {k: v for k, v in m["p"].items()})
    for m in d["panel_types"]:
        o["P:" + m["family"] + ":" + m["name"]] = (None, m["p"])
    for m in d["wall_types"]:
        o["W:" + m["name"]] = (m.get("panel"), m["p"])
    return o
a, b = idx(L), idx(T)
for k in sorted(set(a) - set(b)):
    add("WARN", "есть в библиотеке, нет в тесте", k, "")
for k in sorted(set(b) - set(a)):
    add("WARN", "есть в тесте, нет в библиотеке", k, "")
for k in sorted(set(a) & set(b)):
    if a[k][0] != b[k][0]:
        add("WARN", "тест ≠ библиотека (профиль/панель)", k, "%s | %s" % (a[k][0], b[k][0]))
    for pk in set(a[k][1]) | set(b[k][1]):
        if a[k][1].get(pk) != b[k][1].get(pk):
            add("WARN", "тест ≠ библиотека (параметр)", k, "%s: %s | %s" % (pk, a[k][1].get(pk), b[k][1].get(pk)))
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "findings.csv"), "w", encoding="utf-8-sig", newline="") as f:
    wr = csv.writer(f, delimiter=";"); wr.writerow(["severity", "kind", "where", "what"]); wr.writerows(rows)
cnt = collections.Counter((r[0], r[1]) for r in rows)
summ = {"stat": dict(stat), "counts": {"%s | %s" % k: v for k, v in sorted(cnt.items())}}
json.dump(summ, open(os.path.join(out, "analysis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(summ, ensure_ascii=False, indent=1))
