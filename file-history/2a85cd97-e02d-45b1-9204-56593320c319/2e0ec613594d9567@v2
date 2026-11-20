"""Рендер страниц PDF в PNG для просмотра глазами (сканы, буклеты, таблицы прайса, чертежи).

Только локально: pypdfium2 рисует страницу, PNG пишется стандартной библиотекой (zlib), без Pillow.
Запуск:
  py -P -E render_pdf.py <файл.pdf> <папка_вывода> [страницы: all | 1 | 1-3 | 2,5] [масштаб=2.0]
Выход: <папка>/<имя>_p<N>.png и список путей в stdout.
"""
import struct
import sys
import zlib
from pathlib import Path

import pypdfium2 as pdfium


def write_png(path, width, height, rows_rgb):
    raw = b"".join(b"\x00" + r for r in rows_rgb)
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def parse_pages(spec, n):
    if spec in (None, "", "all"):
        return list(range(1, n + 1))
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return [p for p in out if 1 <= p <= n]


def main(pdf_path, out_dir, pages=None, scale=2.0):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(pdf_path)
    stem = Path(pdf_path).stem
    for p in parse_pages(pages, len(pdf)):
        page = pdf[p - 1]
        bmp = page.render(scale=float(scale), rev_byteorder=True, fill_color=(255, 255, 255, 255))
        w, h, stride = bmp.width, bmp.height, bmp.stride
        buf = bytes(bmp.buffer)
        nchan = len(buf) // (stride * h) and (stride // w)
        rows = []
        for y in range(h):
            line = buf[y * stride: y * stride + w * nchan]
            if nchan == 4:  # RGBA/RGBX → RGB
                line = b"".join(line[i:i + 3] for i in range(0, len(line), 4))
            rows.append(line)
        dst = out / f"{stem}_p{p}.png"
        write_png(dst, w, h, rows)
        print(dst)
    pdf.close()


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit("usage: render_pdf.py file.pdf out_dir [pages] [scale]")
    sys.stdout.reconfigure(encoding="utf-8")
    main(a[0], a[1], a[2] if len(a) > 2 else None, a[3] if len(a) > 3 else 2.0)
