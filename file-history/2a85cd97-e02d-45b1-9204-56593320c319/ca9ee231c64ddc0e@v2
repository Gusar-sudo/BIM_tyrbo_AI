"""Каталог скриптов skills: для каждого fst-* skill пишет references/scripts.md — скрипт, назначение (шапка), аргументы.
Назначение — первые строки комментария/докстринга после «coding»; аргументы — строка с «Аргумент»/«Запуск»/«Usage».
Разовые пробы (probe_/scan_/survey_/prep_) помечаются. Шапки нет — «нет описания» (дописать в скрипт).
Запуск: python -I scripts_catalog.py [skills_dir]
"""
import io, os, re, sys

H = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.claude/skills")


def head(path):
    lines = io.open(path, encoding="utf-8", errors="replace").read().splitlines()[:25]
    desc, args, in_doc = [], "", False
    for ln in lines:
        s = ln.strip()
        if "coding" in s and s.startswith("#"):
            continue
        if s.startswith('"""') or s.startswith("'''") or (in_doc and s.endswith('"""')):
            in_doc = (not in_doc) and s.count('"""') < 2
            s = s.strip('"\' ')
            if not s:
                continue
        elif s.startswith("#"):
            s = s.lstrip("# ")
        elif not in_doc:
            if desc:
                break
            continue
        m = re.search(r"(Аргумент|Запуск|Usage)", s)
        if m:
            pre = s[:m.start()].strip(" .;:—-")
            if pre and len(desc) < 2:
                desc.append(pre)
            args = (args + " " + s[m.start():]).strip()
        elif s and len(desc) < 2:
            desc.append(s)
    return " ".join(desc)[:220], args[:220]


total = 0
for sk in sorted(os.listdir(H)):
    d = os.path.join(H, sk, "scripts")
    if not sk.startswith("fst-") or not os.path.isdir(d):
        continue
    rows = []
    for f in sorted(os.listdir(d)):
        if not f.endswith((".py", ".ps1")) or f.startswith("__"):
            continue
        desc, args = head(os.path.join(d, f))
        tag = " *(разовая проба)*" if re.match(r"(probe_|scan_|survey_|prep_)", f) else ""
        rows.append(u"| `%s`%s | %s | %s |" % (f, tag, (desc or u"**нет описания**").replace("|", "/"), args.replace("|", "/") or u"—"))
    if not rows:
        continue
    os.makedirs(os.path.join(H, sk, "references"), exist_ok=True)
    txt = (u"# Скрипты `%s` (каталог, собран `fst-pipeline/scripts/scripts_catalog.py`)\n\n"
           u"Запуск в Revit — `horizun_execute_python` с `code_path`; вне Revit — `python -I` (с графикой — `python -P -E`). "
           u"Новый скрипт записи — из шаблона `fst-curtainwall-author/scripts/_template_write.py`. После добавления скрипта — пересобрать каталог.\n\n"
           u"| Скрипт | Что делает | Аргументы / запуск |\n|---|---|---|\n" % sk) + u"\n".join(rows) + u"\n"
    io.open(os.path.join(H, sk, "references", "scripts.md"), "w", encoding="utf-8").write(txt)
    total += len(rows)
    print(sk, len(rows), "без описания:", sum(1 for r in rows if u"нет описания" in r))
print("всего", total)
