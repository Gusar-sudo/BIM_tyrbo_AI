# -*- coding: utf-8 -*-
# Наведение порядка в скриптах 2026-11-13 (по плану audit\scripts_2026-11-13\README.md). Ничего не удаляет — только копирует/переносит в архив.
import os, shutil, csv, datetime, hashlib
SK = r"C:\Users\user\.claude\skills"
BIM = r"C:\Users\user\Desktop\Фристайл\_bim"
BA = os.path.join(BIM, "batches")
AR = os.path.join(BIM, "archive", "2026-11-13_scripts")
SCR = r"C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Desktop---------\2a85cd97-e02d-45b1-9204-56593320c319\scratchpad"
log = []


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]


def copy(src, dst, why):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        bk = os.path.join(AR, "skills_replaced", os.path.relpath(dst, SK))
        os.makedirs(os.path.dirname(bk), exist_ok=True); shutil.copy2(dst, bk)
        log.append(["резерв заменяемого", dst, bk, md5(dst)])
    shutil.copy2(src, dst); log.append([why, src, dst, md5(dst)])


# 1-2. в skills
PA = os.path.join(SK, "fst-profile-author", "scripts"); DW = os.path.join(SK, "fst-dwg-reader", "scripts")
VR = os.path.join(SK, "fst-visual-review", "scripts"); PL = os.path.join(SK, "fst-pipeline", "scripts"); RL = os.path.join(SK, "fst-bimlib-release", "scripts")
M2C = os.path.join(BA, "M2_C")
for f in ("build_corner135.py", "mirror_profiles.py", "body_union.py", "fill_mask.py", "fill_loops.py", "apply_corner_types.py"):
    copy(os.path.join(M2C, f), os.path.join(PA, f), "в skills (из batches)")
copy(os.path.join(BA, "color", "batch_fills.py"), os.path.join(PA, "batch_fills.py"), "в skills (из batches)")
copy(os.path.join(M2C, "sheet_row.py"), os.path.join(VR, "sheet_row.py"), "в skills (из batches)")
copy(os.path.join(BA, "release", "bimlib_table_update.py"), os.path.join(RL, "bimlib_table_update.py"), "в skills (из batches)")
for f in ("scripts_inventory.py", "scripts_classify.py", "scripts_reorg.py"):
    copy(os.path.join(BA, "tools", f), os.path.join(PL, f), "в skills (из batches)")
for f in ("probe_pocket.py", "probe_narrow_slot.py", "export_families.py"):
    copy(os.path.join(SCR, f), os.path.join(PA, f), "в skills (из сессии)")
for f in ("dxf_ray.py", "dxf_window_png.py", "dxf_find_texts.py"):
    copy(os.path.join(SCR, f), os.path.join(DW, f), "в skills (из сессии)")
# 3. все .py из batches -> архив (структура папок сохраняется)
for dp, dn, fn in os.walk(BA):
    for f in fn:
        if f.endswith(".py"):
            src = os.path.join(dp, f); dst = os.path.join(AR, "batches", os.path.relpath(src, BA))
            if os.path.abspath(src) == os.path.abspath(__file__):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True); h = md5(src); shutil.move(src, dst)
            log.append(["batches → архив", src, dst, h])
# 4. плагин: старый снимок skills -> архив, новый — копия skills
PS = os.path.join(BIM, "plugin", "fst-bim", "skills")
shutil.move(PS, os.path.join(AR, "plugin_skills_old")); log.append(["снимок плагина → архив", PS, os.path.join(AR, "plugin_skills_old"), ""])
ign = shutil.ignore_patterns("__pycache__", "*.pyc", "*-workspace")
for d in sorted(os.listdir(SK)):
    s = os.path.join(SK, d)
    if os.path.isdir(s) and os.path.exists(os.path.join(s, "SKILL.md")):
        shutil.copytree(s, os.path.join(PS, d), ignore=ign); log.append(["плагин ← skills", s, os.path.join(PS, d), ""])
with open(os.path.join(AR, "manifest.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh, delimiter=";"); w.writerow(["действие", "откуда", "куда", "md5"]); w.writerows(log)
from collections import Counter
print(dict(Counter(r[0] for r in log)))
