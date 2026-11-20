# Скрипты `fst-bimlib-release` (каталог, собран `fst-pipeline/scripts/scripts_catalog.py`)

Запуск в Revit — `horizun_execute_python` с `code_path`; вне Revit — `python -I` (с графикой — `python -P -E`). Новый скрипт записи — из шаблона `fst-curtainwall-author/scripts/_template_write.py`. После добавления скрипта — пересобрать каталог.

| Скрипт | Что делает | Аргументы / запуск |
|---|---|---|
| `bimlib_table_update.py` | Таблица bimlib (копия): новые описания в колонке D по типу строки. Точечная замена ячеек D в XML листа (остальной XML байт в байт), без сторонних библиотек. py bimlib_table_update.py <исходник.xlsx> <выход.xlsx> <отчёт.m | — |
