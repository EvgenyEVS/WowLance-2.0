# WowLance 2.0 — общий обзор: вход в большую инфраструктуру

| Поле | Значение |
|------|----------|
| **Дата** | 2026-09-28 |
| **Статус** | Черновик для обсуждения с PO и смежными командами |
| **База** | Текущий репозиторий WowLance (Django modular monolith, ADR-001) |
| **Целевой стек платформы** | Keycloak · API Gateway · FastAPI · React · PostgreSQL · OpenSpec · Superpowers |
| **Связанные документы** | [A — Snapshot](02-concept-A-snapshot.md) · [B — Federated](03-concept-B-federated.md) · [C — Hybrid Contract](04-concept-C-hybrid.md) |

---

## 1. Решение, которое уже принято

WowLance входит в общую инфраструктуру продукта:

- **авторизация** — общий Keycloak; у каждого микросервиса своя БД пользователей, связь по **стабильному ID** (`sub` / UUID);
- **вход** — API Gateway;
- **бэкенд сервиса** — FastAPI;
- **фронт** — React;
- **БД сервиса** — PostgreSQL (своя схема, без чужих FK);
- контракты и процесс — **OpenSpec**, практики **Superpowers**.

Продуктовый сдвиг:

1. **Директор (фаундер)** не собирает проект «с улицы» в wizard WowLance. Стратегия продаж и документация готовятся в **соседнем сервисе** (ниже — *Strategy / Founder Studio*). Вход — кнопка «Перейти в WowLance и начать продажи прямо сейчас» (бесшовный SSO).
2. **Фрилансер** не регистрируется и не верифицируется в WowLance. До нас — регистрация, стажировка, верификация в **Talent-сервисе**. К нам попадают только подтверждённые. У WowLance — **своя** БД фрилансеров (тень + рабочий контур комнаты) + Keycloak.
3. Ядро продукта — **универсальная комната** (sale **и** develop): бизнес-процессы, SOP, спринты, таски. CRM, Jitsi, payment, invoicing, order и т.п. — **внешние** сервисы, не вшитый монолит.

Текущий WowLance (биржа + sale-room на Django templates) остаётся **источником домена и UX-уроков**, а не целевой формой деплоя.

---

## 2. Прямой ответ: копировать стратегию или читать чужую БД?

**Чужую БД Strategy читать напрямую нельзя** (антипаттерн микросервисов: связанный деплой, ночные падения «чужого» Postgres, невозможность независимо версионировать схему).

Остаются два легитимных механизма + гибрид:

| Подход | Суть | Когда уместен |
|--------|------|----------------|
| **Снимок (copy-on-enter)** | В момент кнопки Strategy отдаёт payload / событие; WowLance **копирует** стратегию, SOP, документы (или ссылки на object storage) в свою БД | Комната должна работать, даже если Strategy лежит; аудит «что исполняли» |
| **Живая ссылка (reference)** | В комнате только `strategy_id` + API Strategy; документы всегда с origin | Стратегия часто меняется; WowLance — тонкий исполнитель |
| **Контрактный гибрид (рекомендация по умолчанию)** | При входе — **версионированный снимок**; Strategy шлёт события `StrategyUpdated`; комната решает принять / отклонить / смержить обновление | Реализм: исполнение стабильно, источник правды у фаундера не исчезает |

**Для фрилансеров:** то же логика. Talent — source of truth по верификации и «паспортным» навыкам. WowLance хранит **локальный roster** (id, display, skills snapshot, availability для staffing) и подтягивает обновления событиями / sync API. Matching и права комнаты **не** делают live JOIN в БД Talent.

Подробности и trade-off — в документах A / B / C.

---

## 3. Что есть сейчас vs что должно стать

| Сейчас (репозиторий) | WowLance 2.0 |
|----------------------|--------------|
| Django + server-rendered HTML | FastAPI + React за Gateway |
| Логин email/password, `users.User` | Keycloak; локальная тень User по UUID |
| Wizard / пресеты / stub оплата → `handle_project_paid` | Handoff из Strategy + внешний Payment |
| Регистрация фрилансера, видео, модерация в BIZ | Только verified из Talent; локальный профиль-тень |
| Комната ≈ Cold Calling / LinkedIn + задачи/лиды | Универсальная комната: BP, SOP, спринты, tasks (sale + develop) |
| Встроенные материалы `RoomDocument`, чат polling, Jitsi-ссылка, stub pay | Внешние: CRM, Meet, Payment, Invoicing, Order… |
| Matching SQL по `FreelancerProfile` в той же БД | Matching через локальный roster + контракт Talent |
| ADR-001: монолит, без брокера | Отдельный сервис(ы), события, OpenSpec-контракты |

**Сохраняемый капитал домена (не выкидывать смыслы):**

