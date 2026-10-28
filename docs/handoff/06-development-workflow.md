# Процесс разработки

См. также [AGENTS.md](../../AGENTS.md).

---

## Обязательный цикл

1. **Контракт раньше кода** — YAML (+ example) в `contracts/<svc>/`, строка в REGISTRY.  
2. Реализация: domain → API → (UI) → pytest.  
3. Stub-адаптеры до live.  
4. Маленький PR в `feature/cNN-…` → review → merge в `main`.  
5. Задание среза — шаблон в `docs/phases/assignments/`.

---

## Ветки

- `main` — канон.  
- `feature/c42-ui-visual-qa` и подобные — срезы.  
- Не коммитить секреты; `.env` в gitignore.

---

## Правила качества

- Идемпотентность на handoff / entitlement / Hot (см. hardening).  
- Понятные `detail` в 4xx.  
- Не читать чужие БД.  
- Не размывать ADR (нет signup, нет deals-in-room).  
- После смены контрактов — обновить `domain/schemas.py` и тесты.

---

## Параллельная работа

Исторически срезы шли парами (C8∥C9, C10∥C11…).  
Осторожно с пересечением `staffing.py`, миграциями Alembic (нужны merge-heads при параллели).
