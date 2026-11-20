# -*- coding: utf-8 -*-
# Только чтение: отрезки собственного контура профиля и вложенной графики в окне у фасадного стекла.
# Аргументы: mullion_types [имена], win [x0,y0,x1,y1] мм. Документы семейств закрываются без сохранения.
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
x0, y0, x1, y1 = args["win"]
mts = dict((Element.Name.GetValue(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))


def segs_of(curves, tr=None, flip=(1.0, 1.0)):
    # flip: отражение вложенного экземпляра (HandFlipped -> x, FacingFlipped -> y) — GetTotalTransform его не учитывает
    out = []
    for g in curves:
        ps = [(tr.OfPoint(XYZ(flip[0] * q.X, flip[1] * q.Y, q.Z)) if tr else q) for q in g.Tessellate()]
        ps = [(round(p.X * FT, 3), round(p.Y * FT, 3)) for p in ps]
        for i in range(len(ps) - 1):
            a, b = ps[i], ps[i + 1]
            if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1 or max(a[1], b[1]) < y0 or min(a[1], b[1]) > y1:
                continue
            out.append([a[0], a[1], b[0], b[1]])
    return out


out = {}
for n in args["mullion_types"]:
    m = mts.get(n)
    if m is None:
        out[n] = u"нет типа"; continue
    pe = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
    pd = doc.EditFamily(pe.Family)
    r = {"family": pe.Family.Name}
    try:
        r["own"] = segs_of([c.GeometryCurve for c in FilteredElementCollector(pd).OfClass(CurveElement) if c.GeometryCurve is not None and c.GetType().Name in ("DetailLine", "DetailCurve", "DetailArc")])
        nested = []
        for fi in FilteredElementCollector(pd).OfClass(FamilyInstance):
            tr = fi.GetTotalTransform(); nd = pd.EditFamily(fi.Symbol.Family)
            fl = (-1.0 if fi.HandFlipped else 1.0, -1.0 if fi.FacingFlipped else 1.0)
            try:
                nested += segs_of([c.GeometryCurve for c in FilteredElementCollector(nd).OfClass(CurveElement) if c.GeometryCurve is not None], tr, fl)
            finally:
                nd.Close(False)
        r["nested"] = nested
    finally:
        pd.Close(False)
    out[n] = r
if args.get("dump"):
    import io
    with io.open(args["dump"], "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, ensure_ascii=False))
__output__ = {"status": "completed_unverified", "summary": u"только чтение, профилей %d" % len(out), "types": list(out.keys())}
