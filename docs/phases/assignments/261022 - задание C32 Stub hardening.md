# Задание: C32 — Stub hardening (идемпотентность · 4xx · логи)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c32-stub-hardening` |
| **База** | актуальный `main` **после merge C26–C29** |
| **Параллельность** | ✅ с C30 · C31 · C33; ⚠️ не большой UI-рефактор; осторожно с общими `deps` / error handlers |
| **Фаза** | C32 (зона «Hardening stub» — владение WL) |
| **Стек** | **FastAPI · PostgreSQL · pytest · OpenSpec (без смены границы)** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [зоны до согласования](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| **Параллель** | [C30](261022%20-%20задание%20C30%20Tasks%20QG%20UX.md) · [C31](261022%20-%20задание%20C31%20Slots%20staffing%20UX.md) · [C33](261022%20-%20задание%20C33%20Contract%20owners.md) |

> Hardening **stubs**, не live. Gateway / боевой Keycloak / брокер outbox — **не** делать. Не ломать G1–G10.

---

## 1. Зачем

Stub-MVP демо-готов, но повторные вызовы и «кривые» 4xx ещё местами шумные. Нужен срез **надёжности stub-контура**: идемпотентность ключевых POST, единый shape ошибок, полезные логи — без подключения соседей.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `backend/app/**` error helpers, logging, idempotency на internal POST | Live broker / webhook worker «доставить outbox» |
| pytest на повтор handoff / entitlement / crm deal | Ломать UI C30/C31 ради красоты |
| Документ `docs/hardening-stub.md` (короткий) | Breaking change граничных YAML |

**Alembic:** только если нужна таблица/уникальный индекс под idempotency key — `015_c32_*` (или следующий free). Dual с C30 маловероятен; при dual — merge migration.

---

## 3. Не делать

- Outbox → Kafka/Rabbit/HTTP retry к Strategy (это live).  
- Полный Gateway / multi-realm auth.  
- Смена имён событий (`PaymentSucceeded` и т.п.) без маппинга.  
- Deep CRM / billing.

---

## 4. Продуктовые правила (must-fix)

1. **Идемпотентность (аудит + добить дыры):**  
   - повтор `POST handoff` с тем же `handoff_id` → тот же `room_id` (уже есть — закрепи тестом).  
   - повтор entitlement / CRM deal-status inbound — без дублей побочек (тест).  
   - где дыра очевидна на мутациях комнаты (create lead/task) — **минимум** понятный 409, не 500.  
2. **Единый 4xx JSON** (минимум для новых/тронутых путей):  
   `{ "detail": { "code": "...", "message": "..." } }` или уже принятый в проекте shape — **не плодить третий**. Зафиксируй в `docs/hardening-stub.md`.  
   Коды: `forbidden_role`, `not_found`, `conflict`, `validation_error` (и существующие).  
3. **Логи:** на internal stub входах (handoff, entitlement, strategy-published, crm deal) — structured log: `event`, `room_id`/`handoff_id`, `outcome` (без PII dump).  
4. **Health:** `GET /health` (или существующий) остаётся зелёным; не ломать pytest auth fixtures.  
5. **Demo:** `AUTH_DISABLED` + founder-demo.ps1 путь жив.

---

## 5. Nice-to-have

- Request-id header echo (`X-Request-Id`).  
- Таблица/сводка «какой POST идемпотентен» в docs.

---

## 6. DoD

- [ ] Must-fix 1–5 + короткий `docs/hardening-stub.md`.  
- [ ] pytest: повтор handoff/entitlement/(crm) + хотя бы один conflict/validation shape.  
- [ ] Нет live broker / Gateway.  
- [ ] PR.

---

## 7. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c32-stub-hardening
База: origin/main после C26–C29.
Параллелен C30/C31/C33: не рефакторь UI панелей; не меняй граничные YAML.
Задание: docs/261022 - задание C32 Stub hardening.md
Stub only; no live outbox delivery / Gateway; keep G1–G10.

Сделай: idempotency audit+tests, unified 4xx shape, structured logs on internal stubs, docs/hardening-stub.md.
План 6–8 шагов, маленькие коммиты.
```
