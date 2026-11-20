# -*- coding: utf-8 -*-
# Однослойная панель: боковой уплотнитель отдельно (как в двухслойной) + цс-типы однослойной цельностеклянной.
# 1) параметры типа FT_Уплотнитель_Бок_Показать (да/нет, по умолчанию да) и FT_Уплотнитель_U5/6/8/10_Бок = and(U*_Показать, Бок_Показать);
#    видимость вертикальных (боковых) полос уплотнителя связывается с U*_Бок;
#    длина уплотнителя: 2*(Ширина + if(Бок, Высота, 0)) * Линий — как в двухслойной.
# 2) типы цс (cs_types: {имя: толщина стекла}): ADSK_Размер_Толщина = thickness_mm, выступы 0, добавка -2.5, Бок выкл.
# Сохраняет КОПИЮ .rfa в out_dir; проект не меняется.
import json, io, os
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
fam = [f for f in FilteredElementCollector(doc).OfClass(Family) if f.Name == args["family"]][0]
fd = doc.EditFamily(fam)
res = {}
try:
    fm = fd.FamilyManager
    t = Transaction(fd, u"боковой уплотнитель"); t.Start()
    try:
        P = dict((p.Definition.Name, p) for p in fm.Parameters)

        def add_bool(n):
            if n in P:
                return P[n]
            p = fm.AddParameter(n, GroupTypeId.Constraints, SpecTypeId.Boolean.YesNo, False); P[n] = p; return p
        pb = add_bool(u"FT_Уплотнитель_Бок_Показать")
        for tp in fm.Types:
            fm.CurrentType = tp; fm.Set(pb, 1)
        for u in (u"U5", u"U6", u"U8", u"U10"):
            q = add_bool(u"FT_Уплотнитель_%s_Бок" % u)
            fm.SetFormula(q, u"and(FT_Уплотнитель_%s_Показать, FT_Уплотнитель_Бок_Показать)" % u)
        n_assoc = 0
        for e in FilteredElementCollector(fd).OfClass(Sweep):
            pp = e.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM)
            fp = fm.GetAssociatedFamilyParameter(pp) if pp else None
            bb = e.get_BoundingBox(None)
            if fp is None or bb is None or (bb.Max.Z - bb.Min.Z) * FT < 100:
                continue
            nm = fp.Definition.Name
            if nm.endswith(u"_Показать") and nm.startswith(u"FT_Уплотнитель_U"):
                fm.AssociateElementParameterToFamilyParameter(pp, P[nm.replace(u"_Показать", u"_Бок")]); n_assoc += 1
        fm.SetFormula(P[u"FT_Стекло_Уплотнитель_Длина"], u"if(FT_Система_М1, 0 мм, 2 * (ADSK_Размер_Ширина + if(FT_Уплотнитель_Бок_Показать, ADSK_Размер_Высота, 0 мм)) * FT_Стекло_Уплотнитель_Линий)")
        res["side_sweeps_reassociated"] = n_assoc
        types = dict((x.Name, x) for x in fm.Types)
        done = []
        for tn, gl in args["cs_types"].items():
            src = args.get("rename", {}).get(tn)
            if tn not in types and src and src in types:
                fm.CurrentType = types[src]; fm.RenameCurrentType(tn); types = dict((x.Name, x) for x in fm.Types)
            if tn not in types:
                fm.CurrentType = types[args["base_type"]]; fm.NewType(tn); types = dict((x.Name, x) for x in fm.Types)
            fm.CurrentType = types[tn]
            fm.Set(P[u"ADSK_Размер_Толщина"], float(args.get("thickness_mm", 61.2)) / FT)
            for n in (u"Выступ сбоку", u"Выступ сверху", u"Выступ снизу"):
                fm.Set(P[n], 0.0)
            fm.Set(P[u"FT_Стекло_Добавка"], -2.5 / FT)
            fm.Set(P[u"Толщина стекла"], float(gl) / FT)
            fm.Set(pb, 0)
            done.append(tn)
        for tn in args.get("delete_types", []):
            if tn in types:
                fm.CurrentType = types[tn]; fm.DeleteCurrentType(); types = dict((x.Name, x) for x in fm.Types)
        res["cs_types"] = done; res["types_after"] = sorted(types)
        t.Commit()
    except Exception:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        raise
    if not os.path.isdir(args["out_dir"]):
        os.makedirs(args["out_dir"])
    o = SaveAsOptions(); o.OverwriteExistingFile = True
    res["rfa"] = os.path.join(args["out_dir"], args["family"] + u".rfa"); fd.SaveAs(res["rfa"], o)
finally:
    fd.Close(False)
__output__ = {"status": "completed_unverified", "summary": u"копия панели: боковых полос %s, цс-типов %d; проект не менялся" % (res.get("side_sweeps_reassociated"), len(res.get("cs_types", []))), "r": res}
