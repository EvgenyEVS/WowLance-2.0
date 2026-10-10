# Концепция C — Hybrid Contract Room («снимок + контракт обновлений»)

| Поле | Значение |
|------|----------|
| **Код** | C / Hybrid Contract |
| **Обзор** | [01-overview.md](01-overview.md) |
| **Идея** | При входе — **версионированный снимок** стратегии/SOP (как A). Strategy остаётся SoT редактирования. Обновления приходят **событиями**; комната принимает их явно или по политике. Фрилансеры — локальный roster + sync из Talent. |
| **Рекомендация** | ★ Целевая архитектура WowLance 2.0 |

---

## 1. Суть

Универсальная комната — **исполнительный контур** с собственной PostgreSQL:

- люди (shadow users + membership);
- процессы (BP), SOP (версии), спринты, задачи, отчёты;
- снимок стратегии, с которой работают;
- ссылки на внешние CRM / Meet / Payment / Order.

Strategy / Talent **не открывают** свои таблицы. Связь:

1. **Handoff** → snapshot vN в WowLance.  
2. **Events** `StrategyPublished` / `FreelancerProfileChanged` → inbox обновлений.  
3. **Политика применения:** auto-minor / manual Accept / freeze до конца спринта (настраивается PO).  
4. **Обратные события** из комнаты: `RoomStarted`, `ReportAccepted`, `MemberTerminated`, `LeadHandedToCrm` — чтобы Studio/Talent/CRM обновляли свои метрики.

Это прямое развитие идей ADR-001 (`handle_project_paid` как единая точка, снапшот `functional_roles`) в мире микросервисов.

---

## 2. Потоки данных

```text
Founder Studio                    WowLance ROOM                      Talent
     |                                 |                                |
     |-- FounderHandoff (vN) --------->| snapshot + create room         |
     |                                 |<-- FreelancerVerified ---------|
     |                                 | roster upsert                  |
     |-- StrategyPublished (vN+1) ---->| update inbox / apply policy    |
     |                                 |-- ReportAccepted ------------->| (rating feed)
     |<-- RoomStarted / KPI hooks -----|                                |
     |                                 |-- LeadExport ------------------> CRM
     |                                 |-- MeetSessionCreate ----------> Meet
     |                                 |-- Charge/Entitlement ---------> Billing
 Keycloak: sub на всех границах
 Gateway: JWT + routing
```

---

## 3. Политика данных: что копируем, что ссылаем

| Артефакт | В snapshot handoff | Live | События |
|----------|-------------------|------|---------|
| Offer / ICP / hot criteria | Да (JSON) | Нет как SoT | `StrategyPublished` |
| SOP / BP docs | Да: metadata + storage keys; опционально pin version | Preview «что нового» из Strategy API | то же |
| Staffing package / roles | Да | — | `PackageChanged`? |
| Freelancer skills / video / level | Да в roster | GET для «обновить карточку» по кнопке | `ProfileChanged`, `Suspended` |
| Task / sprint / reports | Только WowLance | — | исходящие |
| Lead PII | Thin local **или** сразу CRM | — | CRM webhooks |
| Payment status | entitlement id | Billing API | `PaymentSucceeded` |

**Ответ на вопрос «копировать или брать из предыдущей БД»:**  
копируем **версию** в свою БД; «берём» обновления только через **API/события**, никогда через чужой SQL. Документы — общие object keys с pinned version/checksum, не shared mutable blob без версии.

---

## 4. Универсальная комната (sale + develop)

Общий каркас:

```text
Room
 ├── type: sale | develop | …
 ├── strategy_snapshot (versioned)
 ├── business_processes[]
 ├── sop_documents[] (pinned versions)
 ├── sprints[]
 ├── tasks[] (+ optional Quality Gate)
 ├── members[] (roles in room)
 └── integrations[] (crm, meet, billing refs)
```

Шаблоны отличаются набором процессов и дефолтными интеграциями:

| | Sale-шаблон | Develop-шаблон |
|--|-------------|----------------|
| BP | воронка outreach / discovery | delivery / iteration |
| Tasks | звонки, отчёты со скрином | tickets, PR DoD |
| External | CRM, dialer?, Meet | repo?, Meet, Order |
| Staffing | sellers levels/channels | eng/design roles (из Talent schema) |