- комнатный RBAC (директор / тимлид / фрилансер / менеджер-платформы);
- staffing / слоты / «team seats»;
- задачи + отчёт с доказательством (Quality Gate) — как паттерн для sale; для develop — адаптировать DoD;
- Hot → handoff менеджеру → **маппится** на внешний CRM, а не на новую внутреннюю воронку;
- расторжение / архив членства;
- снимок состава и unit-economics как идея «зафиксировали, что купили».

---

## 4. Ключевые переделки и переработки текущего проекта

### 4.1. Платформенный срез (обязательный)

1. **Вынос auth** → Keycloak OIDC; удаление/сужение парольной регистрации и activation email как source of truth.
2. **Локальная User DB** — shadow: `id=Keycloak.sub`, role cache, status sync, display name; без паролей.
3. **PostgreSQL** вместо SQLite; миграции схемы комнаты заново или через перенос доменных сущностей.
4. **API-first FastAPI** вместо Django views/templates; React — единственный UI комнаты.
5. **API Gateway** — маршруты `/wowlance/*`, JWT validation, rate limit; сервис-сервис — client credentials / token exchange.
6. **Контракты OpenSpec** на: handoff из Strategy, sync Talent, webhooks Payment, CRM lead push.

### 4.2. Продуктовый срез комнаты

7. **Убрать / заменить** директорский wizard и пресеты архитектуры как главный вход (логика уезжает в Strategy).
8. **Универсальная модель комнаты:** не только `Lead` Cold/Warm/Hot, а BP / SOP / Sprint / Task (+ тип комнаты `sale` | `develop` | …).
9. **Документы и стратегия:** модель «imported snapshot + version» вместо редактируемого с нуля `input_data` wizard’а (поле можно эволюционировать в `strategy_snapshot`).
10. **Интеграции вместо встройки:** Jitsi/Meet, CRM, Payment, Invoicing — адаптеры; stub оставить только для локальной разработки.
11. **Менеджер Hot-inbox** → тонкий адаптер «создать сущность во внешнем CRM» + deeplink; не строить Deal CRM внутри.

### 4.3. Фрилансеры и staffing

12. **Отключить** публичную регистрацию фрилансера и in-app verify как обязательный путь.
13. **Roster + events** из Talent; matching читает локальную БД WowLance.
14. Видео/навыки: политика «снимок при появлении в roster + обновление по событию»; duration 40s — контракт Talent или WowLance (решить с PO).

### 4.4. Что сознательно не переносить 1:1

- Django Admin как основной ops-UI (заменить на admin React / Backoffice или Keycloak + тонкий ops).
- SQLite-специфичный деплой и `seed_demo_scenario` в текущем виде (переписать под demo-realm Keycloak + fixtures).
- Связанные шаблоны `_room_header`, SSR RBAC — перепроектировать в React route guards + BFF/API claims.

---

## 5. Три концепции (кратко)

| | **A. Snapshot Room** | **B. Federated Live** | **C. Hybrid Contract** ★ |
|--|----------------------|----------------------|---------------------------|
| Стратегия / SOP | Полное копирование при входе | Только ссылки + live API | Версионированный снимок + события обновления |
| Фрилансеры | Полный copy профиля | Тонкая тень + live skills | Roster snapshot + Talent events |
| Устойчивость комнаты | Высокая (работает offline от Strategy) | Низкая без Strategy/Talent | Высокая; обновления контролируемы |
| Сложность | Средняя | Высокая (latency, fallback) | Средняя+/высокая (версии, merge UX) |
| Риск рассинхрона | Стратегия в Studio устарела относительно комнаты | Комната «плывёт» при каждом чтении | Управляется версиями |
| Рекомендация | Быстрый MVP handoff | Если Studio — единственный SoT и всегда online | **Базовый выбор для 2.0** |

★ — рекомендуемая точка старта для переговоров с PO; A — упрощённый MVP того же направления; B — только при жёстком требовании «никогда не копировать».

Полные тексты: [02](02-concept-A-snapshot.md), [03](03-concept-B-federated.md), [04](04-concept-C-hybrid.md).

---

## 6. Вопросы к смежным микросервисам

### 6.1. Identity / Keycloak

- Единый realm? Имена realm roles (`director`, `teamlead`, `freelancer`, `manager`, …)?
- Стабильность `sub` при merge аккаунтов / смене email?
- Кто создаёт пользователя: Strategy registration, Talent onboarding, или оба пишут в Keycloak?
- Logout SSO обязателен для всех клиентов?
- Token exchange / client credentials для ROOM → Talent / Strategy / CRM?

### 6.2. Strategy / Founder Studio (источник стратегии)

- Точный payload кнопки «в WowLance»: какие поля обязательны (offer, ICP, BP, SOP, files, package/slots, budget)?
- Синхронный API create-room **или** async событие `FounderHandoffRequested`?
- Идемпотентный ключ handoff (`handoff_id` / `strategy_version_id`)?
- Документы: байты в object storage + URI, или multipart в событии?
- После handoff: Strategy **read-only** / продолжает редактироваться / «заморозка версии»?
- Кто владеет названием проекта и KPI после входа в комнату?
- Deep link обратно в Studio из комнаты?

