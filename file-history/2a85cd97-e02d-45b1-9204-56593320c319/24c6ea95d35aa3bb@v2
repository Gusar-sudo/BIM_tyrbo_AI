# -*- coding: utf-8 -*-
# Замена межстекольного УП-008 на FS.C-156 (альбом М1) в цельностеклянных М2/М3.
# 1) загрузка семейств профиля из rfa_dir; 2) типы импоста: профиль, «Смещение», параметры, новое имя;
# 3) панели цс (panel_family, FT_Стекло_Добавка == -2.5, имя без «М1») -> добавка 0;
# 4) замер: у каждой стены с новым импостом — зазор между торцами стёкол по слоям и стекло спец. vs геометрия;
# 5) archive: семейства old_families сохраняются в archive_dir и удаляются из проекта, если ими ничто не пользуется
#    (типы импоста без экземпляров, ссылающиеся на них, удаляются вместе с ними).
# dry_run=true: всё в группе транзакций с откатом, архив не пишется.
import json, io, os, re, clr
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    a2 = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read()); a2.update(dict((k, v) for k, v in args.items() if k != "args_file")); args = a2
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
DRY = bool(args.get("dry_run", True))
res = {"dry_run": DRY, "loaded": [], "types": [], "panels": [], "check": [], "archive": [], "problems": []}


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


def setp(e, n, v):
    p = e.LookupParameter(n)
    if p is None or p.IsReadOnly:
        return False
    if p.StorageType == StorageType.String:
        return p.Set(u"" if v is None else v)
    if p.StorageType == StorageType.Integer:
        return p.Set(int(v))
    if p.StorageType == StorageType.Double:
        dt = p.Definition.GetDataType()
        return p.Set(float(v) / FT) if dt == SpecTypeId.Length else p.Set(float(v))
    return False


opt = Options(); opt.DetailLevel = ViewDetailLevel.Fine


def solids(e):
    out = []
    def walk(g):
        for o in g:
            if isinstance(o, Solid) and o.Volume > 1e-9:
                out.append(o)
            elif isinstance(o, GeometryInstance):
                walk(o.GetInstanceGeometry())
    ge = e.get_Geometry(opt)
    if ge:
        walk(ge)
    return out


def glass_of(pn):
    r = []
    for s in solids(pn):
        if s.Faces.Size == 0:
            continue
        m = doc.GetElement(s.Faces.get_Item(0).MaterialElementId)
        if m is not None and u"Стекло" in m.Name:
            r.append(s)
    return r


def check():
    new_names = set(t["new_name"] for t in args["types"])
    for w in FilteredElementCollector(doc).OfClass(Wall):
        cg = w.CurtainGrid
        if cg is None:
            continue
        ms = [doc.GetElement(i) for i in cg.GetMullionIds()]
        hit = [m for m in ms if m.Name in new_names]
        if not hit:
            continue
        lc = w.Location.Curve; o = lc.GetEndPoint(0); dv = (lc.GetEndPoint(1) - o).Normalize(); nv = XYZ(-dv.Y, dv.X, 0)
        loc = lambda p: ((p - o).DotProduct(dv) * FT, (p - o).DotProduct(nv) * FT)
        m = hit[0]; bb = m.get_BoundingBox(None)
        mc = (loc(bb.Min)[0] + loc(bb.Max)[0]) / 2
        zc = (bb.Min.Z + bb.Max.Z) / 2
        pieces = []
        spec = []
        for pid in cg.GetPanelIds():
            pn = doc.GetElement(pid)
            pb = pn.get_BoundingBox(None)
            if pb is None or not (pb.Min.Z < zc < pb.Max.Z):
                continue
            for s in glass_of(pn):
                pts = [loc(q) for ed in s.Edges for q in ed.Tessellate()]
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                if min(xs) - 5 < mc < max(xs) + 5 or abs(min(xs) - mc) < 10 or abs(max(xs) - mc) < 10:
                    pieces.append((round((min(ys) + max(ys)) / 2, 1), min(xs), max(xs), pn))
        gaps = {}
        for yc in sorted(set(p[0] for p in pieces)):
            L = [p for p in pieces if p[0] == yc and p[2] <= mc + 0.5]
            R = [p for p in pieces if p[0] == yc and p[1] >= mc - 0.5]
            if L and R:
                l = max(L, key=lambda p: p[2]); r = min(R, key=lambda p: p[1])
                gaps[str(yc)] = round(r[1] - l[2], 2)
                for pc in (l, r):
                    pn = pc[3]; q = pn.LookupParameter(u"FT_Стекло_Ширина")
                    geo = None
                    gl = [g for g in pieces if g[3].Id == pn.Id and g[0] == yc]
                    if gl:
                        geo = round(gl[0][2] - gl[0][1], 1)
                    spec.append([q.AsDouble() * FT if q else None, geo])
        bad_spec = [s_ for s_ in spec if s_[0] is None or s_[1] is None or not (0 <= s_[1] - s_[0] < 1.0)]
        row = {"wall_type": w.Name, "wall_id": int(w.Id.Value), "mullion": m.Name, "gaps_mm": gaps,
               "spec_vs_geo": [[round(a_, 1) if a_ else a_, b_] for a_, b_ in spec[:4]], "spec_ok": not bad_spec}
        if not gaps or any(abs(v - 4.0) > 0.2 for v in gaps.values()) or bad_spec:
            res["problems"].append(row)
        res["check"].append(row)


