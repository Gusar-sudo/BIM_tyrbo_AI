# -*- coding: utf-8 -*-
# Чтение: реестр параметров (_bim\params\registry.csv) и ФОП против всех открытых проектов —
# есть ли параметр, совпадает ли GUID, нет ли одноимённых с другим GUID. Аргументы: registry_csv, spf_path.
import json, io
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
reg = {}
for i, line in enumerate(io.open(a["registry_csv"], encoding="utf-8-sig").read().splitlines()):
    c = line.split(";")
    if i == 0 or len(c) < 2 or not c[0]:
        continue
    reg[c[0]] = c[1].strip().lower()
fop = {}
txt = io.open(a["spf_path"], encoding="utf-16").read()
for line in txt.splitlines():
    c = line.split("\t")
    if c and c[0] == "PARAM":
        fop[c[2]] = c[1].lower()
res = {"registry": len(reg), "fop": len(fop),
       "in_fop_not_registry": sorted(set(fop) - set(reg)),
       "registry_ft_not_in_fop": sorted(n for n in reg if n.startswith("FT_") and n not in fop),
       "guid_registry_vs_fop": [[n, reg[n], fop[n]] for n in reg if n in fop and reg[n] != fop[n]], "docs": {}}
for d in app.Documents:
    if d.IsFamilyDocument:
        continue
    sp = {}
    for e in FilteredElementCollector(d).OfClass(SharedParameterElement):
        sp.setdefault(e.Name, set()).add(str(e.GuidValue).lower())
    r = {"missing": [], "other_guid": [], "dup_names": [n for n, g in sp.items() if len(g) > 1 and (n.startswith("FT_") or n.startswith("ADSK_"))]}
    for n, g in reg.items():
        if not g:
            continue
        if n not in sp:
            r["missing"].append(n)
        elif g not in sp[n]:
            r["other_guid"].append([n, g, sorted(sp[n])])
    res["docs"][d.Title[:30]] = r
bad = len(res["guid_registry_vs_fop"]) + sum(len(r["other_guid"]) + len(r["dup_names"]) for r in res["docs"].values())
__output__ = {"status": "completed_unverified", "summary": u"реестр %d, ФОП %d, расхождений GUID/дублей %d" % (len(reg), len(fop), bad), "result": res}
