# Задание: C21 — Internal service-token stub

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-19 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c21-internal-service-token` |
| **База** | актуальный `main` **после merge C15** (нужен C8 auth каркас) |
| **Параллельность** | ✅ **можно параллельно с C16 · C17 · C18 · C19 · C20** (осторожно с чужими `/internal` тестами) |
| **Фаза** | C21 (защита `/internal/v1/*` сервисным секретом) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../../../AGENTS.md), [C8](261016%20-%20задание%20C8%20Keycloak%20JWT.md) |
| **Предыдущее** | [C8 Keycloak JWT](261016%20-%20задание%20C8%20Keycloak%20JWT.md) |
| **Параллель** | [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) · [C18](261019%20-%20задание%20C18%20StaffingUnlocked%20outbox.md) · [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C20](261019%20-%20задание%20C20%20Room%20chat.md) |

C8 оставил `/internal/v1/*` открытым («service token later»). C21 закрывает этот долг **stub-секретом**, без token exchange / Gateway.

---

## 1. Зачем

Handoff, entitlement, roster upsert, strategy publish, health publish, CRM stubs — всё на `/internal` без проверки. Для демо платформы нужен минимум: **общий service secret** на internal.

Нужен срез: при `INTERNAL_AUTH_DISABLED=false` internal требует заголовок; user `/api/v1` JWT (C8) **не** менять. Полный client-credentials Keycloak — **не** здесь.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `app/auth/*` или middleware только для `/internal/v1` | Менять user JWT guard C8 / login UI |
| Env: `INTERNAL_AUTH_DISABLED`, `INTERNAL_SERVICE_TOKEN` | Логика earnings/terminate/chat/leads/entitlement **бизнес** |
| Обновить conftest / README curl с заголовком | Ломать AUTH_DISABLED для `/api/v1` |

**Стык с C18/C19:** их новые internal endpoints должны автоматически попасть под тот же guard (prefix-based).  
**Стык с тестами:** все `POST /internal/...` в suite — либо default `INTERNAL_AUTH_DISABLED=true` в conftest (как AUTH_DISABLED), либо передавать заголовок.

**Alembic:** нет.

---

## 3. Не трогать / не делать

- Keycloak client-credentials / token exchange.  
- API Gateway.  
- Защита `/api/v1` повторно (уже C8).  
- Защита `/health` (оставить open).  
- User JWT на internal (service secret ≠ user Bearer).

---

## 4. Продуктовые правила

1. Env (имена можно уточнить в README):  
   - `INTERNAL_AUTH_DISABLED` default **`true`** (локалка/pytest как сейчас).  
   - `INTERNAL_SERVICE_TOKEN` — непустая строка секрета (для строгого режима).  
2. Когда `INTERNAL_AUTH_DISABLED=false`:  
   - запросы к `/internal/v1/*` без валидного секрета → **401**;  
   - валидный секрет → как раньше.  
3. Способ передачи (**зафиксируй одно**):  
   - **рекомендация:** `X-Service-Token: <secret>`  
   - альтернатива: `Authorization: Bearer <secret>` только на internal (не путать с user JWT на `/api/v1`).  
4. `/health`, `/docs`, `/auth/*`, `/api/v1/*` — без этого требования.  
5. Неверный токен → 401 (не 403).  
6. Пустой `INTERNAL_SERVICE_TOKEN` при `INTERNAL_AUTH_DISABLED=false` → старт приложения **fail-fast** или все internal 503 — **рекомендация: fail-fast при startup**.

---

## 5. Контракт

Дописать `contracts/keycloak/AuthBearer.v1.yaml` **или** новый `InternalServiceAuth.v1.yaml`:

```yaml
id: InternalServiceAuth
version: "1"
applies_to: /internal/v1/*
header: X-Service-Token
when: INTERNAL_AUTH_DISABLED=false
errors: [401]
```

Строка в `contracts/README.md`.

---

## 6. Код

### 6.1. Middleware / dependency

Один guard на prefix `/internal/v1` в `main.py` или dependency на internal routers.

### 6.2. Tests

1. Default disabled → handoff без заголовка OK (регресс C1).  
2. Strict: без токена → 401; с токеном → 200.  
3. `/api/v1` и `/health` не требуют service token.  
4. Неверный токен → 401.  
5. Точечный тест + правка conftest (force disabled в pytest **или** header fixture).

### 6.3. Frontend

Не обязателен (UI не ходит в internal). Обновить только README curl для handoff/entitlement.

### 6.4. Docs

`backend/README.md` — C21 таблица env + пример curl с `X-Service-Token`.  
`.env.example` — новые ключи.

---

## 7. DoD

- [ ] Ветка `feature/c21-internal-service-token`.  
- [ ] Guard + env + контракт + pytest + README + `.env.example`.  
- [ ] Default open для локалки; строгий режим документирован.  
- [ ] Не ломает C8 user JWT.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c21-internal-service-token
База: origin/main после C15 (C8 auth есть).
Параллелен C16–C20: не меняй earnings/terminate/chat/leads/entitlement бизнес-логику; только internal auth guard.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261019 - задание C21 Internal service token.md

Сделай C21: INTERNAL_AUTH_DISABLED + INTERNAL_SERVICE_TOKEN; X-Service-Token на /internal/v1; pytest; README; .env.example.
Не делай Keycloak client-credentials, Gateway, защиту /health.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Default disabled = зелёный suite без массовых правок.  
- C18/C19 internal paths покрываются prefix-guard.  
- Не смешивать service secret с user Bearer на `/api/v1`.
