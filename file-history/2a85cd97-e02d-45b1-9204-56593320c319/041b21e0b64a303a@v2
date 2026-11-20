# -*- coding: utf-8 -*-
# Только чтение: для всех семейств профилей, на которые ссылаются типы импостов активного проекта,
# выгрузить кривые графики узла (вложенное «Элементы узлов»; группы и линии вне групп) в out_dir\<семейство>.json.
# Профиль без вложенной графики помечается. Аргументы: out_dir, only (необяз. список имён семейств)
import json, io, os
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)


def mm(p):
    return [round(p.X * FT, 4), round(p.Y * FT, 4)]


DET = ("DetailLine", "DetailArc", "DetailNurbSpline", "DetailEllipse", "DetailCurve")
usage = {}
for m in FilteredElementCollector(doc).OfClass(MullionType):
    s = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
    if s is not None:
        usage.setdefault(s.Family.Name, []).append(m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
names = sorted(usage) if not args.get("only") else args["only"]
rows = []
for i, n in enumerate(names):
    checkpoint(n, i, len(names))
    r = {"family": n, "types": len(usage.get(n, []))}
    pd = None
    try:
        pd = doc.EditFamily(fams[n])
        fis = list(FilteredElementCollector(pd).OfClass(FamilyInstance))
        if not fis:
            r["nested"] = None; rows.append(r); continue
        fi = fis[0]; T = fi.GetTotalTransform()
        nd = pd.EditFamily(fi.Symbol.Family)
        try:
            sets = [(g.GroupType.Name, [nd.GetElement(x) for x in g.GetMemberIds()]) for g in FilteredElementCollector(nd).OfClass(Group)]
            free = [e for e in FilteredElementCollector(nd).OfClass(CurveElement) if e.GroupId == ElementId.InvalidElementId and e.GetType().Name in DET]
            if free:
                sets.append((u"_вне групп", free))
            groups = []
            for gname, members in sets:
                cs = []
                for el in members:
                    if isinstance(el, CurveElement) and el.GeometryCurve is not None and el.GetType().Name in DET:
                        c = el.GeometryCurve
                        if isinstance(c, Line):
                            cs.append(["L"] + mm(c.GetEndPoint(0)) + mm(c.GetEndPoint(1)))
                        elif isinstance(c, Arc) and c.IsBound:
                            cs.append(["A"] + mm(c.GetEndPoint(0)) + mm(c.Evaluate(0.5, True)) + mm(c.GetEndPoint(1)))
                        elif isinstance(c, Arc):
                            cs.append(["C", round(c.Center.X * FT, 4), round(c.Center.Y * FT, 4), round(c.Radius * FT, 4)])
                        else:
                            cs.append(["P", [mm(p) for p in c.Tessellate()]])
                groups.append({"name": gname, "curves": cs})
            fr = len(list(FilteredElementCollector(nd).OfClass(FilledRegion)))
            r.update(nested=fi.Symbol.Family.Name, groups=len(groups), curves=sum(len(g["curves"]) for g in groups), fills_now=fr)
            io.open(os.path.join(OUT, n + u".json"), "w", encoding="utf-8").write(json.dumps({"groups": groups, "mirrored": fi.Mirrored, "family": n}, ensure_ascii=False))
        finally:
            nd.Close(False)
    except Exception as ex:
        r["error"] = str(ex)[:150]
    finally:
        if pd is not None:
            pd.Close(False)
    rows.append(r)
io.open(os.path.join(OUT, u"_index.json"), "w", encoding="utf-8").write(json.dumps({"rows": rows, "usage": usage}, ensure_ascii=False))
__output__ = {"status": "completed_unverified", "summary": u"профилей %d: выгружено %d, без графики %d, ошибок %d; ничего не менялось" % (
    len(rows), sum(1 for r in rows if r.get("curves")), sum(1 for r in rows if r.get("nested") is None and "error" not in r), sum(1 for r in rows if "error" in r)),
    "no_nested": [r["family"] for r in rows if r.get("nested") is None and "error" not in r][:40], "errors": [[r["family"], r["error"]] for r in rows if "error" in r][:20],
    "already_filled": [r["family"] for r in rows if r.get("fills_now")][:20]}