Не плодить два микросервиса «SaleRoom» и «DevRoom» на старте — один ROOM с template packs.

---

## 5. Эволюция сущностей 1.0 → 2.0

| 1.0 | 2.0 (C) |
|-----|---------|
| `Project` + wizard `input_data` | `Room` + `StrategySnapshot` from handoff |
| `RoomFunctionSlot` / matching | Сохраняем идею слотов; кандидаты из local roster |
| `Task` / `Report` / Quality Gate | Базовый execution engine; Gate — policy по типу задачи |
| `Lead` Cold/Warm/Hot | Sale plugin: local thin lead **или** CRM entity id |
| `MANAGER_HANDOFF` inbox | Adapter → CRM + deeplink; inbox как fallback MVP |
| `RoomDocument` | SOP pin + operational uploads |
| `FreelancerProfile` | `FreelancerRosterEntry` (shadow + skills snapshot) |
| `User` password | Keycloak; local shadow by `sub` |
| Django templates | React app |
| Stub pay | Billing events + entitlement before staffing |

---

## 6. Ключевые переделки (полный список)

### Платформа

1. ADR-002: границы WowLance, запрет чужих БД, SoT матрица.  
2. OpenSpec: `FounderHandoff`, `StrategyPublished`, `TalentRoster*`, `RoomOutbound*`.  
3. Keycloak client `wowlance-room` + shadow User.  
4. FastAPI bounded contexts: `identity_shadow`, `handoff`, `room_core`, `staffing`, `integrations`.  
5. React: room shell (BP, SOP, sprints, tasks, team).  
6. PostgreSQL schema; outbox для исходящих событий.  
7. Gateway routes + service tokens к Strategy/Talent/CRM.

### Продукт

8. Убрать wizard как SoT; оставить только admin/demo handoff emulator.  
9. Versioned snapshot storage + UI badge «стратегия vN».  
10. Update inbox: diff / Accept / Dismiss / Defer to sprint end.  
11. Template packs sale & develop.  
12. Staffing на roster; invite/confirm сохранить смыслы 1.0.  
13. Integrations SDK: Meet, CRM, Payment (stub implementations first).  
14. Перенос RBAC и termination как доменных модулей.  
15. Метрики директора: потреблять Billing + CRM, не выдумывать Deal внутри.

### Вывод 1.0

16. Django monolith → archive / reference; критичные тесты домена портировать как pytest против FastAPI.  
17. Demo: Keycloak demo realm + seed handoff + seed roster.

---

## 7. Плюсы

- Комната работает при падении Studio (как A).  
- SoT редактирования стратегии остаётся у фаундера.  
- Аудит: всегда ясно, какая `strategy_version` действовала.  
- Контролируемое обновление (нет «плывущего» BP под ногами исполнителей).  
- Roster локален → matching предсказуем (урок 1.0).  
- Естественный путь: начать с A-механики handoff, добавить events → полный C.  
- Внешние CRM/Meet/Payment не запрещены — наоборот, заложены.

## 8. Минусы и риски

- Нужны event bus / outbox и дисциплины версий.  
- UX «Accept обновления стратегии» надо спроектировать (иначе копится inbox).  
- Сложнее, чем чистый A; нужна платформенная поддержка (Superpowers/OpenSpec).  
- Конфликты merge: структурный BP vs уже созданные tasks.  
- Две команды должны держать совместимость schema v1/v2.

---

## 9. Вопросы к смежникам (специфика C)

**Strategy**

- Семантика версий: semver? monotonic int? content hash?  
- Событие `StrategyPublished`: полный snapshot или patch/diff?  
- Можно ли запросить `GET /strategies/{id}/versions/{n}` для re-hydrate?  
- Политика: какие поля `breaking` (требуют Accept) vs `cosmetic`?  
- Handoff обязателен до первого события update?

**Talent**

- Гарантия at-least-once + `event_id` для идемпотентного upsert roster?  
- Какие поля WowLance **имеет право** писать обратно (rating, acceptance, badges)?  
- Suspend/ban: SLA доставки в WowLance (минуты)?  
- Skills taxonomy общая (код навыка) или free-text?

