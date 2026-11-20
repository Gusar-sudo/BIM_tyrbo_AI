# -*- coding: utf-8 -*-
# В архив неиспользуемое: (1) типы панелей семейств panel_families по списку имён (если 0 экземпляров и не панель по умолчанию
# ни в одном типе стены) — перед удалением семейство панели сохраняется .rfa в archive_dir; (2) типы импостов по списку
# (0 экземпляров, не в типах стен) и их семейства профилей (если профилем больше никто не пользуется) — .rfa в архив.
# dry_run=true — только отчёт, ничего не удаляется и не сохраняется.
import json, io, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    a2 = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read()); a2.update(dict((k, v) for k, v in args.items() if k != "args_file")); args = a2
doc = __revit__.ActiveUIDocument.Document
DRY = bool(args.get("dry_run", True)); AD = args["archive_dir"]
nm = lambda e: Element.Name.GetValue(e)
res = {"dry_run": DRY, "panel_types": [], "panel_kept": [], "mullion_types": [], "mullion_kept": [], "profile_families": [], "saved": []}
used_types = set(x.GetTypeId().Value for x in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType())
used_mt = set(x.GetTypeId().Value for x in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType())
wall_refs = set()
for w in FilteredElementCollector(doc).OfClass(WallType):
    if w.Kind != WallKind.Curtain:
        continue
    for p in w.Parameters:
        if p.StorageType == StorageType.ElementId:
            wall_refs.add(p.AsElementId().Value)
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
del_ids = []; save_fams = set()
for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels):
    if s.Family.Name not in args["panel_families"] or s.Name not in args["panel_types"]:
        continue
    if s.Id.Value in used_types or s.Id.Value in wall_refs:
        res["panel_kept"].append([s.Name, u"используется"]); continue
    res["panel_types"].append([s.Family.Name.replace(u"BIMLIB_ПанельВитража_", u""), s.Name]); del_ids.append(s.Id); save_fams.add(s.Family.Name)
mts = list(FilteredElementCollector(doc).OfClass(MullionType))
prof_users = {}
for m in mts:
    pe = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
    if pe is not None and hasattr(pe, "Family"):
        prof_users.setdefault(pe.Family.Name, []).append(m)
for m in mts:
    if nm(m) not in args.get("mullion_types", []):
        continue
    if m.Id.Value in used_mt or m.Id.Value in wall_refs:
        res["mullion_kept"].append([nm(m), u"используется"]); continue
    res["mullion_types"].append(nm(m)); del_ids.append(m.Id)
    pe = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
    fn = pe.Family.Name if pe is not None and hasattr(pe, "Family") else None
    if fn and all(nm(x) in args["mullion_types"] for x in prof_users.get(fn, [])) and fn not in res["profile_families"]:
        res["profile_families"].append(fn); save_fams.add(fn); del_ids.append(fams[fn].Id)
if not DRY:
    if not os.path.isdir(AD):
        os.makedirs(AD)
    for fn in sorted(save_fams):
        fd = doc.EditFamily(fams[fn])
        try:
            so = SaveAsOptions(); so.OverwriteExistingFile = True
            pth = os.path.join(AD, fn + u".rfa"); fd.SaveAs(pth, so); res["saved"].append(pth)
        finally:
            fd.Close(False)
    t = Transaction(doc, u"FT: неиспользуемое — в архив"); t.Start()
    try:
        doc.Delete(List[ElementId](del_ids)); t.Commit()
    except Exception:
        t.RollBack(); raise
    res["warnings"] = len(doc.GetWarnings())
__output__ = {"status": "completed_unverified", "summary": (u"ПРОБА: " if DRY else u"ПРИМЕНЕНО: ") + u"типов панелей %d (оставлено %d), типов импостов %d, семейств профилей %d, сохранено rfa %d" % (len(res["panel_types"]), len(res["panel_kept"]), len(res["mullion_types"]), len(res["profile_families"]), len(res["saved"])), "r": res}
