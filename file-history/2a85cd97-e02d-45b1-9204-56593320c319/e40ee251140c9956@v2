# -*- coding: utf-8 -*-
# ШАБЛОН скрипта записи в Revit (horizun_execute_python). Новый скрипт записи — копировать отсюда.
# Правила (lessons.md, разд. 2): проба = та же запись + откат; транзакции закрываются при любой ошибке;
# документ семейства (EditFamily) закрывается fd.Close(False) при ошибке; после записи — перечитать и сравнить.
# Аргументы: dry_run (по умолчанию true) + свои.
import json
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
DRY = bool(a.get("dry_run", True))
res = {"dry_run": DRY, "doc": doc.Title, "changed": [], "mismatch": []}


def edit_family(fam, work):
    """Правка семейства: work(fd) внутри транзакции; при ошибке — откат и закрытие без сохранения. Возвращает fd (открыт)."""
    fd = doc.EditFamily(fam)
    t = Transaction(fd, u"FT: правка семейства"); t.Start()
    try:
        work(fd)
        t.Commit()
    except Exception:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        fd.Close(False)
        raise
    return fd  # дальше: fd.SaveAs(...) / doc.LoadFamily(...), затем fd.Close(False)


t = Transaction(doc, a.get("transaction_name", u"FT: запись")); t.Start()
try:
    # --- запись ---
    # p.Set(...); res["changed"].append(...)
    doc.Regenerate()
    # --- перечитать после Regenerate и сравнить с заданным; расхождение -> res["mismatch"] ---
    if DRY or res["mismatch"]:
        t.RollBack(); res["committed"] = False
    else:
        t.Commit(); res["committed"] = True
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
res["status"] = "completed_unverified" if not res["mismatch"] else "partial"
res["summary"] = u"%s%d изменений, расхождений %d" % (u"ПРОБА (откат): " if DRY else u"", len(res["changed"]), len(res["mismatch"]))
__output__ = res
