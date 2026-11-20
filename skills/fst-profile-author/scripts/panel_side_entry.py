# -*- coding: utf-8 -*-
# Семейство панели витража (копия .rfa): заход стекла слева и справа отдельно.
# Добавляет параметры экземпляра FT_Стекло_Поправка_Слева/_Справа (длина) и FT_Выступ_Слева/_Справа = Выступ сбоку + поправка;
# размеры «Выступ сбоку» (слева — до плоскости «Слева», справа — до «Справа») получают новые метки;
# FT_Стекло_Ширина = Ш + FT_Выступ_Слева + FT_Выступ_Справа + FT_Стекло_Поправка_Ширина. Проект не меняется.
# Аргументы: rfas, save
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
app = __revit__.Application
SAVE = bool(args.get("save", False))
res = []
for path in args["rfas"]:
    r = {"rfa": path.split("\\")[-1], "ok": False, "labels": []}
    fd = app.OpenDocumentFile(path)
    try:
        fm = fd.FamilyManager
        t = Transaction(fd, u"заход стекла слева/справа"); t.Start()
        P = dict((p.Definition.Name, p) for p in fm.GetParameters())
        for nm in (u"FT_Стекло_Поправка_Слева", u"FT_Стекло_Поправка_Справа", u"FT_Выступ_Слева", u"FT_Выступ_Справа"):
            if nm not in P:
                P[nm] = fm.AddParameter(nm, GroupTypeId.Geometry, SpecTypeId.Length, True)
        # значение по умолчанию у поправок 0
        for tp in fm.Types:
            fm.CurrentType = tp
            fm.Set(P[u"FT_Стекло_Поправка_Слева"], 0.0); fm.Set(P[u"FT_Стекло_Поправка_Справа"], 0.0)
        fm.SetFormula(P[u"FT_Выступ_Слева"], u"Выступ сбоку + FT_Стекло_Поправка_Слева")
        fm.SetFormula(P[u"FT_Выступ_Справа"], u"Выступ сбоку + FT_Стекло_Поправка_Справа")
        vs = P[u"Выступ сбоку"]
        for d in FilteredElementCollector(fd).OfClass(Dimension):
            try:
                lab = d.FamilyLabel
            except Exception:
                lab = None
            if lab is None or lab.Id != vs.Id:
                continue
            names = [fd.GetElement(x.ElementId).Name for x in d.References]
            side = u"Слева" if u"Слева" in names else (u"Справа" if u"Справа" in names else None)
            if side is None:
                r["labels"].append([names, u"не определена сторона"]); continue
            d.FamilyLabel = P[u"FT_Выступ_" + side]
            r["labels"].append([names, u"FT_Выступ_" + side])
        fw = P[u"FT_Стекло_Ширина"]
        old = fw.Formula
        fm.SetFormula(fw, old.replace(u"2 * Выступ сбоку", u"FT_Выступ_Слева + FT_Выступ_Справа"))
        r["width_formula"] = [old, fw.Formula]
        t.Commit()
        r["ok"] = r["width_formula"][0] != r["width_formula"][1] and len([x for x in r["labels"] if x[1].startswith(u"FT_")]) == 2
        if SAVE and r["ok"]:
            fd.Save()
    except Exception as ex:
        r["error"] = str(ex)[:300]
    finally:
        fd.Close(False)
    res.append(r)
__output__ = {"status": "completed_unverified" if all(x["ok"] for x in res) else "partial",
              "summary": (u"сохранено" if SAVE else u"ОТЧЁТ без сохранения") + u": панелей ок %d из %d; проект не изменён" % (sum(1 for x in res if x["ok"]), len(res)), "results": res}
