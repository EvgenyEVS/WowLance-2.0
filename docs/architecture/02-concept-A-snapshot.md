# Концепция A — Snapshot Room («скопировали и исполняем»)

| Поле | Значение |
|------|----------|
| **Код** | A / Snapshot |
| **Обзор** | [01-overview.md](01-overview.md) |
| **Идея** | В момент «Перейти в WowLance» Strategy отдаёт полный пакет; WowLance **копирует** стратегию, SOP и документы в свою PostgreSQL. Дальше комната живёт автономно. |
| **Роль относительно C** | Упрощённый MVP того же направления (без merge обновлений) |

---

## 1. Суть

Фаундер в Studio нажимает кнопку. После SSO Gateway направляет в WowLance. Сервис:

1. принимает идемпотентный `handoff_id` + payload (или забирает артефакт из object storage по URI);
2. создаёт **Room** + локальный **Project/Engagement**;
3. сохраняет `strategy_snapshot` (JSON) и копии/ссылки на файлы SOP;
4. создаёт shadow-пользователей членов (директор уже есть по Keycloak `sub`);
5. (опционально) создаёт стартовый спринт / набор задач из шаблона пакета.

Дальнейшие правки стратегии **в Studio не протекают** в комнату автоматически. Нужен новый handoff / «перезапуск» / ручной импорт — продуктово решить с PO (см. §7).

Фрилансеры: при появлении в Talent как verified — event → WowLance **копирует** профиль в локальный roster. Matching и UI каталога комнаты читают **только** локальную БД.

---

## 2. Потоки данных

```text
[Founder Studio] --handoff payload/event--> [WowLance ROOM]
                     copy strategy+SOP
                     create room
[Talent] --FreelancerVerified--> [WowLance roster copy]
[Keycloak] --JWT sub--> все сервисы
[WowLance] --adapters--> CRM / Meet / Payment / Invoicing
```

**Запрещено:** SQL/ replication в БД Studio или Talent.

---

## 3. Что копируем при handoff (черновик контракта)

Минимальный payload (OpenSpec позже зафиксирует schema):

| Блок | Примеры полей | Зачем в комнате |
|------|---------------|-----------------|
| Identity | `handoff_id`, `strategy_id`, `strategy_version`, `founder_sub` | Идемпотентность, аудит |
| Project meta | name, market, timezone | Шапка комнаты |
| Sales strategy | offer, ICP/audience, UTPs, hot_criteria, objections | Бывший `Project.input_data` |
| Operating model | BP graph / stages, SOP docs (URI+checksum), RACI | Вкладки BP / SOP |
| Staffing intent | package / roles / levels / hours | Слоты / team seats |
| Commercial | budget hint, tariff code, payment_ref? | Связка с Billing |
| Room type | `sale` \| `develop` \| … | Шаблон процессов |

Документы: предпочтительно **URI в общем object storage** + checksum; байты в event bus не тащить. При политике «полная автономность» WowLance может **докачать** файл в свой bucket при handoff.

---

## 4. Модель в WowLance (эволюция текущего кода)

Из текущего монолита:

| Было | Станет в A |
|------|------------|
| `Project.input_data` (ручной wizard) | `strategy_snapshot` + `source_strategy_id/version` (immutable после create) |
| Wizard / presets UI | Удалить как main path; demo seed эмулирует handoff |
| `RoomDocument` upload «с нуля» | Импорт из snapshot + доп. загрузки уже **в комнате** (операционка) |
| `FreelancerProfile` как SoT | Локальная копия; поля `talent_synced_at`, `source_talent_version` |
| `handle_project_paid` | Триггер: handoff **или** webhook Payment «room funded» — уточнить с Billing |
| Lead + Hot inbox | Sale-шаблон: лиды либо локально thin, либо сразу push в CRM |

Новое ядро универсальной комнаты:

