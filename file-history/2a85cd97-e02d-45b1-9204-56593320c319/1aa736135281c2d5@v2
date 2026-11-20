# -*- coding: utf-8 -*-
# Переименование типов (Element.Name) — у типов стен «Имя типа» через параметр только для чтения.
# Аргументы: renames [[id, "новое имя"], ...], dry_run (true — всё откатывается).
# Проверки: новое имя не занято другим типом того же класса; после записи имя перечитано; число стен каждого типа не изменилось.
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
DRY = bool(args.get("dry_run", True))
rows = []; bad = 0


def walls_of(t):
    return sum(1 for w in FilteredElementCollector(doc).OfClass(Wall) if w.WallType.Id == t.Id) if isinstance(t, WallType) else None


tg = TransactionGroup(doc, u"FT: переименование типов"); tg.Start()
t = None
try:
    t = Transaction(doc, u"FT: переименование типов"); t.Start()
    for tid, new in args["renames"]:
        e = doc.GetElement(ElementId(int(tid)))
        r = {"id": tid, "old": e.Name if e else None, "new": new}
        if e is None:
            r["error"] = u"нет элемента"; bad += 1; rows.append(r); continue
        taken = [x for x in FilteredElementCollector(doc).OfClass(type(e)) if x.Name == new and x.Id != e.Id]
        if taken:
            r["error"] = u"имя занято (%d)" % taken[0].Id.Value; bad += 1; rows.append(r); continue
        n0 = walls_of(e)
        try:
            e.Name = new
        except Exception as ex:
            r["error"] = str(ex); bad += 1; rows.append(r); continue
        r["read_back"] = doc.GetElement(e.Id).Name
        r["walls"] = [n0, walls_of(e)]
        if r["read_back"] != new or n0 != r["walls"][1]:
            r["error"] = u"не совпало"; bad += 1
        rows.append(r)
    st = t.Commit(); t = None
finally:
    if t is not None and t.HasStarted() and not t.HasEnded():
        t.RollBack()
    if DRY or bad:
        tg.RollBack()
    else:
        tg.Assimilate()
res = {"dry_run": DRY, "applied": (not DRY and not bad), "errors": bad, "warnings": len(doc.GetWarnings()), "rows": rows}
__output__ = {"status": "completed_unverified" if not bad else "partial",
              "summary": u"%s: типов %d, ошибок %d%s" % (u"ПРОБНО (откат)" if DRY else u"ПРИМЕНЕНО" if not bad else u"ОТКАЧЕНО из-за ошибок", len(rows), bad, ""),
              "result": res}
