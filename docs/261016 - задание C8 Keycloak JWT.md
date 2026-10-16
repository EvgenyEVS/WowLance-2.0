# Задание: C8 — Keycloak JWT + shadow User

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-16 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c8-keycloak-jwt` |
| **База** | актуальный `main` **после merge C6 + C7** |
| **Параллельность** | ✅ **можно делать параллельно с C9** (`feature/c9-hot-lead-crm`) |
| **Фаза** | C8 (OIDC JWT на клиентских API + локальный shadow User) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–4 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md), [05-integration-map](architecture/05-integration-map.md) §3.1 |
| **Предыдущее** | [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) · [C5 Strategy Accept](261015%20-%20задание%20C5%20Strategy%20accept.md) · [C6/C7](261015%20-%20задание%20C6%20Roster%20assign.md) |
| **Параллель** | [C9 Hot → CRM](261016%20-%20задание%20C9%20Hot%20lead%20CRM.md) |

Без C6/C7 в `main` не начинать: на защищаемых маршрутах уже есть rooms / slots / tasks / Accept.

---

## 1. Зачем

До C7 клиентские API открыты; роли и `X-Actor-Sub` — декоративные заголовки. По ADR вход людей идёт через **Keycloak**; в WowLance — **shadow-пользователь** с тем же `sub`.

Нужен первый auth-срез: проверка Bearer JWT (JWKS / demo-realm), upsert `User` по `sub`, защита `/api/v1/*`. Internal-контур соседей (handoff, entitlements, publications, roster upsert) остаётся открытым или с отдельным service stub — **не** смешивать с user JWT в этом тикете.

Полноценный RBAC (teamlead vs freelancer на каждый endpoint), Gateway, token exchange — **не** здесь (достаточно: «валидный JWT → есть `sub` → пускаем»).

---

## 2. Параллель с C9 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `app/auth/*`, middleware, зависимости FastAPI `CurrentUser` | Таблицы `leads` / Hot→CRM / outbox payload C9 |
| Login UI, хранение access token, `Authorization: Bearer` на fetch | Менять контракт `HotLeadToCrm` |
| Upsert в существующую `users` | Ломать domain leads |

**Alembic:** C8 может обойтись **без** новой таблицы (использовать `users`). Если нужны поля (`email`, `last_login_at`) — свой `007_c8_*` от текущего head `main` (`006_merge_c6_c7_heads`). Dual head с C9 → merge-миграция на QA.

**Merge:** C9 роутеры/панели оставить; auth middleware не должен отрезать internal CRM stub без согласования (internal paths — allowlist).

`X-Actor-Sub` на мутациях: после C8 **предпочтительно** брать `sub` из JWT; заголовок можно оставить как fallback только если `AUTH_DISABLED=true` (local/tests). Зафиксировать в README.

---

## 3. Не трогать / не делать

- Живой продакшен-Keycloak платформы; достаточно **локального** Keycloak в compose **или** mock JWKS + документированный способ выпустить тестовый JWT.  
- Полная матрица ролей / запрет Accept для freelancer.  
- Hot leads / CRM (C9).  
- Защита `/internal/v1/*` user-токеном (оставить open + комментарий «service token later»).  
- Переписывать C1–C7 бизнес-логику.  
- Копировать Django auth 1.0.

---

## 4. Продуктовые / технические правила

1. Клиентские маршруты `/api/v1/**` → **401** без Bearer / с невалидным JWT.  
2. Валидный JWT → найти или создать `User(sub=…, display_name?)` (shadow).  
3. `/health` — без auth.  
4. `/internal/v1/**` — без user JWT в C8.  
5. Режим разработки: env `AUTH_DISABLED=true` (default в тестах) → поведение как сейчас (удобный pytest без Keycloak).  
6. `AUTH_DISABLED=false` — строгий JWT; README: как поднять Keycloak / получить token.  
7. React: страница Login (OIDC code flow **или** «вставить access token» для MVP — допустим второй вариант, если OIDC UI не уложится в срок; в PR явно написать, что выбрано).  
8. После логина все `fetch` на `/api` несут `Authorization`. Старые вызовы с одним `X-Actor-Sub` без Bearer при `AUTH_DISABLED=false` → 401.

---

## 5. Контракт / конфиг (C0 шага)

Файл: `contracts/wowlance/AuthBearer.v1.yaml` (лёгкий):

```yaml
id: AuthBearer
version: "1"
direction: client -> WowLance
header: Authorization: Bearer <access_token>
claims_required: [sub]
optional_claims: [preferred_username, email, name]
shadow_user: upsert on first authenticated request
unauthenticated_api: 401
public: [/health]
internal_open_in_c8: [/internal/v1/*]
```

Env (`.env.example`):

```text
AUTH_DISABLED=true
KEYCLOAK_ISSUER=http://127.0.0.1:8080/realms/wowlance
KEYCLOAK_AUDIENCE=wowlance-api   # или отключить aud-check в demo
KEYCLOAK_JWKS_URL=...            # опционально, можно вывести из issuer
```

Строка в `contracts/README.md`. Обновить root / backend README: как включить auth.

---

## 6. Что сделать в коде

### 6.1. Backend

- Модуль `app/auth/` (verify JWT via JWKS, `get_current_user` dependency).  
- Подключить dependency на роутеры `/api/v1/*` (rooms, slots, roster GET, assign, strategy decide, tasks).  
- При первом запросе — upsert `User`.  
- Тесты:  
  1. `AUTH_DISABLED=true` — регресс C1–C7 зелёный.  
  2. `AUTH_DISABLED=false` + fake JWT / mock JWKS → 200 на GET room.  
  3. Без токена → 401.  
  4. Internal handoff без токена → всё ещё 200/201.

Библиотека: `PyJWT` + `cryptography` или `python-jose` — зафиксировать в `requirements.txt`.

### 6.2. Keycloak / demo

Минимум один из вариантов (описать в README):

**A (предпочтительно):** сервис `keycloak` в `docker-compose.yml` + realm export `devtools/keycloak/wowlance-realm.json` (user `demo` / пароль в README).  
**B:** скрипт выдачи RS256 test JWT + JWKS stub endpoint в FastAPI только при `AUTH_DISABLED=false` и `AUTH_STUB_JWKS=true` (явно «не для prod»).

### 6.3. Frontend

- Login / «Set token» → сохранить token (memory + `sessionStorage`).  
- Общий `apiFetch` с Bearer.  
- Если 401 — показать «нужен login».  
- При `AUTH_DISABLED` на бэке UI может слать запросы без токена (как сейчас) — ок для локального демо без Keycloak.

### 6.4. Документация

`backend/README.md` — секция C8.  
`frontend/README.md` — login / token.  
Не раздувать ADR.

---

## 7. DoD

- [ ] Ветка **`feature/c8-keycloak-jwt`** от `main` с C6+C7.  
- [ ] Контракт AuthBearer + `.env.example`.  
- [ ] `/api/v1/*` защищены при `AUTH_DISABLED=false`; `/internal` и `/health` — нет.  
- [ ] Shadow upsert `User` по `sub`.  
- [ ] React передаёт Bearer (или документированный stub-flow).  
- [ ] pytest: disabled-режим = полный регресс; enabled-режим = 401/200 кейсы.  
- [ ] Не реализует Hot leads (C9).  
- [ ] PR: «как получить token за 2 минуты».

---

## 8. Вне скоупа / параллель

- HotLead / CRM (C9)  
- Полный RBAC, Gateway, service token на internal  
- Quality Gate  

**Параллельно:** [C9 — Hot lead CRM](261016%20-%20задание%20C9%20Hot%20lead%20CRM.md).

---

## 9. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c8-keycloak-jwt
База: origin/main ПОСЛЕ merge C6 + C7.
Этот тикет ПАРАЛЛЕЛЕН C9 (feature/c9-hot-lead-crm): не создавай leads/CRM/outbox для Hot.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261016 - задание C8 Keycloak JWT.md

Сделай C8:
1) contracts/wowlance/AuthBearer.v1.yaml + .env.example (AUTH_DISABLED, KEYCLOAK_*)
2) app/auth: JWT verify (JWKS), get_current_user, shadow upsert User
3) Require auth on /api/v1/* when AUTH_DISABLED=false; /health and /internal/v1/* stay open
4) AUTH_DISABLED=true (default for pytest) — полный регресс C1–C7 зелёный
5) Тесты 401 без токена / 200 с валидным stub JWT при enabled
6) React: login или paste-token + Bearer на api fetch
7) README: как поднять demo Keycloak ИЛИ stub JWKS и получить token

Не делай Hot leads, полный RBAC, защиту internal user-JWT, live platform Keycloak.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 10. Ревьюеру

- Internal не сломан.  
- Тесты по умолчанию без Keycloak.  
- Нет «секретного» hardcode prod realm.  
- Параллель с C9: allowlist `/internal`, нет правок leads.  
- Dual Alembic head с C9 — только если C8 добавлял миграцию.
