# -*- coding: utf-8 -*-
# Только чтение: точные кривые графики узла (вложенное семейство «Элементы узлов») в координатах ВЛОЖЕННОГО, мм.
# Профиль берётся из .rfa (rfa_path) или из проекта (family). Для каждой группы: отрезки ["L",x1,y1,x2,y2],
# дуги ["A",x1,y1,xm,ym,x2,y2], прочее — ломаной ["P",[[x,y]...]]; плюс заливки (FilledRegion) с именем типа.
# Также пишет преобразование вложенный -> профиль (T, mirrored). Аргументы: rfa_path | family, dump_path
import json, io
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8


def mm(p):
    return [round(p.X * FT, 4), round(p.Y * FT, 4)]


pd = __revit__.Application.OpenDocumentFile(args["rfa_path"]) if args.get("rfa_path") else doc.EditFamily([f for f in FilteredElementCollector(doc).OfClass(Family) if f.Name == args["family"]][0])
res = {"groups": [], "regions": []}
try:
    fi = list(FilteredElementCollector(pd).OfClass(FamilyInstance))[0]
    T = fi.GetTotalTransform()
    res["nested_family"] = fi.Symbol.Family.Name; res["mirrored"] = fi.Mirrored
    res["T"] = {"origin": mm(T.Origin), "bx": [T.BasisX.X, T.BasisX.Y], "by": [T.BasisY.X, T.BasisY.Y]}
    nd = pd.EditFamily(fi.Symbol.Family)
    try:
        sets = [(g.GroupType.Name, [nd.GetElement(m) for m in g.GetMemberIds()]) for g in FilteredElementCollector(nd).OfClass(Group)]
        free = [e for e in FilteredElementCollector(nd).OfClass(CurveElement) if e.GroupId == ElementId.InvalidElementId and e.GetType().Name in ("DetailLine", "DetailArc", "DetailNurbSpline", "DetailEllipse", "DetailCurve")]
        if free:
            sets.append((u"_вне групп", free))   # линии, не собранные в группы (после правки профиля)
        for gname, members in sets:
            cs = []
            for el in members:
                if isinstance(el, CurveElement) and el.GeometryCurve is not None:
                    c = el.GeometryCurve
                    if isinstance(c, Line):
                        cs.append(["L"] + mm(c.GetEndPoint(0)) + mm(c.GetEndPoint(1)))
                    elif isinstance(c, Arc) and c.IsBound:
                        cs.append(["A"] + mm(c.GetEndPoint(0)) + mm(c.Evaluate(0.5, True)) + mm(c.GetEndPoint(1)))
                    elif isinstance(c, Arc):
                        ctr = c.Center; r = c.Radius
                        cs.append(["C", round(ctr.X * FT, 4), round(ctr.Y * FT, 4), round(r * FT, 4)])
                    else:
                        cs.append(["P", [mm(p) for p in c.Tessellate()]])
            res["groups"].append({"name": gname, "curves": cs})
        for fr in FilteredElementCollector(nd).OfClass(FilledRegion):
            t = nd.GetElement(fr.GetTypeId())
            res["regions"].append({"type": t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), "in_group": fr.GroupId != ElementId.InvalidElementId})
    finally:
        nd.Close(False)
finally:
    pd.Close(False)
io.open(args["dump_path"], "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False))
__output__ = {"status": "completed_unverified", "summary": u"групп %d, заливок %d; ничего не менялось" % (len(res["groups"]), len(res["regions"])),
              "groups": [[g["name"], len(g["curves"]), sorted(set(c[0] for c in g["curves"]))] for g in res["groups"]],
              "region_types": sorted(set(r["type"] for r in res["regions"])), "mirrored": res.get("mirrored"), "T": res.get("T")}
