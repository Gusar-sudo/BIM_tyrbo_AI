# -*- coding: utf-8 -*-
# Жалюзи: светлые рёбра ламелей, чтобы 100+ ламелей с шагом 22 мм не сливались в чёрное на 3D с рёбрами.
# Открывает КОПИЮ панели (panel_rfa), во вложенном семействе ламели создаёт подкатегорию subcat с цветом линий rgb
# и материалом по подкатегории, назначает её телу ламели; перезагружает в панель и сохраняет копию. Проект не меняется.
# Аргументы: panel_rfa, subcat ("FT_Жалюзи_Ламели"), rgb [175,175,180]
import json
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
res = {}


class _LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, a, b, src, c):
        src.Value = FamilySource.Family; c.Value = True; return True


pd = app.OpenDocumentFile(args["panel_rfa"]); nd = None
try:
    lam = [fi for fi in FilteredElementCollector(pd).OfClass(FamilyInstance) if u"Ламел" in fi.Symbol.Family.Name]
    fam = lam[0].Symbol.Family
    nd = pd.EditFamily(fam)
    t = Transaction(nd, u"FT: подкатегория ламелей"); t.Start()
    cat = nd.OwnerFamily.FamilyCategory
    sub = None
    for s in cat.SubCategories:
        if s.Name == args.get("subcat", u"FT_Жалюзи_Ламели"):
            sub = s
    if sub is None:
        sub = nd.Settings.Categories.NewSubcategory(cat, args.get("subcat", u"FT_Жалюзи_Ламели"))
    c = args.get("rgb", [175, 175, 180]); sub.LineColor = Color(c[0], c[1], c[2])
    n = 0
    for g in FilteredElementCollector(nd).OfClass(GenericForm):
        g.Subcategory = sub; n += 1
    t.Commit()
    res.update(category=cat.Name, forms=n, family=fam.Name)
    nd.LoadFamily(pd, _LO()); nd.Close(False); nd = None
    pd.Save()
    res["saved"] = args["panel_rfa"]
finally:
    if nd is not None:
        nd.Close(False)
    pd.Close(False)
__output__ = {"status": "completed_unverified", "summary": u"ламели: подкатегория, тел %d; копия панели сохранена" % res.get("forms", 0), "result": res}
