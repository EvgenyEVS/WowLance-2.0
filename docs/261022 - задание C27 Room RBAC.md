# Задание: C27 — Room RBAC lite

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c27-room-rbac` |
| **База** | актуальный `main` **после merge C25** |
| **Параллельность** | ⚠️ **осторожно с C29** (оба UI); ✅ с C26 · C28 |
| **Фаза** | C27 (роли в комнате на stubs) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [зоны до согласования](261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) · наследие 1.0 RBAC |
| **Параллель** | [C26](261022%20-%20задание%20C26%20Founder%20demo%20pack.md) · [C28](261022%20-%20задание%20C28%20QA%20C0-C25.md) · [C29](261022%20-%20задание%20C29%20Room%20UX%20polish.md) |

> Контракты draft. Stub only. Live Keycloak roles / Gateway **не** делать. Не ломать G1–G10 при `AUTH_DISABLED=true` (demo mode).

---

## 1. Зачем

Сейчас любой валидный актор может accept/reject/assign/terminate. Нужен тонкий срез **ролей комнаты** внутри WowLance: founder / teamlead / member — без боевого realm.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `room_members` (или roles на shadow + membership), `domain/rbac.py`, guards на мутациях | Live Keycloak groups / Gateway |
| UI: скрыть кнопки по роли | Ломать C26 demo (оставить bypass при AUTH_DISABLED **или** seed ролей в demo-скрипте) |
| | Менять граничные YAML соседей |

**Alembic:** `014_c27_*` (или следующий free). Dual с C29 маловероятен.

---

## 3. Не делать

- Полный Gateway / token exchange.  
- Привязка только к JWT realm roles без локальной membership (для C27 — **локальная** таблица членов комнаты).  
- Deep CRM / matching live.

---

## 4. Продуктовые правила

1. Роли: `founder` | `teamlead` | `member` (строки).  
2. При handoff create: `founder_sub` → роль `founder` в room.  
3. Assign на слот → upsert membership `member` (если ещё нет).  
4. Явный `POST …/members` или promote teamlead — **минимум один** способ назначить teamlead (тимлид stub: POST с actor founder).  
5. Матрица (зафиксируй в README):

| Действие | founder | teamlead | member |
|----------|---------|----------|--------|
| Accept/Reject strategy | ✅ | ✅ | ❌ |
| Assign/unassign/reassign/rematerialize/match | ✅ | ✅ | ❌ |
| Terminate | ✅ | ✅ | ❌ |
| Task create / accept/reject QG | ✅ | ✅ | ❌ create/accept; member: start/complete своих |
| Lead hot/handoff | ✅ | ✅ | ❌ |
| Chat post / meet ensure | ✅ | ✅ | ✅ |
| GET room/lists | ✅ | ✅ | ✅ |

6. При нарушении → **403** `forbidden_role`.  
7. `AUTH_DISABLED=true`: **рекомендация** — RBAC **выключен** (как сейчас), чтобы demo/pytest не ломались; `ROOM_RBAC_DISABLED` default true **или** при AUTH_DISABLED игнорировать роли. Зафиксируй одно; для строгих тестов — отдельный suite с RBAC on.

---

## 5. Контракт

`contracts/wowlance/RoomMembers.v1.yaml` (draft) + list/promote paths.  
Строка в `contracts/README.md` / REGISTRY если есть.

---

## 6. Код / тесты

- Таблица membership; guards в API мутаций.  
- pytest: teamlead OK assign; member 403 assign; AUTH_DISABLED path зелёный.  
- UI: скрыть Terminate/Accept у member.

---

## 7. DoD

- [ ] Membership + матрица + 403 + UI hide + pytest + README.  
- [ ] Demo/G1–G10 при default env живы.  
- [ ] Нет live Keycloak roles.  
- [ ] PR.

---

## 8. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c27-room-rbac
База: origin/main после C25.
Параллелен C26/C28; с C29 — не конфликтуй сильно в одних кнопках UI.
Задание: docs/261022 - задание C27 Room RBAC.md
Draft contracts; stub; no live Keycloak/Gateway; keep AUTH_DISABLED demo green.

Сделай room membership roles + 403 matrix + UI hide + pytest.
План 6–8 шагов, маленькие коммиты.
```
