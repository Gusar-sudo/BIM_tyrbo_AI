# -*- coding: utf-8 -*-
# Опись скриптов: skills, _bim\batches, _bim\plugin — дубли по имени, совпадение содержимого, какая копия новее.
# py scripts_inventory.py <out.csv> <out.md>
import os, sys, hashlib, csv, datetime, re
ROOTS = {"skills": r"C:\Users\user\.claude\skills", "batches": r"C:\Users\user\Desktop\Фристайл\_bim\batches",
         "plugin": r"C:\Users\user\Desktop\Фристайл\_bim\plugin"}
rows = []
for tag, root in ROOTS.items():
    for dp, dn, fn in os.walk(root):
        if any(x in dp for x in ("__pycache__", "eval-viewer", "-workspace")):
            continue
        for f in fn:
            if f.endswith(".py"):
                p = os.path.join(dp, f); b = open(p, "rb").read()
                head = b.decode("utf-8", "replace").splitlines()[1:3]
                rows.append({"root": tag, "name": f, "path": p, "rel": os.path.relpath(p, root), "size": len(b),
                             "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M"),
                             "md5": hashlib.md5(b.replace(b"\r\n", b"\n")).hexdigest()[:8], "doc": " ".join(h.strip("# ").strip() for h in head)[:150]})
with open(sys.argv[1], "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter=";"); w.writeheader(); w.writerows(rows)
by = {}
for r in rows:
    by.setdefault(r["name"], []).append(r)
dup = {k: v for k, v in by.items() if len(v) > 1}
cnt = {}
for r in rows:
    k = r["root"] + ("\\" + r["rel"].split(os.sep)[0] if os.sep in r["rel"] else "")
    cnt[k] = cnt.get(k, 0) + 1
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    fh.write("# Опись скриптов (%s)\n\nВсего %d файлов .py, имён с несколькими копиями: %d.\n\n## По папкам\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), len(rows), len(dup)))
    for k in sorted(cnt):
        fh.write("- %s: %d\n" % (k, cnt[k]))
    fh.write("\n## Дубли (одинаковое имя)\n| Имя | Копии (папка · дата · отпечаток) | Содержимое |\n|---|---|---|\n")
    for k in sorted(dup):
        v = sorted(dup[k], key=lambda r: r["mtime"], reverse=True)
        same = len(set(r["md5"] for r in v)) == 1
        fh.write("| %s | %s | %s |\n" % (k, "<br>".join("%s\\%s · %s · %s" % (r["root"], r["rel"], r["mtime"], r["md5"]) for r in v),
                                         "одинаковое" if same else "РАЗНОЕ — новее: %s\\%s" % (v[0]["root"], v[0]["rel"])))
print(len(rows), len(dup))
