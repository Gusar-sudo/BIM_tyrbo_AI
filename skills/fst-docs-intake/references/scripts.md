# Скрипты `fst-docs-intake` (каталог, собран `fst-pipeline/scripts/scripts_catalog.py`)

Запуск в Revit — `horizun_execute_python` с `code_path`; вне Revit — `python -I` (с графикой — `python -P -E`). Новый скрипт записи — из шаблона `fst-curtainwall-author/scripts/_template_write.py`. После добавления скрипта — пересобрать каталог.

| Скрипт | Что делает | Аргументы / запуск |
|---|---|---|
| `extract_docs.py` | Извлекает текст из документов производителя (PDF, DOCX, XLSX) в папку extract/. Работает только локально: читает файлы, пишет .txt и index.json. Сеть не используется. | Запуск:  py -I extract_docs.py <папка_с_документами> <папка_для_результата> |
| `find_duplicates.py` | Поиск дублей среди документов производства и выбор актуального (правило: при расхождении — самый свежий). Вход: папка с документами и папка extract (после extract_docs.py, там index.json и тексты). | Запуск: py -P -E find_duplicates.py <корень_документов> <extract> <catalog> |
| `parse_albums.py` | Строит каталог из текстов альбомов технических решений (после extract_docs.py). Выход (UTF-8 с BOM, чтобы Excel открыл кириллицу): | Запуск: |
| `render_pdf.py` | Рендер страниц PDF в PNG для просмотра глазами (сканы, буклеты, таблицы прайса, чертежи). Только локально: pypdfium2 рисует страницу, PNG пишется стандартной библиотекой (zlib), без Pillow. | Запуск: |
