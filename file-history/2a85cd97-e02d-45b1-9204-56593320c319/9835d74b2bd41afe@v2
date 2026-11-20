# -*- coding: utf-8 -*-
# Размер заполнения в спецификации = геометрии: FT_Стекло_Ширина = Ш + 2·«Выступ сбоку» + поправка,
# FT_Стекло_Высота = В + «Выступ сверху» + «Выступ снизу» + поправка (раньше — через FT_Стекло_Добавка).
# Сохраняет КОПИИ .rfa в out_dir; проект не меняется. Аргументы: families, out_dir.
import json, os
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
FW = u"if(FT_Система_М1, 0 мм, rounddown((ADSK_Размер_Ширина + 2 * Выступ сбоку + FT_Стекло_Поправка_Ширина) / 1 мм) * 1 мм)"
FH = u"if(FT_Система_М1, 0 мм, rounddown((ADSK_Размер_Высота + Выступ сверху + Выступ снизу + FT_Стекло_Поправка_Высота) / 1 мм) * 1 мм)"
rows = []
for n in args["families"]:
    r = {"family": n}
    fd = doc.EditFamily(fams[n])
    try:
        fm = fd.FamilyManager; P = dict((p.Definition.Name, p) for p in fm.Parameters)
        t = Transaction(fd, u"FT: размер стекла по выступам"); t.Start()
        try:
            fm.SetFormula(P[u"FT_Стекло_Ширина"], FW); fm.SetFormula(P[u"FT_Стекло_Высота"], FH)
            t.Commit()
        except Exception:
            t.RollBack(); raise
        r["formulas"] = [P[u"FT_Стекло_Ширина"].Formula, P[u"FT_Стекло_Высота"].Formula]
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        r["rfa"] = os.path.join(OUT, n + u".rfa"); fd.SaveAs(r["rfa"], so); r["ok"] = True
    except Exception:
        import traceback
        r["error"] = traceback.format_exc()[-400:]
    finally:
        fd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified" if all(x.get("ok") for x in rows) else "partial", "summary": u"семейств %d из %d; проект не менялся" % (sum(1 for x in rows if x.get("ok")), len(rows)), "rows": rows}
