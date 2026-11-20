# -*- coding: utf-8 -*-
# Профиль у потолка: заливка ленты (FilledRegion типа region_type) во вложенной графике отражается зеркально
# (вложенное взято от профиля у пола без отражения). Плоскость отражения — ось nested_axis ("X" или "Y") вложенного семейства.
# Аргументы: families [имена профилей], region_type, nested_axis, out_dir. Сохраняет КОПИИ .rfa; проект не меняется.
import json, io, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


rows = []
for n in args["families"]:
    r = {"family": n}
    pd = doc.EditFamily(fams[n]); nd = None
    try:
        fi = list(FilteredElementCollector(pd).OfClass(FamilyInstance))[0]
        nd = pd.EditFamily(fi.Symbol.Family)
        v = [x for x in FilteredElementCollector(nd).OfClass(View) if not x.IsTemplate][0]
        regs = [fr for fr in FilteredElementCollector(nd).OfClass(FilledRegion) if nd.GetElement(fr.GetTypeId()).Name == args["region_type"]]
        bb0 = [regs[0].get_BoundingBox(v).Min, regs[0].get_BoundingBox(v).Max] if regs else None
        normal = XYZ.BasisY if args.get("nested_axis", "Y") == "Y" else XYZ.BasisX
        t = Transaction(nd, u"FT: отразить ленту"); t.Start()
        try:
            ElementTransformUtils.MirrorElements(nd, List[ElementId]([x.Id for x in regs]), Plane.CreateByNormalAndOrigin(normal, XYZ.Zero), False)
            t.Commit()
        except Exception:
            t.RollBack(); raise
        regs2 = [fr for fr in FilteredElementCollector(nd).OfClass(FilledRegion) if nd.GetElement(fr.GetTypeId()).Name == args["region_type"]]
        b2 = regs2[0].get_BoundingBox(v)
        r["band_before_mm"] = [[round(p.X * FT, 1), round(p.Y * FT, 1)] for p in bb0] if bb0 else None
        r["band_after_mm"] = [[round(b2.Min.X * FT, 1), round(b2.Min.Y * FT, 1)], [round(b2.Max.X * FT, 1), round(b2.Max.Y * FT, 1)]]
        r["regions"] = [len(regs), len(regs2)]
        nd.LoadFamily(pd, LO()); nd.Close(False); nd = None
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        r["rfa"] = os.path.join(OUT, n + u".rfa"); pd.SaveAs(r["rfa"], so); r["ok"] = True
    except Exception:
        import traceback
        r["error"] = traceback.format_exc()[-400:]
    finally:
        if nd is not None:
            nd.Close(False)
        pd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified" if all(x.get("ok") for x in rows) else "partial", "summary": u"отражено %d из %d; проект не менялся" % (sum(1 for x in rows if x.get("ok")), len(rows)), "rows": rows}
