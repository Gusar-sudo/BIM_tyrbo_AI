# -*- coding: utf-8 -*-
# Открыть и активировать документ (тестовый проект). Модели не меняет.
# Аргументы: path
import json
args = json.loads(HORIZUN_ARGS_JSON)
uidoc = __revit__.OpenAndActivateDocument(args["path"])
d = uidoc.Document
__output__ = {"status": "completed_unverified", "summary": u"Открыт: " + d.Title, "title": d.Title, "path": d.PathName}
