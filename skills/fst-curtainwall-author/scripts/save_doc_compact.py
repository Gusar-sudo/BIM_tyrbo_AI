# -*- coding: utf-8 -*-
# Сохранить активный документ НА ТО ЖЕ МЕСТО со сжатием (SaveAs Compact + перезапись) — убирает «мусор» после
# многократных перезагрузок семейств. Проверку файла (дата/размер) делает Claude отдельно.
from Autodesk.Revit.DB import *
doc = __revit__.ActiveUIDocument.Document
res = {"path": doc.PathName, "modified_before": doc.IsModified}
try:
    o = SaveAsOptions(); o.OverwriteExistingFile = True; o.Compact = True
    doc.SaveAs(doc.PathName, o)
    res.update(saved=True, status="completed_unverified", summary=u"SaveAs(Compact) отработал")
except Exception as ex:
    res.update(saved=False, error=str(ex)[:200], status="failed", summary=u"SaveAs(Compact) отказал")
res["modified_after"] = doc.IsModified
__output__ = res