### 6.3. Talent / Freelancer pipeline

- Событие `FreelancerVerified` / `FreelancerSuspended` — контракт и гарантии доставки?
- Минимальный профиль для roster: skills schema, levels, channels (cold/linkedin), video URL, languages?
- Может ли WowLance **писать обратно** (rating, acceptance_rate, termination) в Talent?
- Availability: кто SoT — Talent или room occupancy?
- Можно ли фрилансеру быть в N комнатах WowLance?

### 6.4. API Gateway / Platform

- Префикс маршрутов, CORS, лимиты upload?
- Кто валидирует JWT: только Gateway или ещё сервисы?
- Единый object storage / CDN для media?
- Observability: trace id end-to-end (кнопка Studio → комната)?

### 6.5. Внешние домены (CRM, Meet, Payment, Invoicing, Order)

- Какой CRM first? Webhook «lead created / stage changed»?
- Meet: один провайдер на платформу или выбор клиента?
- Payment: кто инициирует charge за запуск комнаты / слоты — Studio, WowLance, Billing?
- Order / Invoicing: нужен ли WowLance как consumer статусов оплаты для staffing?

---

## 7. Вопросы продакт-оунеру

1. **Граница продукта:** WowLance 2.0 — только «комната исполнения» или ещё marketplace UI (каталог) внутри?
2. **Sale + develop в одной комнате** или разные типы комнат / шаблоны с общим каркасом?
3. Что **обязательно в MVP 2.0**: sprints? SOP viewer? staffing? Quality Gate? CRM handoff?
4. При изменении стратегии в Studio **после** старта продаж: авто-обновление комнаты, ручной Accept, или запрет до конца спринта?
5. Документы SOP: редактирование в комнате разрешено или только read-only снимок?
6. Роль **менеджера платформы** и Hot-лиды: остаются внутри WowLance или сразу только CRM?
7. Фрилансер **видит** исходный Studio-проект или только комнату?
8. Develop-комната: те же роли (тимлид/исполнители) или другие (PM, eng)?
9. SLA / автозамены слотов — в scope 2.0 или phase 2?
10. Юр./данные: где хранится PII лидов — WowLance, CRM, оба?
11. Метрики директора («потратил / заработал»): считает WowLance, Billing, или Studio?
12. Нужен ли **обратный** поток: из комнаты дозаказать слоты / изменить пакет без возврата в Studio?
13. Demo/sandbox для стейкхолдеров: общий demo-realm или отдельный контур?
14. Срок «заморозки» текущего Django-демо vs старт 2.0 greenfield?

---

## 8. Предлагаемый порядок работ (независимо от выбора A/B/C)

```text
1. ADR-002: WowLance как сервис в платформе (границы, SoT, запрет чужих БД)
2. OpenSpec: FounderHandoff, TalentRosterSync, RoomCore (BP/SOP/Sprint/Task)
3. Keycloak client + local user shadow + Gateway route
4. FastAPI skeleton + PostgreSQL + React shell комнаты
5. Handoff Strategy → создание комнаты (по выбранной концепции данных)
6. Roster Talent → staffing (упрощённый)
7. Адаптеры: Meet, Payment (stub→live), CRM lead export
8. Перенос ценных доменов 1.0: RBAC, Quality Gate pattern, termination
9. Вывод Django monolith из продуктивного контура (оставить как reference/archive)
```

---

## 9. Риски (общие)

| Риск | Митигация |
|------|-----------|
| «Большой взрыв» rewrite без контрактов | Сначала OpenSpec handoff + room core |
| Двойной SoT стратегии | Явная политика версий (C) или запрет правок (A) |
| Keycloak без shadow User | Сломанные FK комнаты; всегда локальная тень |
| React UI раньше стабильного API | API + контрактные тесты первее полировки |
| Встроить CRM «на чуть-чуть» | Жёсткий запрет Deal-модели в ROOM без ADR |
| Matching по live Talent | Таймауты и пустой staffing; только локальный roster |

---

## 10. Рекомендация команды разработки (черновик)

1. Зафиксировать с PO концепцию **C (Hybrid Contract)** как целевую; для первого интеграционного вертикального среза допустим упрощённый **A** (снимок без merge UX).
2. **Не** выбирать B как default: комната исполнения не должна падать вместе со Studio.
3. Стратегию и SOP — **копировать версией**, не читать БД Strategy.
4. Навыки фрилансера — **подтягивать и кэшировать** в своей БД; Talent остаётся SoT верификации.
5. Универсальная комната — общий каркас; sale/develop — шаблоны процессов, не два монолита.
6. Максимум «сервисов вокруг» — через Gateway-адаптеры; ядро ROOM держит только исполнение (люди, спринты, задачи, снимки, членство).

Следующий шаг: разбор A/B/C на созвоне с PO + владельцами Strategy/Talent/Keycloak; выбор концепции → ADR-002 + первый OpenSpec.