_T = Transaction
OPEN = []
def Transaction(d, n):
    x = _T(d, n); OPEN.append(x); return x
tg = TransactionGroup(doc, u"FT: FS.C-156 вместо УП-008"); tg.Start()
try:
    t = Transaction(doc, u"FT: FS.C-156 — загрузка"); t.Start()
    for f in sorted(os.listdir(args["rfa_dir"])):
        if f.lower().endswith(".rfa") and not re.search(r"\.\d{4}\.rfa$", f.lower()):
            ok = doc.LoadFamily(os.path.join(args["rfa_dir"], f), LO(), clr.Reference[Family]())
            res["loaded"].append([f, bool(ok)])
    t.Commit()
    fams = dict((fa.Name, fa) for fa in FilteredElementCollector(doc).OfClass(Family))
    mts = dict((Element.Name.GetValue(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
    t = Transaction(doc, u"FT: FS.C-156 — типы и панели"); t.Start()
    for ty in args["types"]:
        m = mts.get(ty["old_name"]) or mts.get(ty["new_name"])
        if m is None:
            res["problems"].append([u"нет типа", ty["old_name"]]); continue
        m.get_Parameter(BuiltInParameter.MULLION_PROFILE).Set(list(fams[ty["profile"]].GetFamilySymbolIds())[0])
        bad = [k for k, v in ty.get("params", {}).items() if not setp(m, k, v)]
        if not setp(m, u"Смещение", ty["offset_mm"]):
            bad.append(u"Смещение")
        if Element.Name.GetValue(m) != ty["new_name"]:
            m.Name = ty["new_name"]
        left = [p.Definition.Name for p in m.Parameters if p.StorageType == StorageType.String and p.AsString() and u"УП-008" in p.AsString()]
        n_inst = sum(1 for x in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType() if x.GetTypeId() == m.Id)
        res["types"].append({"type": ty["new_name"], "id": int(m.Id.Value), "instances": n_inst, "bad_params": bad, "still_mention_up008": left})
    for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels):
        if s.Family.Name not in args["panel_families"] or u"М1" in s.Name:
            continue
        q = s.LookupParameter(u"FT_Стекло_Добавка")
        if q is not None and abs(q.AsDouble() * FT + 2.5) < 0.01:
            q.Set(0.0); res["panels"].append([s.Family.Name, s.Name])
    t.Commit()
    check()
    # архив старых семейств
    if args.get("archive_dir"):
        if not DRY and not os.path.isdir(args["archive_dir"]):
            os.makedirs(args["archive_dir"])
        mts = list(FilteredElementCollector(doc).OfClass(MullionType))
        todo = []
        for fn in args.get("old_families", []):
            fa = dict((x.Name, x) for x in FilteredElementCollector(doc).OfClass(Family)).get(fn)
            if fa is None:
                res["archive"].append([fn, u"нет в проекте"]); continue
            syms = set(i.Value for i in fa.GetFamilySymbolIds())
            users = [m for m in mts if m.IsValidObject and m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId().Value in syms]
            used = [Element.Name.GetValue(m) for m in users if any(x.GetTypeId() == m.Id for x in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType())]
            if used:
                res["archive"].append([fn, u"используется, оставлено", used]); continue
            path = os.path.join(args["archive_dir"], fn + u".rfa")
            if not DRY:
                fd = doc.EditFamily(fa)
                try:
                    so = SaveAsOptions(); so.OverwriteExistingFile = True; fd.SaveAs(path, so)
                finally:
                    fd.Close(False)
            if not DRY and not os.path.isfile(path):
                raise Exception(u"архивная копия не записана: " + path)
            todo.append((fn, path, [m.Id for m in users] + [fa.Id], [Element.Name.GetValue(m) for m in users]))
        t = Transaction(doc, u"FT: УП-008 — в архив"); t.Start()
        for fn, path, ids, names in todo:
            doc.Delete(List[ElementId](ids))
            res["archive"].append([fn, u"в архив и удалено" if not DRY else u"будет в архив и удалено", path, names])
        t.Commit()
    if DRY:
        tg.RollBack()
    else:
        tg.Assimilate()
except Exception:
    import traceback
    res["error"] = traceback.format_exc()[-600:]
    for x in OPEN:
        if x.HasStarted() and not x.HasEnded():
            x.RollBack()
    if tg.HasStarted() and not tg.HasEnded():
        tg.RollBack()
st = "failed" if res.get("error") else ("partial" if res["problems"] else "completed_unverified")
__output__ = {"status": st, "summary": (u"ПРОБА (откат): " if DRY else u"ПРИМЕНЕНО: ") + u"типов %d, панелей %d, стен проверено %d, проблем %d, в архив %d" % (len(res["types"]), len(res["panels"]), len(res["check"]), len(res["problems"]), len(res["archive"])), "r": res}
