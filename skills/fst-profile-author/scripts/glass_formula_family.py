# -*- coding: utf-8 -*-
# Семейства панелей: размер стекла по альбому. Добавляет FT_Стекло_Добавка (тип, на сторону), FT_Стекло_Поправка_Ширина/Высота
# (экземпляр, по умолчанию 0) и меняет формулы FT_Стекло_Ширина/Высота: rounddown(Ширина + 2*Добавка + Поправка).
# Добавка: цельностеклянные -2.5 (значение как раньше, L-5), «72 мм» 12.5 (М3 стойка стандартная), иначе 10.5 (М2 стойка основная).
# Аргументы: families, dry_run, rfa_out_dir (необязательно: сохранить копию семейства). Затем загрузка в проект и проверка экземпляров.
import json, os, clr, math
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
DRY = bool(args.get("dry_run", True))
F_W = u"if(FT_Система_М1, 0 мм, rounddown((ADSK_Размер_Ширина + 2 * FT_Стекло_Добавка + FT_Стекло_Поправка_Ширина) / 1 мм) * 1 мм)"
F_H = u"if(FT_Система_М1, 0 мм, rounddown((ADSK_Размер_Высота + 2 * FT_Стекло_Добавка + FT_Стекло_Поправка_Высота) / 1 мм) * 1 мм)"


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


def base_for(tn):
    if u"цельностекл" in tn:
        return -2.5
    if u"72 мм" in tn:
        return 12.5
    return 10.5


fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
res = {"families": [], "check": {}}
fdocs = []
for fn in args["families"]:
    fd = doc.EditFamily(fams[fn])
    fm = fd.FamilyManager
    r = {"family": fn[:60], "types": {}}
    t = Transaction(fd, u"Размер стекла по альбому"); t.Start()
    byname = dict((p.Definition.Name, p) for p in fm.Parameters)

    def add(name, inst):
        if name in byname:
            return byname[name]
        p = fm.AddParameter(name, GroupTypeId.Construction, SpecTypeId.Length, inst)
        byname[name] = p
        return p
    pd = add(u"FT_Стекло_Добавка", False)
    pw = add(u"FT_Стекло_Поправка_Ширина", True)
    ph = add(u"FT_Стекло_Поправка_Высота", True)
    for ft in list(fm.Types):
        fm.CurrentType = ft
        b = base_for(ft.Name)
        fm.Set(pd, b / FT)
        fm.Set(pw, 0.0)
        fm.Set(ph, 0.0)
        r["types"][ft.Name[:55]] = b
    fm.SetFormula(byname[u"FT_Стекло_Ширина"], F_W)
    fm.SetFormula(byname[u"FT_Стекло_Высота"], F_H)
    t.Commit()
    od = args["rfa_out_dir"]
    if not os.path.isdir(od):
        os.makedirs(od)
    so = SaveAsOptions(); so.OverwriteExistingFile = True
    rfa = os.path.join(od, fn + u".rfa")
    fd.SaveAs(rfa, so)
    fd.Close(False)
    r["rfa"] = rfa
    fdocs.append(rfa)
    res["families"].append(r)

tg = TransactionGroup(doc, u"Размер стекла по альбому"); tg.Start()
try:
    t = Transaction(doc, u"Семейства панелей: размер стекла по альбому"); t.Start()
    res["loaded"] = [bool(doc.LoadFamily(rfa, LoadOpt(), clr.Reference[Family]())) for rfa in fdocs]
    t.Commit()
    # значения нового параметра типа выставляются в типах проекта (при перезагрузке Revit даёт им одно значение)
    t = Transaction(doc, u"Типы панелей: добавка стекла по альбому"); t.Start()
    nset = 0
    for st in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels):
        if st.FamilyName in args["families"]:
            st.LookupParameter(u"FT_Стекло_Добавка").Set(base_for(st.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()) / FT)
            nset += 1
    t.Commit()
    res["types_set"] = nset
    # проверка: FT == floor(Ширина + 2*Добавка + Поправка) у всех экземпляров этих семейств
    n = bad = 0; samples = []
    for pn in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
        st = doc.GetElement(pn.GetTypeId())
        if st is None or not hasattr(st, "FamilyName") or st.FamilyName not in args["families"]:
            continue
        m1 = st.LookupParameter(u"FT_Система_М1")
        if m1 and m1.AsInteger() == 1:
            continue
        W = pn.LookupParameter(u"ADSK_Размер_Ширина").AsDouble() * FT
        H = pn.LookupParameter(u"ADSK_Размер_Высота").AsDouble() * FT
        b = st.LookupParameter(u"FT_Стекло_Добавка").AsDouble() * FT
        gw = pn.LookupParameter(u"FT_Стекло_Ширина").AsDouble() * FT
        gh = pn.LookupParameter(u"FT_Стекло_Высота").AsDouble() * FT
        ew = math.floor(W + 2 * b + 1e-6); eh = math.floor(H + 2 * b + 1e-6)
        n += 1
        if abs(b - base_for(st.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())) > 0.01:
            bad += 1
        if abs(gw - ew) > 0.01 or abs(gh - eh) > 0.01:
            bad += 1
        if len(samples) < 6:
            samples.append([int(pn.Id.Value), st.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()[:40], round(W, 1), round(H, 1), b, round(gw, 1), round(gh, 1)])
    res["check"] = {"panels": n, "mismatch": bad, "samples [id,тип,W,H,добавка,стекло W,стекло H]": samples}
    res["warnings"] = len(doc.GetWarnings())
finally:
    if DRY:
        tg.RollBack()
    else:
        tg.Assimilate()
res["dry_run"] = DRY
res["status"] = "completed_unverified" if res["check"].get("mismatch") == 0 else "partial"
res["summary"] = u"%sсемейств %d, панелей проверено %d, расхождений %d, предупреждений %s" % (
    u"ПРОБНЫЙ ПРОГОН (откат): " if DRY else u"", len(fdocs), res["check"].get("panels", 0), res["check"].get("mismatch"), res.get("warnings"))
__output__ = res
