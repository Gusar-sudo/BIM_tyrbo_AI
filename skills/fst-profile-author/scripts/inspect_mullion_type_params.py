# -*- coding: utf-8 -*-
# Чтение: все параметры заданных типов импостов (имя -> значение). Аргументы: types [имена]
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
mt = dict((m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
out = {}
for n in args["types"]:
    m = mt.get(n)
    if m is None:
        out[n] = None; continue
    row = {}
    for p in m.Parameters:
        try:
            if p.StorageType == StorageType.ElementId:
                e = doc.GetElement(p.AsElementId()); v = e.Name if e else None
            elif p.StorageType == StorageType.String:
                v = p.AsString()
            else:
                v = p.AsValueString()
            row[p.Definition.Name] = v
        except Exception:
            pass
    out[n] = row
# только отличающиеся параметры
keys = sorted(set(k for r in out.values() if r for k in r))
diff = dict((k, dict((n, (out[n] or {}).get(k)) for n in out)) for k in keys if len(set(str((out[n] or {}).get(k)) for n in out)) > 1)
__output__ = {"status": "completed_unverified", "summary": "типов %d, различающихся параметров %d" % (len(out), len(diff)), "diff": diff}