- `BusinessProcess` / stages (описание, не обязательно BPM engine);
- `SopDocument` (version, checksum, storage_key);
- `Sprint` (даты, цель);
- `Task` (обобщить текущий `pipeline.Task`; Quality Gate — опция шаблона).

---

## 5. Плюсы

- Комната **устойчива**: Studio и Talent могут лежать — исполнение и SOP на месте.
- Простой mental model для команды: «импорт → работа».
- Хорошо стыкуется с аудитом: «продавали по версии X».
- Ближе всего к уже существующей идее снапшота `functional_roles` / budget в 1.0.
- Быстрее закрыть вертикальный срез, чем B или полный C.

## 6. Минусы и риски

- Рассинхрон: фаундер правил стратегию в Studio, комната показывает старое.
- Дублирование storage (файлы) и риск «забыли обновить checksum».
- Повторный handoff без политики = две комнаты или тихий overwrite.
- Навыки фрилансера устаревают, пока нет периодического re-sync (минимальный cron/event всё равно нужен).

---

## 7. Ключевые переделки относительно репозитория 1.0

1. Greenfield FastAPI + React + PG (или strangler: API рядом, UI новый).
2. Заменить вход директора: удалить зависимость UX от `/setup/` wizard как SoT.
3. Handoff consumer + идемпотентность (таблица `handoffs`).
4. Иммутабельный snapshot + UI «только чтение» для strategy/SOP origin.
5. Talent roster ingest; выключить публичную регистрацию фрилансера.
6. Keycloak shadow users; убрать password auth из продукта.
7. Адаптеры внешних сервисов; не переносить stub как прод-путь.
8. Расширить комнату до BP/SOP/Sprint (не только leads kanban).

---

## 8. Вопросы к смежникам (специфика A)

**Strategy**

- Гарантируете ли полный self-contained payload (все URI доступны WowLance по service identity)?
- Можно ли делать **повторный** handoff той же strategy? С той же `strategy_version`?
- Нужен ли endpoint «export snapshot» или только push event?
- TTL ссылок на файлы?

**Talent**

- Полный профиль в event или «id + WowLance pulls GET /freelancers/{id} один раз»?
- Как часто шлёте update (skills changed)? В A без этого — stale skills.

**Billing / Payment**

- Handoff до оплаты или после? Кто блокирует staffing без money?

**Platform storage**

- Общий bucket с ACL между Studio и WowLance или copy-on-write в bucket комнаты?

---

## 9. Вопросы PO (специфика A)

1. После старта комнаты стратегия в Studio **замораживается**?
2. Если фаундер ошибся в SOP — правим в комнате (ломаем «чистый снимок») или новый handoff?
3. Две комнаты на одну strategy (sale + develop) — норма?
4. Каталог фрилансеров в UI WowLance нужен, если все уже verified в Talent?
5. MVP: только sale-шаблон или сразу develop?

---

## 10. Когда выбирать A

- Нужен быстрый интеграционный MVP «кнопка → комната».
- Strategy/Talent ещё нестабильны online.
- PO согласен на «версия зафиксирована при входе».
- Позже можно эволюционировать в **C**, добавив `StrategyUpdated` + Accept.

## 11. DoD концепции A (интеграционный срез)

- [ ] OpenSpec `FounderHandoff` v1 принят обеими командами  
- [ ] Кнопка Studio создаёт ровно одну комнату на `handoff_id`  
- [ ] SOP/strategy видны в React комнате без запросов в БД Studio  
- [ ] Verified freelancer появляется в roster WowLance без ручной регистрации  
- [ ] JWT Keycloak пускает founder/freelancer в свои экраны  
- [ ] Meet link и CRM stub/адаптер вызываются из комнаты, не из монолита Django  

---

## 12. Вердикт

**A — рабочий стартовый контур** для входа в платформу. Не запрещает внешние CRM/Meet/Payment. Слабое место — устаревание снимка; закрывается политикой заморозки или апгрейдом до C.
