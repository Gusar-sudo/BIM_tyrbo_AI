# -*- coding: utf-8 -*-
# Семейство панели ГКЛ: общие параметры для площади и листов ГКЛ (решение 14.11.2026).
# Добавляет из ФОП (экземпляр): FT_ГКЛ_Площадь = Ш×В куска × 2 слоя, FT_ГКЛ_Кусков = 2,
# FT_ГКЛ_Больше_листа = кусок шире sheet_w или выше sheet_h; FT_Утеплитель_Площадь — семейный -> общий (формула сохраняется).
# Кусок = FT_Стекло_Ширина/Высота (ячейка + заход в паз, уже в семействе).
# Аргументы: family, spf_path, rfa_out_dir, sheet_w_mm (1100), sheet_h_mm (3000), dry_run,
#   source_doc (необязательно: заголовок другого открытого документа, из которого брать семейство; сам он не меняется).
# Документ, в который грузится семейство, — активный. Семейство правится в памяти и сохраняется копией в rfa_out_dir.
import json, os, clr
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
app = doc.Application
DRY = bool(a.get("dry_run", True)); FT = 304.8
SW = float(a.get("sheet_w_mm", 1100)); SH = float(a.get("sheet_h_mm", 3000))
FORM = {u"FT_ГКЛ_Площадь": u"FT_Стекло_Ширина * FT_Стекло_Высота * 2",
        u"FT_ГКЛ_Кусков": u"2",
        u"FT_ГКЛ_Больше_листа": u"or(FT_Стекло_Ширина > %g мм, FT_Стекло_Высота > %g мм)" % (SW, SH)}


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


src = doc
if a.get("source_doc"):
    src = [d for d in app.Documents if not d.IsFamilyDocument and d.Title == a["source_doc"]][0]
old_spf = app.SharedParametersFilename
res = {"dry_run": DRY, "source_doc": src.Title, "target_doc": doc.Title}
try:
    app.SharedParametersFilename = a["spf_path"]
    defs = {}
    for g in app.OpenSharedParameterFile().Groups:
        for d in g.Definitions:
            defs[d.Name] = d
    fam = [f for f in FilteredElementCollector(src).OfClass(Family) if f.Name == a["family"]][0]
    fd = src.EditFamily(fam); fm = fd.FamilyManager
    t = Transaction(fd, u"Параметры ГКЛ"); t.Start()
    try:
        by = dict((p.Definition.Name, p) for p in fm.Parameters)
        done = []
        for n in (u"FT_ГКЛ_Площадь", u"FT_ГКЛ_Кусков", u"FT_ГКЛ_Больше_листа"):
            if n not in by:
                grp = GroupTypeId.Geometry if n == u"FT_ГКЛ_Площадь" else GroupTypeId.Data
                by[n] = fm.AddParameter(defs[n], grp, True); done.append(u"добавлен " + n)
        u = by.get(u"FT_Утеплитель_Площадь")
        if u is not None and not u.IsShared:
            # Revit не заменяет параметр общим с тем же именем и с формулой: снять формулу, переименовать, заменить, вернуть формулу
            f_old = u.Formula
            if f_old:
                fm.SetFormula(u, None)
            fm.RenameParameter(u, u"FT_Утеплитель_Площадь_tmp")
            np = fm.ReplaceParameter(u, defs[u"FT_Утеплитель_Площадь"], GroupTypeId.Geometry, True)
            by[u"FT_Утеплитель_Площадь"] = np
            if f_old:
                fm.SetFormula(np, f_old)
            done.append(u"утеплитель -> общий")
        for n, f in FORM.items():
            fm.SetFormula(by[n], f)
        t.Commit()
    except Exception:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        fd.Close(False)
        raise
    res["family_changes"] = done
    res["formulas"] = dict((n, by[n].Formula) for n in list(FORM) + [u"FT_Утеплитель_Площадь"])
    res["shared"] = dict((n, by[n].IsShared) for n in list(FORM) + [u"FT_Утеплитель_Площадь"])
    od = a["rfa_out_dir"]
    if not os.path.isdir(od):
        os.makedirs(od)
    so = SaveAsOptions(); so.OverwriteExistingFile = True
    rfa = os.path.join(od, a["family"] + u".rfa")
    fd.SaveAs(rfa, so); fd.Close(False)
    res["rfa"] = rfa
    tg = TransactionGroup(doc, u"Параметры ГКЛ в проекте"); tg.Start()
    try:
        t = Transaction(doc, u"Загрузка семейства ГКЛ"); t.Start()
        res["loaded"] = bool(doc.LoadFamily(rfa, LoadOpt(), clr.Reference[Family]()))
        t.Commit()
        chk = []
        for p in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
            st = doc.GetElement(p.GetTypeId())
            if getattr(st, "FamilyName", "") != a["family"]:
                continue
            gw = p.LookupParameter(u"FT_Стекло_Ширина").AsDouble() * FT; gh = p.LookupParameter(u"FT_Стекло_Высота").AsDouble() * FT
            ar = p.LookupParameter(u"FT_ГКЛ_Площадь").AsDouble() * 0.09290304
            big = p.LookupParameter(u"FT_ГКЛ_Больше_листа").AsInteger()
            ok = abs(ar - gw * gh * 2 / 1e6) < 0.001 and big == int(gw > SW or gh > SH)
            chk.append({"id": p.Id.Value, "кусок": [round(gw), round(gh)], "м2": round(ar, 3), "больше": big, "ok": ok})
        res["instances"] = chk
        sym = [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol) if s.FamilyName == a["family"]]
        res["types_in_target"] = len(sym)
        res["warnings"] = len(doc.GetWarnings())
    finally:
        if DRY:
            tg.RollBack()
        else:
            tg.Assimilate()
finally:
    app.SharedParametersFilename = old_spf
bad = [c for c in res.get("instances", []) if not c["ok"]]
res["status"] = "completed_unverified" if not bad else "partial"
res["summary"] = u"%sпараметры ГКЛ: %s; загружено=%s; экземпляров проверено %d, ошибок %d" % (
    u"ПРОБА (откат в проекте): " if DRY else u"", u", ".join(res.get("family_changes", [])) or u"уже были", res.get("loaded"),
    len(res.get("instances", [])), len(bad))
__output__ = res