**Billing**

- Entitlement `room.staffing_enabled` до или после handoff?  
- Событие для дозаказа слотов из комнаты?

**CRM**

- Идемпотентный create lead/deal с `wowlance_lead_id`?  
- Обратный webhook статусов сделки → метрика «заработал»?

**Platform**

- Стандарт outbox / Kafka / NATS / HTTP webhooks — что принято в инфраструктуре?  
- OpenSpec репозиторий: общий monorepo contracts?

**Keycloak**

- Маппинг ролей платформы vs ролей **в комнате** (не путать)?  
- Группы vs realm roles для freelancer verified flag (лучше Talent event, не только KC group)?

---

## 10. Вопросы PO (специфика C)

1. Default policy обновлений: auto / accept / freeze-on-active-sprint?  
2. Кто жмёт Accept: только директор или тимлид тоже?  
3. Breaking change BP при открытых tasks — блокировать publish в Studio или решать в комнате?  
4. Sale и develop — одна кнопка «в WowLance» с выбором типа или две кнопки в Studio?  
5. Нужен ли каталог внутри WowLance или «назначение только из Talent shortlist»?  
6. Hot-лиды: обязательный CRM с day-1 или inbox-fallback на 1–2 спринта?  
7. Может ли комната **редактировать** копию SOP (fork) с пометкой «отклонение от Studio vN»?  
8. KPI директора: какой сервис показывает «заработал»?  
9. Migrate существующих демо-комнат 1.0 или только greenfield?  
10. Критерий успеха MVP 2.0 одной фразой (для отсечения scope)?

---

## 11. Поэтапное внедрение C

| Фаза | Содержание | ≈ опора |
|------|------------|---------|
| **C0** | Контракты OpenSpec + ADR-002 | Документы |
| **C1** | Handoff = A (immutable snapshot), без update inbox | Вертикальный срез |
| **C2** | Keycloak + React room shell + tasks/sprints | Ядро |
| **C3** | Talent roster sync + staffing | Люди |
| **C4** | StrategyPublished + Accept UI | Полный гибрид |
| **C5** | CRM / Meet / Payment adapters live | Внешний контур |
| **C6** | Develop template pack | Универсальность |
| **C7** | Archive Django 1.0 | Чистка |

Так PO видит ценность уже на C1–C2, не дожидаясь идеальной шины.

---

## 12. DoD концепции C (целевое)

- [ ] Матрица SoT согласована (Strategy / Talent / Room / Billing / CRM)  
- [ ] Handoff идемпотентен; snapshot version виден в UI  
- [ ] Комната открывается при недоступности Studio (документы из своего storage/DB)  
- [ ] `StrategyPublished` создаёт inbox item; Accept обновляет pin version  
- [ ] Roster идемпотентен; matching без live JOIN Talent DB  
- [ ] Outbound события комнаты документированы и принимаются хотя бы одним consumer  
- [ ] Хотя бы один live adapter (Meet **или** CRM) + stubs остальных  
- [ ] Sale и develop создаются из одного room core с разными packs  

---

## 13. Сравнение с A и B (для выбора на созвоне)

| Критерий | A | B | C |
|----------|---|---|---|
| Автономность комнаты | +++ | + | +++ |
| Свежесть стратегии | + | +++ | ++ |
| Аудит версии | ++ | + (если hash) | +++ |
| Сложность платформы | ++ | +++ | +++ |
| Скорость первого среза | +++ | + | ++ (через C1=A) |
| Соответствие «внешние CRM/Meet» | +++ | +++ | +++ |
| Matching как в 1.0 | +++ | + | +++ |

---

## 14. Вердикт

**C — целевая модель.** Стратегию и документацию **не читаем из чужой БД**; **копируем версию** и обновляем по контракту. Навыки фрилансеров **подтягиваем и храним у себя**, Talent — SoT верификации и мастер-профиля. Универсальная комната держит исполнение; остальное — адаптеры. Практичный план: запустить как A (C1), нарастить события и Accept до полного C.
