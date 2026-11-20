# -*- coding: utf-8 -*-
# Замер нагрузки от 3D-тела профиля С ОТКАТОМ: строит n_walls стен-витражей того же типа, что у стены с импостом
# mullion_type_like (длина length_mm), затем перезагружает семейство профиля «новое» (new_rfa) и «старое» (копия из
# проекта) и меряет время перезагрузки (= перестроение всех импостов) и число граней/рёбер у одного импоста.
# Аргументы: mullion_type_like, new_rfa, family_name, n_walls=10, length_mm=30000, height_mm=3000, tmp_dir, repeat=2
import json, os, time
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
like = args["mullion_type_like"].lower().split()
res = {"errors": []}


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


mul = wall = None
for w in FilteredElementCollector(doc).OfClass(Wall):
    if w.CurtainGrid is None: continue
    for mid in w.CurtainGrid.GetMullionIds():
        m = doc.GetElement(mid)
        if all(k in (m.Symbol.FamilyName + u" " + m.Name).lower() for k in like) and abs(m.LocationCurve.Direction.Z) > 0.9:
            mul, wall = m, w; break
    if mul: break
mtype = mul.Symbol
opt = Options(); opt.DetailLevel = ViewDetailLevel.Fine


def geo_stats(e):
    f = ed = 0
    def walk(g):
        global_ = None
        for o in g:
            if isinstance(o, Solid) and o.Faces.Size:
                yield o
            elif isinstance(o, GeometryInstance):
                for s in walk(o.GetInstanceGeometry()): yield s
    for s in walk(e.get_Geometry(opt)):
        f += s.Faces.Size; ed += s.Edges.Size
    return f, ed


fam = [x for x in FilteredElementCollector(doc).OfClass(Family) if x.Name == args["family_name"]][0]
od = os.path.join(args["tmp_dir"], u"old")   # имя файла = имя семейства, иначе загрузится как новое семейство
old_rfa = os.path.join(od, args["family_name"] + u".rfa")
if not os.path.isdir(od): os.makedirs(od)
fd = doc.EditFamily(fam); so = SaveAsOptions(); so.OverwriteExistingFile = True
fd.SaveAs(old_rfa, so); fd.Close(False)
# имя файла должно совпадать с именем семейства — копия нового под тем же именем
tg = TransactionGroup(doc, u"замер нагрузки (откат)"); tg.Start()
try:
    t = Transaction(doc, u"стены для замера"); t.Start()
    lvl = doc.GetElement(wall.LevelId)
    walls = []
    for i in range(int(args.get("n_walls", 10))):
        y = (5000 + i * 1500) / FT
        ln = Line.CreateBound(XYZ(0, -y - 50000 / FT, lvl.Elevation), XYZ(args.get("length_mm", 30000) / FT, -y - 50000 / FT, lvl.Elevation))
        walls.append(Wall.Create(doc, ln, wall.WallType.Id, lvl.Id, args.get("height_mm", 3000) / FT, 0, False, False))
    t.Commit()
    t = Transaction(doc, u"сетка и импосты"); t.Start()
    n_mul = 0; step = args.get("grid_mm", 1000) / FT
    for w in walls:
        g = w.CurtainGrid
        c = w.Location.Curve
        L = c.Length; k = 1
        while k * step < L - 1e-6:
            p = c.Evaluate(k * step / L, True)
            gl = g.AddGridLine(False, XYZ(p.X, p.Y, lvl.Elevation + 1 / FT), False)
            for si in range(gl.AllSegmentCurves.Size):
                try:
                    gl.AddMullions(gl.AllSegmentCurves.get_Item(si), mtype, False)
                except Exception:
                    pass
            k += 1
    t.Commit()
    for w in walls:
        for mid in w.CurtainGrid.GetMullionIds():
            if doc.GetElement(mid).Symbol.Id == mtype.Id: n_mul += 1
    res["mullions_fsc21"] = n_mul
    probe = [doc.GetElement(mid) for mid in walls[0].CurtainGrid.GetMullionIds() if doc.GetElement(mid).Symbol.Id == mtype.Id][0]
    res["old_faces_edges"] = geo_stats(probe)
    times = {"new": [], "old": []}
    for r_ in range(int(args.get("repeat", 2))):
        for tag, path in (("new", args["new_rfa"]), ("old", old_rfa)):
            t = Transaction(doc, u"перезагрузка " + tag); t.Start()
            t0 = time.time(); doc.LoadFamily(path, LO()); doc.Regenerate(); dt = time.time() - t0
            t.Commit(); times[tag].append(round(dt, 2))
            if tag == "new" and r_ == 0:
                res["new_faces_edges"] = geo_stats(probe)
    res["reload_s"] = times
except Exception as ex:
    res["errors"].append(str(ex)[:300])
finally:
    tg.RollBack(); res["rolled_back"] = True
__output__ = {"status": "partial" if res["errors"] else "completed_unverified", "summary": u"замер с откатом", "result": res}
