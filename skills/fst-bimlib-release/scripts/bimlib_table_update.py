# -*- coding: utf-8 -*-
# Таблица bimlib (копия): новые описания в колонке D по типу строки. Точечная замена ячеек D в XML листа
# (остальной XML байт в байт), без сторонних библиотек. py bimlib_table_update.py <исходник.xlsx> <выход.xlsx> <отчёт.md>
import sys, re, zipfile
from xml.sax.saxutils import escape
from xml.etree import ElementTree as ET
SRC, OUT, REP = sys.argv[1:4]
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
z = zipfile.ZipFile(SRC)
files = {n: z.read(n) for n in z.namelist()}
sst = ET.fromstring(files["xl/sharedStrings.xml"])
strings = ["".join(t.text or "" for t in si.iter(NS + "t")) for si in sst.findall(NS + "si")]
xml = files["xl/worksheets/sheet1.xml"].decode("utf-8")
CELL = re.compile(r'<c r="([A-Z]+)(\d+)"([^>]*?)(?:/>|>(.*?)</c>)', re.S)


def val(attrs, inner):
    if inner is None:
        return ""
    m = re.search(r"<v>(.*?)</v>", inner, re.S)
    if 't="s"' in attrs and m:
        return strings[int(m.group(1))]
    if "inlineStr" in attrs:
        return "".join(re.findall(r"<t[^>]*>(.*?)</t>", inner, re.S))
    return m.group(1) if m else ""


cells = {}
for m in CELL.finditer(xml):
    cells[(m.group(1), int(m.group(2)))] = val(m.group(3), m.group(4))

TAIL = " Производитель ФристайлТехнолоджи. Модель разработана с применением ФОП ADSK 2017. Имеется спецификация по ГОСТ"
BASE = "Версия Autodesk Revit 2026. Семейство выполнено в двух уровнях детализации с УГО профилей импостов."


def new_desc(name, short, old):
    lead = short.replace("Цельностекляная", "Цельностеклянная").strip() + "."
    if "система М1" in name:
        extra = ""
    elif name.startswith("Каркасная"):
        extra = " Стекло 5, 6, 8 или 10 мм, уплотнитель FS.C-U по толщине стекла."
    elif name.startswith("Цельностекл"):
        extra = " Стекло 8 или 10 мм (отдельные типы стен), стык стёкол — межстекольный профиль FS.C-156, уплотнитель FS.C-U по толщине стекла."
    else:
        extra = ""
    return "%s %s%s%s%s" % (lead, BASE, extra, TAIL, " и спецификация деталей сборки" if "спецификация деталей сборки" in old else "")


changes = []
rows = sorted(set(r for (col, r) in cells if r > 1))
newd = {}
for r in rows:
    name = cells.get(("B", r), ""); short = cells.get(("C", r), ""); old = cells.get(("D", r), "")
    if not name.strip() or ("D", r) not in cells:
        continue
    nd = new_desc(name, short, old)
    if nd != old:
        newd[r] = nd; changes.append((cells.get(("A", r), ""), name, old, nd))


def repl(m):
    col, r = m.group(1), int(m.group(2))
    if col != "D" or r not in newd:
        return m.group(0)
    attrs = re.sub(r'\s*t="[^"]*"', "", m.group(3))
    return '<c r="D%d"%s t="inlineStr"><is><t>%s</t></is></c>' % (r, attrs, escape(newd[r]))


xml2 = CELL.sub(repl, xml)
files["xl/worksheets/sheet1.xml"] = xml2.encode("utf-8")
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as o:
    for info in z.infolist():
        o.writestr(info, files[info.filename])
# проверка: перечитать выход
z2 = zipfile.ZipFile(OUT); x3 = z2.read("xl/worksheets/sheet1.xml").decode("utf-8")
ET.fromstring(x3.encode("utf-8"))
ok = sum(1 for r, nd in newd.items() if escape(nd) in x3)
with open(REP, "w", encoding="utf-8") as f:
    f.write("# Таблица bimlib — изменения описаний (черновик 2026-11-12)\n\n")
    f.write("Исходник: `bimlib-freestyletech-001-048_исходник.xlsx` (копия файла производителя, не изменялась). Изменено строк: %d (проверено в выходном файле: %d). Меняется только колонка «Описание»; наименования, коды, файлы, картинки — без изменений.\n\n" % (len(changes), ok))
    for n, name, old, nd in changes:
        f.write("## №%s · %s\n- было: %s\n- стало: %s\n\n" % (n, name, old, nd))
print("changed", len(changes), "verified", ok)
