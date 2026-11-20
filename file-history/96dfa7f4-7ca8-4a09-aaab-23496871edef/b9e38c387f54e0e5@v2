# -*- coding: utf-8 -*-
# Перенос в рабочую копию библиотеки: загрузить все .rfa из src_dir (переопределить семейства, значения параметров
# типов НЕ перезаписывать), проверить: число импостов/панелей и предупреждения до/после, уплотнитель во всех
# стеклянных панелях (отступ от кромки и глубина от лица стекла по DWG, на всю длину кромки), М1 — без уплотнителя.
# commit=false -> откат всей группы (пробный прогон). Аргументы: src_dir, commit
import json, os, glob, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
commit = bool(args.get("commit", False))
EXPECT = {5: [4.08, 5.17, 14.13], 6: [5.06, 6.0, 14.61], 8: [5.32, 8.01, 14.66], 10: [3.31, 8.42, 14.91]}
opt = Options(); opt.DetailLevel = ViewDetailLevel.Fine


class LoadOpt(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True


def counts():
    mul = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType().GetElementCount()
    pan = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType().GetElementCount()
    return {"mullions": mul, "panels": pan, "warnings": len(doc.GetWarnings())}


def solids(el):
    out = []
    def walk(ge, tr):
        for g in ge:
            if isinstance(g, Solid) and g.Volume > 1e-12:
                out.append(SolidUtils.CreateTransformed(g, tr) if tr else g)
            elif isinstance(g, GeometryInstance):
                walk(g.GetSymbolGeometry(), tr.Multiply(g.Transform) if tr else g.Transform)
    ge = el.get_Geometry(opt)
    if ge:
        walk(ge, None)
    return out


def mname(s):
    for f in s.Faces:
        m = doc.GetElement(f.MaterialElementId)
        if m is not None:
            return m.Name
    return ""


def ext(sols, o, ax):
    lo, hi = 1e9, -1e9
    for s in sols:
        for e in s.Edges:
            for p in e.Tessellate():
                d = (p - o).DotProduct(ax) * FT
                lo = min(lo, d); hi = max(hi, d)
    return lo, hi


def seal_check():
    ok, bad, m1, nopanel = 0, [], 0, 0
    for w in FilteredElementCollector(doc).OfClass(Wall):
        if w.CurtainGrid is None:
            continue
        c = w.Location.Curve
        d = c.ComputeDerivatives(0.5, True).BasisX.Normalize(); n = XYZ.BasisZ.CrossProduct(d); o = c.GetEndPoint(0)
        for pid in w.CurtainGrid.GetPanelIds():
            p = doc.GetElement(pid)
            if not isinstance(p, Panel):
                continue
            ss = solids(p)
            gl = [s for s in ss if u"тек" in mname(s).lower()]
            se = [s for s in ss if mname(s) == u"FT_Уплотнитель_EPDM"]
            if not gl:
                nopanel += 1; continue
            if u"(М1)" in p.Name:
                if se:
                    bad.append({"panel": int(pid.Value), "type": p.Name, "why": u"в М1 есть уплотнитель"})
                else:
                    m1 += 1
                continue
            for g in gl:
                gx = ext([g], o, d); gy = ext([g], o, n); gz = ext([g], o, XYZ.BasisZ)
                t = int(round(gy[1] - gy[0]))
                face = gy[0] if abs(gy[0]) > abs(gy[1]) else gy[1]
                sg = 1 if face < 0 else -1
                mine = [s for s in se if abs((ext([s], o, n)[0] + ext([s], o, n)[1]) / 2 - (gy[0] + gy[1]) / 2) < 25]
                e = EXPECT.get(t)
                good = e is not None and len(mine) == 4
                for s in mine:
                    sx = ext([s], o, d); sy = ext([s], o, n); sz = ext([s], o, XYZ.BasisZ)
                    dep = sorted([(sy[0] - face) * sg, (sy[1] - face) * sg])
                    if sx[1] - sx[0] < 50:
                        ins = min(sx[0] - gx[0], gx[1] - sx[1]); span = [sz[0] - gz[0], gz[1] - sz[1]]
                    else:
                        ins = min(sz[0] - gz[0], gz[1] - sz[1]); span = [sx[0] - gx[0], gx[1] - sx[1]]
                    if e is None or abs(ins - e[0]) > 0.05 or abs(dep[0] - e[1]) > 0.05 or abs(dep[1] - e[2]) > 0.05 or max(abs(v) for v in span) > 0.05:
                        good = False
                if good:
                    ok += 1
                else:
                    bad.append({"wall": int(w.Id.Value), "panel": int(pid.Value), "type": p.Name, "t": t, "seals": len(mine)})
    return {"glass_ok": ok, "m1_ok": m1, "bad": bad[:15], "bad_count": len(bad)}


res = {"before": counts()}
tg = TransactionGroup(doc, u"FT: перенос исправлений из теста (уплотнитель, столбы, профили)"); tg.Start()
try:
    t = Transaction(doc, u"FT: загрузка семейств"); t.Start()
    loaded = []
    for rfa in sorted(glob.glob(os.path.join(args["src_dir"], "*.rfa"))):
        f = clr.Reference[Family]()
        loaded.append([os.path.basename(rfa)[:-4], bool(doc.LoadFamily(rfa, LoadOpt(), f))])
    t.Commit()
    res["loaded_ok"] = sum(1 for x in loaded if x[1]); res["loaded_total"] = len(loaded)
    res["not_loaded"] = [x[0] for x in loaded if not x[1]]
    res["after"] = counts()
    res["seals"] = seal_check()
finally:
    if commit:
        tg.Assimilate()
    else:
        tg.RollBack()
res["committed"] = commit
__output__ = {"status": "completed_unverified", "summary": u"%s: загружено %d/%d" % (u"применено" if commit else u"пробный прогон, откат", res.get("loaded_ok", 0), res.get("loaded_total", 0)), "result": res}
