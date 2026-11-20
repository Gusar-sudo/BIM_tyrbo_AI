# -*- coding: utf-8 -*-
# ПРИМЕНЕНИЕ: перезагрузить семейства в АКТИВНЫЙ документ из другого открытого документа (напр. библиотеки):
# source_doc (заголовок), names [] или name_prefix; до/после — пересечения импостов с панелями, импосты без геометрии,
# предупреждения. Не сохраняет. Аргументы: source_doc, names | name_prefix, out_json
import json, io
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
src = [d for d in __revit__.Application.Documents if d.Title == args["source_doc"]][0]


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src_, b):
        src_.Value = FamilySource.Family; b.Value = True; return True


opt = Options()
panels = List[ElementId](FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType().ToElementIds())


def snapshot():
    clash = 0; nogeo = 0; n = 0
    for m in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType():
        n += 1
        g = m.get_Geometry(opt)
        if g is None or not any(True for _ in g): nogeo += 1; continue
        try:
            if FilteredElementCollector(doc, panels).WherePasses(ElementIntersectsElementFilter(m)).GetElementCount(): clash += 1
        except Exception: pass
    return {"mullions": n, "clash": clash, "nogeo": nogeo, "warnings": len(doc.GetWarnings())}


fams = [f for f in FilteredElementCollector(src).OfClass(Family)
        if (args.get("names") and f.Name in args["names"]) or (args.get("name_prefix") and f.Name.startswith(args["name_prefix"]))]
res = {"before": snapshot(), "loaded": 0, "failed": [], "found": len(fams)}
for i, f in enumerate(fams):
    checkpoint(f.Name, i, len(fams))
    fd = src.EditFamily(f)
    try:
        fd.LoadFamily(doc, LO()); res["loaded"] += 1
    except Exception as ex:
        res["failed"].append(f.Name + ": " + str(ex)[:80])
    finally:
        fd.Close(False)
res["after"] = snapshot()
if args.get("out_json"):
    io.open(args["out_json"], "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
ok = not res["failed"] and res["after"]["clash"] <= res["before"]["clash"] and res["after"]["nogeo"] == 0
__output__ = {"status": "completed_unverified" if ok else "partial", "summary": u"из «%s»: найдено %d, загружено %d; коллизий %d→%d; предупреждений %d→%d; не сохранено" % (
    args["source_doc"], len(fams), res["loaded"], res["before"]["clash"], res["after"]["clash"], res["before"]["warnings"], res["after"]["warnings"]), "result": res}
