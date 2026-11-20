# Скрипты `fst-dwg-reader` (каталог, собран `fst-pipeline/scripts/scripts_catalog.py`)

Запуск в Revit — `horizun_execute_python` с `code_path`; вне Revit — `python -I` (с графикой — `python -P -E`). Новый скрипт записи — из шаблона `fst-curtainwall-author/scripts/_template_write.py`. После добавления скрипта — пересобрать каталог.

| Скрипт | Что делает | Аргументы / запуск |
|---|---|---|
| `dwg_pdf_compare.py` | Сверка DWG (тексты из dxf_extract) и PDF той же документации (тексты из extract_docs). Для каждого листа DWG находится наиболее похожая страница PDF (по словосочетаниям), считается сходство | Запуск: |
| `dwg_profiles.py` | Артикулы профилей из всех DWG (texts.txt после dxf_extract) против каталога альбомов (profiles.csv). Для каждого кода: подписи из DWG (самая частая — как имя), в каких DWG встречается и сколько раз, | Запуск: |
| `dwg_to_dxf.py` | DWG → DXF локально бесплатными средствами: LibreDWG (dwg2dxf, GPL) или ODA File Converter (если установлен). Ничего не скачивает и не отправляет. Конвертер ищется: | Запуск: |
| `dxf_extract.py` | Извлечение содержания DXF (после dwg_to_dxf.py): единицы, слои, листы, тексты, размеры, блоки с атрибутами. Только локально (ezdxf) | Запуск: |
| `dxf_find_texts.py` | Позиции текстов/выносок DXF, содержащих шаблон. py dxf_find_texts.py <dxf> <regex> | — |
| `dxf_ray.py` | Пересечения горизонтали y (или вертикали --vertical x) с линиями DXF в диапазоне. py dxf_ray.py <dxf> <y> <x0> <x1> [--vertical]  → список (координата, слой, тип) | — |
| `dxf_render.py` | Рендер DXF в PNG для визуальной сверки (тонкие чёрные линии на белом — без «толстых линий» DWG). Только локально (ezdxf + matplotlib) | Запуск: |
| `dxf_window_png.py` | Картинка окна DXF тонкими линиями (по слоям цветом). py dxf_window_png.py <dxf> x0,y0,x1,y1 <out.png> [--grid=10] | — |
