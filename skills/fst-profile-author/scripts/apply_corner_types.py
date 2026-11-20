# -*- coding: utf-8 -*-
# Применение угловых профилей с держателем в активном проекте:
#   1) загрузка .rfa профилей (перезапись существующих семейств);
#   2) типы импостов: существующие — новый профиль; недостающие — копия базового типа 90°;
#   3) ADSK_Наименование по углу (если задано в types[].adsk_name).
# dry_run=true: ничего не пишет, отчитывается, что изменится (есть ли тип, текущий профиль, наименование, артикулы держателя).
# Аргументы: rfa_paths, types [{name, base, profile_family, adsk_name?}], dry_run
import json, io, os, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
DRY = bool(args.get("dry_run", True))


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = False; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = False; return True


def mts():
    return dict((m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), m) for m in FilteredElementCollector(doc).OfClass(MullionType))


def pval(el, n):
    p = el.LookupParameter(n)
    return p.AsString() if p is not None and p.StorageType == StorageType.String else None


def holder_info(m):
    out = []
    for p in m.Parameters:
        try:
            if p.StorageType == StorageType.String and p.AsString() and (u"FS.C-06" in p.AsString() or u"FS.C-19" in p.AsString() or u"FC.C-06" in p.AsString()):
                out.append([p.Definition.Name, p.AsString()])
        except Exception:
            pass
    return out


res = {"dry_run": DRY, "doc": doc.Title, "types": [], "loaded": []}
M = mts()
fams_before = set(f.Name for f in FilteredElementCollector(doc).OfClass(Family))
for t in args["types"]:
    m = M.get(t["name"]); b = M.get(t["base"])
    cur = None
    if m is not None:
        sid = m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId()
        s = doc.GetElement(sid); cur = s.Family.Name if s is not None else None
    res["types"].append({"name": t["name"], "exists": m is not None, "base_exists": b is not None,
                         "profile_now": cur, "profile_new": t["profile_family"], "family_loaded_now": t["profile_family"] in fams_before,
                         "adsk_now": pval(m, u"ADSK_Наименование") if m else None, "adsk_base": pval(b, u"ADSK_Наименование") if b else None,
                         "adsk_new": t.get("adsk_name"), "holder_params": holder_info(m if m is not None else b) if (m or b) else []})
if not DRY:
    tr = Transaction(doc, u"FT: угловые столбы с держателем"); tr.Start()
    try:
        for rfa in args["rfa_paths"]:
            res["loaded"].append([os.path.basename(rfa)[:-4], bool(doc.LoadFamily(rfa, LoadOpt(), clr.Reference[Family]()))])
        fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
        # пробные семейства пилота: удалить, только если ни один тип импоста на них не ссылается
        used = set()
        for mt in FilteredElementCollector(doc).OfClass(MullionType):
            s = doc.GetElement(mt.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
            if s is not None:
                used.add(s.Family.Name)
        res["deleted_families"] = []
        for fn in args.get("delete_unused_families", []):
            if fn in fams and fn not in used:
                doc.Delete(fams[fn].Id); res["deleted_families"].append(fn)
        M = mts(); done = []
        for t in args["types"]:
            m = M.get(t["name"])
            if m is None:
                m = M[t["base"]].Duplicate(t["name"]); M[t["name"]] = m
            sym = doc.GetElement(list(fams[t["profile_family"]].GetFamilySymbolIds())[0])
            m.get_Parameter(BuiltInParameter.MULLION_PROFILE).Set(sym.Id)
            if t.get("adsk_name"):
                p = m.LookupParameter(u"ADSK_Наименование")
                if p is not None and not p.IsReadOnly:
                    p.Set(t["adsk_name"])
            done.append(t["name"])
        tr.Commit()
    except Exception:
        if tr.HasStarted() and not tr.HasEnded():
            tr.RollBack()
        raise
    # перечитать
    M = mts(); chk = []
    for t in args["types"]:
        m = M.get(t["name"])
        s = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId()) if m else None
        chk.append([t["name"], m is not None, s.Family.Name == t["profile_family"] if s else False, pval(m, u"ADSK_Наименование") if m else None])
    res["verify"] = chk
    res["ok_all"] = all(c[1] and c[2] for c in chk)
__output__ = {"status": "completed_unverified", "summary": (u"пробный прогон: типов %d (нет: %d)" % (len(res["types"]), sum(1 for x in res["types"] if not x["exists"]))) if DRY else (u"применено, проверка типов: %s" % res.get("ok_all")), "result": res}
