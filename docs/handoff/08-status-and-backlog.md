# Текущий статус и бэклог

Снимки для стейкхолдеров: [status/](../status/).  
Аудит кода: [261026 — технический аудит](../status/261026%20-%20технический%20аудит%20и%20обоснование%20рефакторинга.md).

---

## Готовность (ориентир 2026-10-28)

| Контур | Оценка |
|--------|--------|
| Demo / stub-MVP комнаты | **~93–95%** |
| Контракты к согласованию | **~85%** (нет `agreed`) |
| Live с соседями | **~15–25%** |
| Боевой прод | **~40%** |

Фазы в коде: **C0–C42** (вертикальные срезы + UX polish + UI parity/visual QA).  
Live adapters / Gateway — **после `agreed`**.

---

## Что уже есть (кратко)

- Полный stub-контур комнаты + outbox  
- Founder-demo script  
- RBAC lite, auth/JWT stub, internal token stub  
- Контракты по сервисам + REGISTRY  
- Утверждённая схема платформы (Miro / PNG)  
- Pytest на PostgreSQL, серия QA-отчётов  
- UI polish C29–C41; visual QA C42 — 2.0 ещё далёк от chrome 1.0  

---

## Бэклог для принимающей команды

### Сразу (без соседей)

1. Поддержать зелёный pytest + demo.  
2. Закрыть P0 из аудита: дефолты auth в non-local, CI, ACL на read где нужно.  
3. UI parity с 1.0 — по приоритету продукта (см. ui-parity + C42).  
4. Заполнить **owners** в contracts-owners (имена, каналы).

### Со смежниками

1. Разослать пакеты `contracts/<svc>/` → `proposed`.  
2. Получить `agreed` (порядок: Keycloak → US Closer → Order → Talent → CRM).  
3. Live adapters за feature-flag (stub не удалять).

### Не делать раньше времени

- Rewrite всего приложения  
- Deep CRM / deals в комнате  
- Signup в WowLance  
- Live без `agreed`

---

## Таблица фаз (навигация)

Полная таблица C0–C33+ — в [корневом README](../../README.md).  
Задания: [phases/assignments/](../phases/assignments/).  
QA-отчёты: [phases/qa/](../phases/qa/).

| Блок | Фазы | Смысл |
|------|------|--------|
| Ядро комнаты | C0–C13 | Handoff…health |
| Расширение stubs | C14–C25 | Meet, earnings, chat, matching… |
| Demo / RBAC / UX | C26–C36 | Demo pack, polish панелей |
| QA волны | C28, C37, C38 | Полные прогоны |
| UI parity | C39–C42 | Tokens, chrome, panels, visual QA |
| Live | после `agreed` | Адаптеры + Gateway |
