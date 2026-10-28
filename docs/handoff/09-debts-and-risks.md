# Известные долги и риски

Опора: [технический аудит 261026](../status/261026%20-%20технический%20аудит%20и%20обоснование%20рефакторинга.md).

---

## P0 (не отдавать «как прод» без этого)

| Долг | Риск |
|------|------|
| `AUTH_DISABLED=true` / `INTERNAL_AUTH_DISABLED=true` по умолчанию | Открытые API на стенде |
| Outbox статус `sent` без реального брокера/webhook worker | Соседи «не получают» события в бою |
| Нет CI (GitHub Actions) | Регрессии при merge |
| Read-эндпоинты / ACL | Утечка данных комнаты при строгом auth |

## P1

| Долг | Комментарий |
|------|-------------|
| UI parity с 1.0 | C42: 2.0 chrome ещё далёк |
| Полный RBAC ролей платформы | Сейчас lite + флаги |
| Enrich Talent (ProfileChanged, rating) | Только тонкий upsert |
| Example для CrmDealStatus | Добавить при пинге CRM |

## P2 / продукт

- Live Gateway, Keycloak realm  
- Object storage SOP end-to-end  
- WebSocket chat (сейчас poll)  

---

## Риски передачи

1. Новая команда начнёт rewrite — **не нужно** (аудит).  
2. Перепутают 1.0 Django и 2.0 FastAPI.  
3. Начнут live без `agreed` → двойная переделка контрактов.  
4. Сломают пути к `contracts/*/examples` в тестах при реоргане.

---

## Принцип

Инкрементальный рефакторинг слоями. Ядро handoff / entitlement / snapshot / slots **не сносить**.
