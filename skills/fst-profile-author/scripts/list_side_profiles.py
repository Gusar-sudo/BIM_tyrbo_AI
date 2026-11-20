# -*- coding: utf-8 -*-
# Чтение: боковые профили «Боковой…» и типы краёв по стойкам: «примыкание к стене/полу/потолку/двери» и свободный край
# «не доходит до стены» (профили «…Закрытый»). Модель не меняется.
# Аргументы: stands [обозначения стоек, например ["FSC22", "FSC01К"]]
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
st = args["stands"]
fams = sorted(f.Name for f in FilteredElementCollector(doc).OfClass(Family) if f.Name.startswith(u"BIMLIB_Профиль_") and u"_Боковой" in f.Name and any((u"_%s_" % s) in f.Name for s in st))
mt = {}
for m in FilteredElementCollector(doc).OfClass(MullionType):
    n = m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    if (u"примыкание к" in n or u"не доходит до стены" in n) and any((u" %s " % s) in n for s in st):
        pe = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
        mt[n] = pe.Family.Name.replace(u"BIMLIB_Профиль_", u"") if pe and hasattr(pe, "Family") else None
__output__ = {"status": "completed_unverified", "summary": "профилей %d, типов %d" % (len(fams), len(mt)), "profiles": fams, "types": mt}
