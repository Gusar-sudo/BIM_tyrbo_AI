# -*- coding: utf-8 -*-
# Загрузка семейств из rfa (перезапись), dry_run — с откатом. Аргументы: rfas [пути], dry_run.
import json, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
DRY = bool(args.get("dry_run", True))


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


res = {"loaded": [], "failed": []}
t = Transaction(doc, u"FT: загрузка семейств"); t.Start()
try:
    for f in args["rfas"]:
        (res["loaded"] if doc.LoadFamily(f, LO(), clr.Reference[Family]()) else res["failed"]).append(f.split("\\")[-1])
    res["warnings"] = len(doc.GetWarnings())
    if DRY:
        t.RollBack()
    else:
        t.Commit()
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
__output__ = {"status": "completed_unverified" if not res["failed"] else "partial", "summary": (u"ПРОБА (откат): " if DRY else u"ПРИМЕНЕНО: ") + u"загружено %d, не загружено %d, предупреждений %s" % (len(res["loaded"]), len(res["failed"]), res["warnings"]), "r": res}
