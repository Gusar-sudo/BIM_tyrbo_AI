"""Извлечение содержания DXF (после dwg_to_dxf.py): единицы, слои, листы, тексты, размеры, блоки с атрибутами.

Только локально (ezdxf). Запуск:
  py -P -E dxf_extract.py <файл.dxf> <папка_вывода>
Выход:
  <имя>.summary.json   — единицы ($INSUNITS → мм), габариты, слои, листы (имя, формат бумаги), счётчики
  <имя>.texts.txt      — все тексты по листам/пространству модели, с метками «=== лист: … ===» (для сравнения с PDF)
  <имя>.dims.csv       — размеры: лист; слой; тип; измерено_мм; текст_размера; x; y
  <имя>.blocks.csv     — вставки блоков: лист; блок; слой; x; y; атрибуты
Все длины — в миллиметрах с учётом $INSUNITS (дюймы ×25.4, метры ×1000 и т. д.).
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import ezdxf
from ezdxf import bbox

UNIT_MM = {0: None, 1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0, 14: 100.0}
UNIT_NAME = {0: "не задано", 1: "дюйм", 2: "фут", 4: "мм", 5: "см", 6: "м", 14: "дм"}


def clean(s):
    """Битые символы из конвертера (одиночные суррогаты) → «?», чтобы файл записался."""
    return s.encode("utf-8", "replace").decode("utf-8").replace("�", "?")


def plain(e):
    try:
        if e.dxftype() == "MTEXT":
            return clean(e.plain_text().strip())
        return clean((e.dxf.text or "").strip())
    except Exception:
        return ""


def nested_texts(e, depth=0, limit=5):
    """Тексты из виртуальных элементов блока/таблицы с рекурсией по вложенным блокам."""
    out = []
    if depth > limit:
        return out
    try:
        for sub in e.virtual_entities():
            st = sub.dxftype()
            if st in ("TEXT", "MTEXT", "ATTRIB"):
                s = plain(sub)
                if s:
                    out.append(s)
            elif st in ("INSERT", "ACAD_TABLE"):
                out.extend(nested_texts(sub, depth + 1, limit))
    except Exception:
        pass
    return out


def main(dxf_path, out_dir):
    doc = ezdxf.readfile(dxf_path)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    stem = Path(dxf_path).stem
    insunits = int(doc.header.get("$INSUNITS", 0))
    k = UNIT_MM.get(insunits) or 1.0  # неизвестно — считаем мм и помечаем

    spaces = [("Модель", doc.modelspace())] + [(l.name, l) for l in doc.layouts if l.name != "Model"]
    texts, dims, blocks = defaultdict(list), [], []
    counts, layers = Counter(), Counter()
    layouts_info = []
    for name, space in spaces:
        if name != "Модель":
            try:
                pw, ph = space.dxf.paper_width, space.dxf.paper_height
            except Exception:
                pw = ph = None
            layouts_info.append({"name": name, "paper_mm": [pw, ph], "entities": len(space)})
        for e in space:
            t = e.dxftype(); counts[t] += 1
            layers[getattr(e.dxf, "layer", "?")] += 1
            if t in ("TEXT", "MTEXT", "ATTRIB"):
                s = plain(e)
                if s:
                    texts[name].append(s)
            elif t == "ACAD_TABLE":  # таблицы AutoCAD (комплектация): тексты ячеек через виртуальные элементы
                texts[name].extend(nested_texts(e))
            elif t == "MULTILEADER":  # выноски с подписями (артикулы, названия деталей)
                try:
                    from ezdxf.tools.text import plain_mtext
                    s = clean(plain_mtext(e.get_mtext_content() or "").strip())
                    if s:
                        texts[name].append(s)
                except Exception:
                    pass
            elif t == "OLE2FRAME":
                counts["OLE2FRAME_не_читается"] += 1  # встроенные объекты (часто таблицы Excel) — только на картинке
            elif t == "DIMENSION":
                try:
                    meas = e.get_measurement()
                    meas = float(meas) * k if isinstance(meas, (int, float)) else None
                except Exception:
                    meas = None
                try:  # подпись размера = длина × DIMLFAC (узлы часто начерчены в масштабе)
                    lf = float(e.override().get("dimlfac", 1.0) or 1.0)
                except Exception:
                    lf = 1.0
                shown = None if meas is None else meas * lf
                p = getattr(e.dxf, "defpoint", None)
                dims.append({"sheet": name, "layer": e.dxf.layer, "type": e.dimtype, "measured_mm": "" if meas is None else round(meas, 2),
                             "dimlfac": round(lf, 6), "shown": "" if shown is None else round(shown, 2),
                             "text": clean(e.dxf.get("text", "") or ""), "x": round(p.x * k, 1) if p else "", "y": round(p.y * k, 1) if p else ""})
            elif t == "INSERT":
                attrs = clean("; ".join(f"{a.dxf.tag}={a.dxf.text}" for a in e.attribs)) if e.attribs else ""
                for a in e.attribs:
                    s = plain(a)
                    if s:
                        texts[name].append(s)
                p = e.dxf.insert
                blocks.append({"sheet": name, "block": e.dxf.name, "layer": e.dxf.layer, "x": round(p.x * k, 1), "y": round(p.y * k, 1), "attribs": attrs})
                # тексты внутри блоков (таблицы, штампы), включая вложенные блоки
                texts[name].extend(nested_texts(e))
    try:
        ext = bbox.extents(doc.modelspace(), fast=True)
        extents = {"min_mm": [round(v * k, 1) for v in ext.extmin][:2], "max_mm": [round(v * k, 1) for v in ext.extmax][:2]} if ext.has_data else None
    except Exception:
        extents = None

    summary = {"file": str(dxf_path), "dxf_version": doc.dxfversion, "insunits": insunits,
               "units": UNIT_NAME.get(insunits, str(insunits)), "mm_per_unit": UNIT_MM.get(insunits),
               "units_warning": None if insunits == 4 else "единицы чертежа не мм — длины пересчитаны; проверьте по известному размеру",
               "model_extents": extents, "layouts": layouts_info, "layers": dict(layers.most_common()),
               "entity_counts": dict(counts.most_common()), "texts": sum(len(v) for v in texts.values()),
               "dimensions": len(dims), "block_inserts": len(blocks)}
    (out / f"{stem}.summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(out / f"{stem}.texts.txt", "w", encoding="utf-8") as f:
        for name, _ in spaces:
            if texts.get(name):
                f.write(f"=== лист: {name} ===\n" + "\n".join(texts[name]) + "\n")
    for fname, rows, cols in ((f"{stem}.dims.csv", dims, ["sheet", "layer", "type", "measured_mm", "dimlfac", "shown", "text", "x", "y"]),
                              (f"{stem}.blocks.csv", blocks, ["sheet", "block", "layer", "x", "y", "attribs"])):
        with open(out / fname, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, delimiter=";"); w.writeheader(); w.writerows(rows)
    print(json.dumps({k2: summary[k2] for k2 in ("units", "units_warning", "texts", "dimensions", "block_inserts")}, ensure_ascii=False),
          "листов:", len(layouts_info))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: dxf_extract.py file.dxf out_dir")
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2])
