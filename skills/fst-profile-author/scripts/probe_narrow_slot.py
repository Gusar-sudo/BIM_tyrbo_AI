# -*- coding: utf-8 -*-
# Только чтение: все семейства профилей М2/М3 — есть ли в 3D-теле узкий вырез под стекло (ступень на |y| = 25,6 М2 / 30,7 М3,
# т. е. линия вдоль стены на этой высоте) и широкий (|y| 17,9/15,5 М2, 24,7/20,6 М3). Семейства закрываются без сохранения.
import json, re
from Autodesk.Revit.DB import *
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
NAR = {u"М2": 25.6, u"М3": 30.7}
out = []
for f in FilteredElementCollector(doc).OfClass(Family):
    m = re.search(u"Профиль_(М2|М3)_(FSC\\d+К?)_(\\w+?)_Фристайл", f.Name)
    if not m:
        continue
    y0 = NAR[m.group(1)]
    fd = doc.EditFamily(f)
    try:
        hz = []
        for ce in FilteredElementCollector(fd).OfClass(CurveElement):
            if ce.GetType().Name not in ("DetailLine", "DetailCurve") or not isinstance(ce.GeometryCurve, Line):
                continue
            a = ce.GeometryCurve.GetEndPoint(0); b = ce.GeometryCurve.GetEndPoint(1)
            if abs(a.Y - b.Y) * FT < 0.05 and abs(abs(a.Y * FT) - y0) < 0.15 and abs(a.X - b.X) * FT > 1.0:
                hz.append([round(a.X * FT, 2), round(b.X * FT, 2), round(a.Y * FT, 2)])
        if hz:
            used = 0
            for sid in f.GetFamilySymbolIds():
                pass
            out.append([m.group(1) + u" " + m.group(2) + u" " + m.group(3), hz])
    finally:
        fd.Close(False)
out.sort()
__output__ = {"status": "completed_unverified", "summary": u"только чтение, профилей с узким вырезом %d" % len(out), "r": out}
