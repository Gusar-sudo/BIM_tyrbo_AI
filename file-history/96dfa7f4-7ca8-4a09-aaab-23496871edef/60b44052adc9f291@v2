"""Рендер DXF в PNG для визуальной сверки (тонкие чёрные линии на белом — без «толстых линий» DWG).

Только локально (ezdxf + matplotlib). Запуск:
  py -P -E dxf_render.py <файл.dxf> <папка_вывода> [листы: all | model | <имя листа>[,<имя>…]] [dpi=150]
Выход: <имя>_<лист>.png. Для пространства модели с большим чертежом можно ограничить окно:
  --window xmin,ymin,xmax,ymax   (в единицах чертежа)
"""
import argparse
import re
import sys
from pathlib import Path

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing import config as dcfg


def make_config():
    cfg = dcfg.Configuration()
    changes = {}
    if hasattr(dcfg, "ColorPolicy"):
        changes["color_policy"] = dcfg.ColorPolicy.BLACK
    if hasattr(dcfg, "BackgroundPolicy"):
        changes["background_policy"] = dcfg.BackgroundPolicy.WHITE
    if hasattr(dcfg, "LineweightPolicy"):
        changes["lineweight_policy"] = dcfg.LineweightPolicy.RELATIVE_FIXED  # одинаковая тонкая линия
    try:
        return cfg.with_changes(**changes)
    except Exception:
        return cfg


def render(doc, layout, dst, dpi, window=None):
    fig = plt.figure(figsize=(11.69, 8.27))  # А4 альбом
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    Frontend(ctx, MatplotlibBackend(ax), config=make_config()).draw_layout(layout, finalize=True)
    if window:
        ax.set_xlim(window[0], window[2]); ax.set_ylim(window[1], window[3])
    fig.savefig(dst, dpi=dpi, facecolor="white")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf"); ap.add_argument("out_dir")
    ap.add_argument("sheets", nargs="?", default="all"); ap.add_argument("dpi", nargs="?", type=int, default=150)
    ap.add_argument("--window")
    a = ap.parse_args()
    doc = ezdxf.readfile(a.dxf)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stem = Path(a.dxf).stem
    window = [float(v) for v in a.window.split(",")] if a.window else None
    targets = []
    if a.sheets in ("all", "model"):
        targets.append(("model", doc.modelspace()))
    if a.sheets != "model":
        wanted = None if a.sheets == "all" else set(a.sheets.split(","))
        targets += [(l.name, l) for l in doc.layouts if l.name != "Model" and (wanted is None or l.name in wanted)]
    for name, layout in targets:
        dst = out / f"{stem}_{re.sub(r'[^\w.-]+', '_', name)}.png"
        try:
            render(doc, layout, dst, a.dpi, window if name == "model" else None)
            print(dst)
        except Exception as e:
            print(f"ERR {name}: {e}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
