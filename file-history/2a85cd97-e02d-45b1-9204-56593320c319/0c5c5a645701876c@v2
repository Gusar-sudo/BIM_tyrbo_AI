# -*- coding: utf-8 -*-
# Чтение: общие параметры ADSK_ из документа (имя, GUID, тип данных, используются ли семействами Фристайл) -> CSV строк реестра.
# Одноимённые с разными GUID помечаются «ДУБЛЬ». Аргументы: out_csv, document_title (необязательно; иначе активный).
import json, io, os
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
if a.get("document_title"):
    doc = [d for d in app.Documents if d.Title == a["document_title"]][0]
# какие ADSK встречаются в типах импостов/панелей/стен Фристайл
used = {}
cats = [BuiltInCategory.OST_CurtainWallMullions, BuiltInCategory.OST_CurtainWallPanels, BuiltInCategory.OST_Walls, BuiltInCategory.OST_Doors]
for c in cats:
    for e in FilteredElementCollector(doc).OfCategory(c).WhereElementIsElementType():
        for p in e.Parameters:
            n = p.Definition.Name
            if n.startswith(u"ADSK_") and p.IsShared:
                used.setdefault(n, set()).add(LabelUtils.GetLabelForGroup(p.Definition.GetGroupTypeId()) if hasattr(p.Definition, "GetGroupTypeId") else "")
rows = {}
for e in FilteredElementCollector(doc).OfClass(SharedParameterElement):
    n = e.Name
    if not n.startswith(u"ADSK_"):
        continue
    d = e.GetDefinition()
    try:
        dt = LabelUtils.GetLabelForSpec(d.GetDataType())
    except Exception:
        dt = ""
    rows.setdefault(n, []).append((str(e.GuidValue), dt))
out = [u"name;guid;data_type;instance_or_type;group;tooltip;owner;used_by;status;source"]
for n in sorted(rows):
    dup = len(set(g for g, _ in rows[n])) > 1
    for g, dt in rows[n]:
        out.append(u"%s;%s;%s;;%s;;ADSK;%s;%s;модель %s %s" % (
            n, g, dt, u"/".join(sorted(used.get(n, []))), u"витраж/импост/панель/дверь" if n in used else u"шаблон (не в семействах Фристайл)",
            u"ДУБЛЬ имени — разобрать" if dup else u"действует", doc.Title[:20], u"14.11.2026"))
d = os.path.dirname(a["out_csv"])
if d and not os.path.isdir(d):
    os.makedirs(d)
with io.open(a["out_csv"], "w", encoding="utf-8-sig") as f:
    f.write(u"\n".join(out) + u"\n")
__output__ = {"status": "completed_unverified", "summary": u"ADSK общих: %d имён, %d строк, используются семействами: %d, дублей имён: %d" % (
    len(rows), len(out) - 1, len(used), sum(1 for n in rows if len(set(g for g, _ in rows[n])) > 1)), "out_csv": a["out_csv"]}
