# Библиотека skill «Фристайл BIM» v1.2.0

**Что нового в 1.2.0 (14.11.2026):** каталог скриптов в каждом skill (`references/scripts.md`, сборка `fst-pipeline/scripts/scripts_catalog.py`); шаблон скрипта записи `fst-curtainwall-author/scripts/_template_write.py`; стекло — наименования «Стекло N мм», ведомость стекла и пересчёт (`glass_calc.py`); ГКЛ — типы стен «Глухое заполнение ГКЛ», параметры площади/кусков/«больше листа», ведомость и раскрой на листы 1100×2500/3000 (`gkl_pieces.py`, `gkl_cut.py`); требования аудита F1.6, F3.5–3.6, F5.3–5.4; уроки разнесены по разделам; реестр параметров с ADSK и проверка `check_registry_models.py`. Список команд будущего плагина Revit — `revit_plugin_backlog.md`.

Комплект skill для Claude, по которому BIM-отдел ведёт библиотеку моделей «Фристайл Технолоджи» по методологии fetchBIM. Человек проверяет работу Claude только визуально: все числа проверяются автоматически, человеку приходят только гейты — ТЗ и приёмка — одной страницей с вопросами.

## Состав (14 skill)
| Этап | Skill | Что делает |
|---|---|---|
| — | **fst-pipeline** | Главный: этапы, статус каждой системы (`_bim\status.md`), какой skill следующий. Начинать с него: «что дальше по М2?» |
| 0 | fst-docs-intake | Документы производства → тексты, каталог профилей, правила стекла, дубли и актуальность, рендер PDF, вопросы. Скрипты: `extract_docs.py`, `parse_albums.py`, `find_duplicates.py`, `render_pdf.py` |
| 0 | fst-dwg-reader | DWG без AutoCAD и Revit: DWG → DXF → тексты, размеры (мм), блоки/артикулы, листы, картинки, сверка с PDF. Скрипты: `dwg_to_dxf.py`, `dxf_extract.py`, `dxf_render.py`, `dwg_pdf_compare.py` |
| 1, 5 | fst-curtainwall-author | Устройство библиотеки (витражи М1–М3, импосты FSC, двери), инвентаризация, сборка/обновление, перенос тест → библиотека, журнал уроков. Скрипты: `inventory_from_query.py`, `export_families.py`, `library_load.py`, `load_rfas.py`, `open_doc.py`, `save_doc.py` |
| 5 | fst-profile-author | Семейства профилей импостов (контур тела, рейки, пазы, ГКЛ, зеркальные и угловые столбы) и панелей (стекло формулой, уплотнитель, глухая ГКЛ, жалюзи). 23 скрипта |
| 1, 8 | fst-family-audit | Аудит: требования Фристайл F1–F6 + стекло по формулам альбома. Скрипт: `check_glass.py` |
| 1, 8 | fetch-checklist-audit | Общий чек-лист fetchBIM (8 разделов) |
| 2, 9 | fst-visual-review | Страница приёмки: картинки, вопросы, «Принять / Вернуть», решение с отпечатком |
| 3 | fst-tz-gate | ТЗ на пересборку из аудита и ответов приёмки (гейт 1) |
| 4 | fst-shared-params | Реестр параметров ADSK + FT_, проверка GUID, добавление через dry-run |
| 5 | partition-family-author | Правила сборки загружаемых семейств перегородок (для новых продуктов: раздвижные, мобильные и т. п.) |
| 6 | fst-project-test | Тест в проекте: flex на крайних размерах, двери, предупреждения, лист PDF для приёмки; листы «модель рядом с альбомом» (вертикальные сечения + 3D, фасад и узлы, схемы углов). Скрипты: `vertical_nodes.py`, `partition_elev_sections.py`, `corner_schemes.py`, `scheme_sheets.py`, `render_pdf_pages.py`, `album_fig_map.py`, `export_views_png.py` |
| 7 | fst-spec-price | Пересчёт спецификации (длина × расход) и сверка с ГОСТ-спецификацией Revit. Скрипт: `spec_calc.py` |
| 10 | fst-bimlib-release | Пакет выпуска, таблица bimlib, журнал версий, сопровождение |

## Установка
**Claude Code (рабочие места BIM-отдела)** — плагин:
```
/plugin marketplace add "C:\Users\user\Desktop\Фристайл\_bim\plugin"
/plugin install fst-bim@fst-bim-local
```
(путь — папка, где лежит этот README и `.claude-plugin\marketplace.json`; её можно положить на общий диск).
Важно: на этой машине те же skill уже стоят как личные (`%USERPROFILE%\.claude\skills`). Ставить плагин сюда не нужно — будут дубли.

**claude.ai** — файлы `dist\*.skill`: открыть файл в чате и нажать «Save skill» (если организация разрешает свои skill). Скрипты внутри skill на claude.ai работают только при наличии среды выполнения кода; работа с Revit (horizun) — только в Claude Code / Claude desktop с подключённым MCP horizun-revit.

## Требования
- Revit 2023–2027 + MCP **horizun-revit** (рекомендуемый профиль `safe_write`; для экспорта PDF листов — `full_write` по решению человека).
- Python 3 (`py`) + бесплатные пакеты: `pypdf` (текст PDF), `pypdfium2` (картинки PDF), `ezdxf` + `matplotlib` (DXF), `pillow` (картинки пазов `slot_widen.py`). Установка: `py -m pip install --user pypdf pypdfium2 ezdxf matplotlib pillow`.
- Конвертер DWG → DXF: LibreDWG (GPL, `dwg2dxf.exe`) или ODA File Converter (бесплатный, лицензию принимает человек).
- Проект: папка с документами производства; всё производное — в её подпапке `_bim\`.

## Данные и безопасность
- Ни один skill не обращается к сети, не загружает файлы наружу и не использует сторонние сервисы и ИИ. Проверка: в скриптах нет `requests`, `urllib`, `socket`, `subprocess`, `curl`, base64.
- Запись в модели — только dry-run → визуальный пакет → «Принять» → применение; исходники bimlib не открываются на запись (работа с копиями в `_bim\work\`).
- Публикацию на bimlib.pro делает человек.

## Обновление комплекта
Источник истины — `%USERPROFILE%\.claude\skills`. После правок: `build.ps1 -Version 1.0.1` пересобирает плагин и `dist\` (проверка формата встроена). Изменения и уроки — в `fst-curtainwall-author\references\lessons.md`.
