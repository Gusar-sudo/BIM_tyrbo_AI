# -*- coding: utf-8 -*-
# Перетипировать импосты: в стенах типа wall_type импосты типа from_type -> to_type.
# Аргументы: wall_type, from_type, to_type, dry_run (true). Пробный прогон откатывается.
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
dry = bool(args.get("dry_run", True))
mts = dict((Element.Name.GetValue(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
src = mts[args["from_type"]]; dst = mts[args["to_type"]]
walls = [w for w in FilteredElementCollector(doc).OfClass(Wall) if w.WallType.Name == args["wall_type"] and w.CurtainGrid]
res = {"walls": [w.Id.Value for w in walls], "changed": [], "fail": []}
w_before = len(doc.GetWarnings())
t = Transaction(doc, u"FT: перетипировать импосты"); t.Start()
try:
    for w in walls:
        for mid in w.CurtainGrid.GetMullionIds():
            m = doc.GetElement(mid)
            if m.GetTypeId() != src.Id:
                continue
            try:
                if m.Pinned:
                    m.Pinned = False
                m.ChangeTypeId(dst.Id)
                res["changed"].append(mid.Value)
            except Exception as ex:
                res["fail"].append([mid.Value, str(ex)])
    doc.Regenerate()
    res["check_new_type"] = sum(1 for i in res["changed"] if doc.GetElement(ElementId(i)).GetTypeId() == dst.Id)
    res["warnings_before"] = w_before; res["warnings_after"] = len(doc.GetWarnings())
    if dry:
        t.RollBack()
    else:
        res["commit"] = str(t.Commit())
except Exception as ex:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    res["error"] = str(ex)
__output__ = {"status": "failed" if res.get("error") or res["fail"] else "completed_unverified",
              "summary": u"%s: стен %d, импостов перетипировано %d (проверено %s), ошибок %d, предупр. %s→%s" % (
                  u"ПРОБНО (откат)" if dry else u"ПРИМЕНЕНО", len(walls), len(res["changed"]), res.get("check_new_type"),
                  len(res["fail"]), res.get("warnings_before"), res.get("warnings_after")), "result": res}
