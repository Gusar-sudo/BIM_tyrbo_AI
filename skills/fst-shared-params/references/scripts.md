# Скрипты `fst-shared-params` (каталог, собран `fst-pipeline/scripts/scripts_catalog.py`)

Запуск в Revit — `horizun_execute_python` с `code_path`; вне Revit — `python -I` (с графикой — `python -P -E`). Новый скрипт записи — из шаблона `fst-curtainwall-author/scripts/_template_write.py`. После добавления скрипта — пересобрать каталог.

| Скрипт | Что делает | Аргументы / запуск |
|---|---|---|
| `check_registry_models.py` | Чтение: реестр параметров (_bim\params\registry.csv) и ФОП против всех открытых проектов — есть ли параметр, совпадает ли GUID, нет ли одноимённых с другим GUID | Аргументы: registry_csv, spf_path. |
| `registry_adsk_from_model.py` | Чтение: общие параметры ADSK_ из документа (имя, GUID, тип данных, используются ли семействами Фристайл) -> CSV строк реестра. Одноимённые с разными GUID помечаются «ДУБЛЬ» | Аргументы: out_csv, document_title (необязательно; иначе активный). |
