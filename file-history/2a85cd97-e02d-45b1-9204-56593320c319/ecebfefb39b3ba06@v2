# -*- coding: utf-8 -*-
# Подготовка (include): PREP(doc, pa) — цельностеклянный стык (замечания 10.11).
# pa: rfa_dir; edge_swaps [{mullion_type, family}]; up_types [{name, family, base_type, params{}}];
#     walls [{wall_type, up_type}] — внутренний вертикальный импост; panels [{type_name, set{param: value_mm|int}}]
# Ключи ответа совместимы с apply_wall_band.py.
import os, clr
from Autodesk.Revit.DB import *


class _CsLO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True
        return True

    def OnSharedFamilyFound(self, a, b, src, c):
        src.Value = FamilySource.Family; c.Value = True
        return True


def _setp(e, n, v):
    p = e.LookupParameter(n)
    if p is None or p.IsReadOnly:
        return False
    if p.StorageType == StorageType.String:
        return p.Set(u"" if v is None else v)
    if p.StorageType == StorageType.Integer:
        return p.Set(int(v))
    if p.StorageType == StorageType.Double:
        return p.Set(float(v) / 304.8) if p.Definition.GetDataType() == SpecTypeId.Length else p.Set(float(v))
    return False


def PREP(doc, pa=None):
    out = {"loaded": 0, "load_fail": [], "swapped": [], "swap_fail": [], "types_created": []}
    t = Transaction(doc, u"FT: стык цс — загрузка"); t.Start()
    for f in sorted(os.listdir(pa["rfa_dir"])):
        if f.lower().endswith(".rfa") and not __import__("re").search(r"\.\d{4}\.rfa$", f.lower()):   # резервные копии Revit не грузить
            if doc.LoadFamily(os.path.join(pa["rfa_dir"], f), _CsLO(), clr.Reference[Family]()):
                out["loaded"] += 1
            else:
                out["load_fail"].append(f)
    t.Commit()
    fams = dict((fa.Name, fa) for fa in FilteredElementCollector(doc).OfClass(Family))
    mts = dict((Element.Name.GetValue(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
    wts = dict((Element.Name.GetValue(w), w) for w in FilteredElementCollector(doc).OfClass(WallType))
    sym = lambda fn: list(fams[fn].GetFamilySymbolIds())[0]
    t = Transaction(doc, u"FT: стык цс — типы"); t.Start()
    try:
        for e in pa.get("edge_swaps", []):
            ok = mts[e["mullion_type"]].get_Parameter(BuiltInParameter.MULLION_PROFILE).Set(sym(e["family"]))
            bad = [k for k, v in (e.get("params") or {}).items() if not _setp(mts[e["mullion_type"]], k, v)]
            (out["swapped"] if ok and not bad else out["swap_fail"]).append([e["mullion_type"], e["family"], bad])
        for u in pa.get("up_types", []):
            m = mts.get(u["name"])
            if m is None:
                m = mts[u["base_type"]].Duplicate(u["name"]); mts[u["name"]] = m; out["types_created"].append([u["name"], int(m.Id.Value)])
            m.get_Parameter(BuiltInParameter.MULLION_PROFILE).Set(sym(u["family"]))
            bad = [k for k, v in u.get("params", {}).items() if not _setp(m, k, v)]
            (out["swap_fail"] if bad else out["swapped"]).append([u["name"], bad or "ok"])
        for w in pa.get("walls", []):
            wt = wts[w["wall_type"]]
            # вертикальная сетка = та же сетка, что у «Граница 1 типа» с вертикальным краевым импостом (по BIP)
            grid = None
            for p in wt.Parameters:
                if p.Definition.Name == u"Граница 1 типа" and p.AsElementId() != ElementId.InvalidElementId:
                    m = doc.GetElement(p.AsElementId())
                    if m is not None and u"стене" in Element.Name.GetValue(m):
                        grid = str(p.Definition.BuiltInParameter)[-1]
            hit = None
            for p in wt.Parameters:
                if p.Definition.Name == u"Внутренний тип" and grid and str(p.Definition.BuiltInParameter).endswith(grid):
                    hit = p
            if hit is not None and hit.Set(mts[w["up_type"]].Id):
                out["swapped"].append([w["wall_type"], u"внутренний вертикальный", w["up_type"], str(hit.Definition.BuiltInParameter)])
            else:
                out["swap_fail"].append([w["wall_type"], u"внутренний тип не найден", grid])
        for mt in pa.get("materials", []):   # [{name, rgb, transparency}]
            ms = [m for m in FilteredElementCollector(doc).OfClass(Material) if m.Name == mt["name"]]
            for m in ms:
                c = mt["rgb"]; m.Color = Color(c[0], c[1], c[2]); m.Transparency = int(mt.get("transparency", 0))
            (out["swapped"] if ms else out["swap_fail"]).append([mt["name"], len(ms)])
        allp = list(FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels))
        for pnl in pa.get("panels", []):
            ss = [s for s in allp if Element.Name.GetValue(s) == pnl["type_name"]]   # имя может повторяться в разных семействах
            if not ss:
                out["swap_fail"].append([pnl["type_name"], u"нет типа"]); continue
            for s in ss:
                bad = [k for k, v in pnl["set"].items() if s.LookupParameter(k) is not None and not _setp(s, k, v)]
                miss = [k for k in pnl["set"] if s.LookupParameter(k) is None]
                (out["swap_fail"] if bad else out["swapped"]).append([pnl["type_name"], s.FamilyName, bad or "ok", miss])
        t.Commit()
    except Exception:
        t.RollBack(); raise
    return out
