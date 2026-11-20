# -*- coding: utf-8 -*-
# Только чтение: по стойкам (М2 FSC139/FSC21, М3 FSC111/FSC01К/FSC01/FSC09) собрать аргументы для
#  build_rail_profiles.py (3 профиля на стойку) и prep_cs_joint.py up_types (11 типов на стойку) из существующих типов:
#  «<М> <FSC> не доходит до стены с двух/однослойным остеклением левый/правый» (закрытые профили) и
#  «<М> <FSC> примыкание к стене с двухслойным остеклением правый/левый» (края с лентой).
# Аргументы: stands [["М2","FSC21"], ...], rfa_dir, build_out, prep_out (пути JSON для записи).
import json, io
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
mts = dict((Element.Name.GetValue(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))


def prof(tn):
    m = mts.get(tn)
    if m is None:
        return None
    p = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
    return p.FamilyName if p else None


def sp(tn, name):
    p = mts[tn].LookupParameter(name)
    return p.AsString() if p and p.StorageType == StorageType.String else None


LAY = {u"двух": u"двухслойным", u"одно": u"однослойным"}
build, up, miss = [], [], []
for sysn, fsc in args["stands"]:
    pre = u"%s %s " % (sysn, fsc)
    n = lambda s: pre + s
    cl = {(ly, side): n(u"не доходит до стены с %s остеклением %s" % (LAY[ly], side)) for ly in LAY for side in (u"левый", u"правый")}
    we = {side: n(u"примыкание к стене с двухслойным остеклением %s" % side) for side in (u"правый", u"левый")}
    need = list(cl.values()) + list(we.values())
    bad = [t for t in need if t not in mts]
    if bad:
        miss.append(bad); continue
    short = fsc
    sysd = sysn.replace(u"М", u"М")
    rail = sp(cl[(u"двух", u"левый")], u"FT_Рейка_Артикул") or (u"FS.C-158" if sysn == u"М2" else u"FS.C-26")
    adsk0 = sp(cl[(u"двух", u"левый")], u"ADSK_Наименование") or u""
    model = adsk0.split(u" не доходит")[0] if u" не доходит" in adsk0 else (u"Сборка MODEL %s" % sysn[-1])
    fam = lambda k: u"BIMLIB_Профиль_%s_%s_%s_ФристайлТехнолоджи" % (sysn, fsc, k)
    build += [
        {"a": prof(cl[(u"двух", u"правый")]), "b": prof(cl[(u"двух", u"левый")]), "keep": "neg", "save_as": fam(u"НадПотолкомДвеРейки")},
        {"a": prof(we[u"правый"]), "b": prof(cl[(u"двух", u"левый")]), "keep": "neg", "save_as": fam(u"НадПотолкомСтенаПравый")},
        {"a": prof(we[u"левый"]), "b": prof(cl[(u"двух", u"правый")]), "keep": "pos", "save_as": fam(u"НадПотолкомСтенаЛевый")}]
    up += [
        {"name": n(u"над подвесным потолком"), "family": fam(u"НадПотолкомДвеРейки"), "base_type": cl[(u"двух", u"правый")],
         "params": {"FT_Витраж_Артикул": u"", "FT_Витраж_Расход": 0, "FT_Рейка_Артикул": rail, "FT_Рейка_Расход": 2, "ADSK_Наименование": model + u" над подвесным потолком (накрывающие рейки с двух сторон)"}}]
    for side in (u"правый", u"левый"):
        up.append({"name": n(u"над подвесным потолком примыкание к стене %s" % side), "family": fam(u"НадПотолкомСтена" + (u"Правый" if side == u"правый" else u"Левый")),
                   "base_type": we[side], "params": {"FT_Витраж_Артикул": u"", "FT_Витраж_Расход": 0, "FT_Рейка_Артикул": rail, "FT_Рейка_Расход": 1,
                                                    "ADSK_Наименование": model + u" над подвесным потолком, примыкание к стене"}})
    for ly in LAY:
        L_ = LAY[ly]
        up += [
            {"name": n(u"ригель у подвесного потолка с %s остеклением" % L_), "family": prof(cl[(ly, u"левый")]), "base_type": cl[(ly, u"левый")],
             "params": {"ADSK_Наименование": model + u" ригель у подвесного потолка с %s остеклением (рейка сверху)" % L_}},
            {"name": n(u"у проёма с %s остеклением левый" % L_), "family": prof(cl[(ly, u"левый")]), "base_type": cl[(ly, u"левый")],
             "params": {"ADSK_Наименование": model + u" у проёма с %s остеклением" % L_}},
            {"name": n(u"у проёма с %s остеклением правый" % L_), "family": prof(cl[(ly, u"правый")]), "base_type": cl[(ly, u"правый")],
             "params": {"ADSK_Наименование": model + u" у проёма с %s остеклением" % L_}},
            {"name": n(u"над проёмом с %s остеклением" % L_), "family": prof(cl[(ly, u"правый")]), "base_type": cl[(ly, u"правый")],
             "params": {"ADSK_Наименование": model + u" над проёмом с %s остеклением (рейка снизу)" % L_}}]
io.open(args["build_out"], "w", encoding="utf-8").write(json.dumps({"out_dir": args["rfa_dir"], "items": build}, ensure_ascii=False, indent=1))
io.open(args["prep_out"], "w", encoding="utf-8").write(json.dumps({"rfa_dir": args["rfa_dir"], "up_types": up}, ensure_ascii=False, indent=1))
__output__ = {"status": "completed_unverified", "summary": u"профилей %d, типов %d, пропусков %d" % (len(build), len(up), len(miss)), "result": {"missing": miss, "build": build}}
