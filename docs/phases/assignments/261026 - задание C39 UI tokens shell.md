# Задание: C39 — UI tokens + shell как в WowLance 1.0

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-26 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c39-ui-tokens-shell` |
| **База** | актуальный `main` **после C38** (`2f395f7`+) |
| **Параллельность** | ⚠️ **база для C40 · C41** — мержить **первым**; ✅ параллельно с C42 (docs/QA visual) |
| **Фаза** | C39 (визуал only — design tokens + app chrome) |
| **Стек** | **React · CSS** (без FastAPI / без смены контрактов) |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [зоны](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) · UI 1.0: `WowLance/static/css/style.css`, `fonts.css`, `templates/base.html` |
| **Параллель** | [C40](261026%20-%20задание%20C40%20UI%20room%20chrome.md) · [C41](261026%20-%20задание%20C41%20UI%20panels.md) · [C42](261026%20-%20задание%20C42%20UI%20visual%20QA.md) |

> **Только визуал.** Архитектуру, API, RBAC, домен, роуты данных — **не** менять. Live / новые контракты — не делать.

---

## 1. Зачем

Stub-shell 2.0 (Segoe + узкая колонка) не похож на 1.0 (Syne / DM Sans, токены, `app-shell`, sticky header). Стейкхолдерам нужна **узнаваемая** картинка. C39 — фундамент: токены и оболочка приложения.

---

## 2. Reference (1.0)

Копировать **визуальные значения**, не Django-логику:

- `static/css/style.css` — `:root` (цвета, radius, shadow, `--font-*`, `--header-h`)
- `static/css/fonts.css` + `static/fonts/*.woff2` — **скопировать** в `frontend/public/fonts/` (или `src/assets/fonts/`)
- `templates/base.html` — структура `app-shell` + `site-header` + logo mark «W»

Допустимо: сократить CSS до нужных классов (не тащить весь 2800-строчный файл слепо).

---

## 3. Не делать

- Менять endpoints, schemas, pytest домена.  
- Новые поля RoomRead / граничные YAML.  
- Пиксель-в-пиксель весь 1.0 (дашборды директора, мастер, каталог) — **только** оболочка app + Home/Login/Room wrapper.  
- Трогать бизнес-кнопки панелей (это C41).

---

## 4. Must-fix

1. **CSS variables** 1.0 в `:root` 2.0 (`--bg`, `--text`, `--accent`, `--radius`, fonts…).  
2. **Шрифты** Syne + DM Sans подключены (self-host woff2 из 1.0).  
3. **Фон** как в 1.0: `--bg` + лёгкий grid/gradient (`body::before` или эквивалент).  
4. **Layout:** `app-shell` на всю ширину; контент в `.container` (~1120px), не `max-width: 40rem`.  
5. **Sticky header:** logo mark + «WowLance», ссылка Home / Login как сейчас по смыслу; без новых маршрутов.  
6. **Кнопки:** базовые `.btn` / `.btn-primary` / `.btn-secondary` / `.btn-sm` — стили 1.0; постепенно заменить `slot-action` на эти классы **в shell** (Home, Login, back-link). Панели комнаты — минимум или оставить на C41.  
7. G1–G10 / founder-demo **функционально** без регрессии (только look).

---

## 5. DoD

- [ ] Tokens + fonts + app-shell + header + container.  
- [ ] Home + Login выглядят в языке 1.0.  
- [ ] RoomPage обёрнут в тот же shell (панели могут ещё быть «старыми» до C41).  
- [ ] README frontend: 5–8 строк «visual parity C39, reference 1.0 CSS».  
- [ ] Нет изменений backend.  
- [ ] PR (+ скрины Home/Login/Room header до/после желательны).

---

## 6. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c39-ui-tokens-shell
База: origin/main после C38.
Reference UI: соседний репо WowLance 1.0 static/css/style.css + fonts.css + base.html.
Задание: docs/261026 - задание C39 UI tokens shell.md
ТОЛЬКО визуал. Не меняй API/RBAC/домен.

Сделай: tokens, fonts, app-shell, sticky header, container width, btn primitives на Home/Login.
План 5–7 шагов, маленькие коммиты. C39 мержить до C40/C41.
```
