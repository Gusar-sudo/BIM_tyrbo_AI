# -*- coding: utf-8 -*-
# Сохранить активный документ на диск (doc.Save) и сообщить результат. Проверку файла делает Claude отдельно (дата/размер).
from Autodesk.Revit.DB import *
doc = __revit__.ActiveUIDocument.Document
res = {"path": doc.PathName, "modified_before": doc.IsModified}
try:
    doc.Save()
    res.update(saved=True, status="completed_unverified", summary=u"doc.Save() отработал")
except Exception as ex:
    res.update(saved=False, error=str(ex), status="failed", summary=u"doc.Save() отказал")
res["modified_after"] = doc.IsModified
__output__ = res
