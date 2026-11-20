# -*- coding: utf-8 -*-
# КОПИИ семейств панелей (проект не меняется): во вложенных семействах профиля уплотнителя (FS.C-U5/U6/U8/U10)
# заменить контур на новый (seal_adapt.py, координаты семейства уплотнителя), загрузить в панель, сохранить копию панели.
# Аргументы: panels [имена семейств панелей], seals_json (adapt_*.json: seals.U5.loop ...), out_dir, save=true
import json, io, os
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
SE = json.loads(io.open(args["seals_json"], encoding="utf-8").read())["seals"]
OUT = args["out_dir"]
if not os.path.isdir(OUT): os.makedirs(OUT)
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


rows = []
for pn in args["panels"]:
    r = {"panel": pn, "seals": {}}
    pd = doc.EditFamily(fams[pn])
    try:
        sealfams = [f for f in FilteredElementCollector(pd).OfClass(Family) if u"Уплотнитель_FS.C-" in f.Name]   # список до перезагрузок
        for f in sealfams:
            u = f.Name.split(u"FS.C-")[1].split(u"_")[0]
            if u not in SE: continue
            fd = pd.EditFamily(f)
            try:
                own = [ce for ce in FilteredElementCollector(fd).OfClass(CurveElement) if ce.GetType().Name.startswith("Detail")]
                view = fd.GetElement(own[0].OwnerViewId); gs = own[0].LineStyle
                t = Transaction(fd, u"уплотнитель прямоугольником"); t.Start()
                for ce in own: fd.Delete(ce.Id)
                L = SE[u]["loop"]; n = 0
                for i in range(len(L)):
                    a_ = L[i]; b_ = L[(i + 1) % len(L)]
                    c = fd.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(a_[0] / FT, a_[1] / FT, 0), XYZ(b_[0] / FT, b_[1] / FT, 0)))
                    try: c.LineStyle = gs
                    except Exception: pass
                    n += 1
                t.Commit()
                fd.LoadFamily(pd, LO())
                r["seals"][u] = {"old_lines": len(own), "new_lines": n}
            finally:
                fd.Close(False)
        if args.get("save", True):
            o = SaveAsOptions(); o.OverwriteExistingFile = True
            pd.SaveAs(os.path.join(OUT, pn + ".rfa"), o); r["saved"] = True
    except Exception as ex:
        r["error"] = str(ex)[:200]
    finally:
        pd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified", "summary": u"копии панелей: %d; проект не менялся" % sum(1 for r in rows if r.get("saved")), "rows": rows}
