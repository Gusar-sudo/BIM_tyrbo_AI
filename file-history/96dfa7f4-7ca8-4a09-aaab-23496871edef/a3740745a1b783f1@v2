# -*- coding: utf-8 -*-
# ПРИМЕНЕНИЕ: загрузить семейства из rfas (замена существующих, значения параметров не переписываются). Аргументы: rfas [пути].
import json, os, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


res = []
t = Transaction(doc, u"Профили: " + args.get("label", u"загрузка")); t.Start()
try:
    for rfa in args["rfas"]:
        ok = doc.LoadFamily(rfa, LoadOpt(), clr.Reference[Family]())
        res.append([os.path.basename(rfa)[:-4][:80], bool(ok)])
    t.Commit()
finally:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
fams = set(f.Name for f in FilteredElementCollector(doc).OfClass(Family))
present = all(r[0] in fams for r in res)
__output__ = {"status": "completed_unverified" if all(r[1] for r in res) and present else "partial",
              "summary": u"загружено %d/%d, семейства в проекте: %s, предупреждений %d" % (sum(1 for r in res if r[1]), len(res), present, len(doc.GetWarnings())),
              "loaded": res}
