# Задание: C33 — Владельцы контрактов (подготовка к `agreed`)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c33-contract-owners` |
| **База** | актуальный `main` **после merge C26–C29** |
| **Параллельность** | ✅ **полностью** с C30 · C31 · C32 (почти только docs) |
| **Фаза** | C33 (зона «подготовка к live» из бэклога зон — **не код live**) |
| **Стек** | **Markdown · `contracts/REGISTRY.md` · OpenSpec (без breaking)** |
| **Исполнитель** | тимлид / сильный стажёр + ИИ (документация) |
| **Срок** | 1–2 дня |
| **Канон** | [зоны до согласования](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) §5 · [REGISTRY](../../../contracts/REGISTRY.md) |
| **Параллель** | [C30](261022%20-%20задание%20C30%20Tasks%20QG%20UX.md) · [C31](261022%20-%20задание%20C31%20Slots%20staffing%20UX.md) · [C32](261022%20-%20задание%20C32%20Stub%20hardening.md) |

> Это **не** live adapters. Цель — таблица владельцев и процесс `proposed → agreed`, чтобы соседи могли подписать YAML. Код комнаты не обязателен.

---

## 1. Зачем

Комната на stubs готова к демо (C26–C29). Блокер платформы — никто не «владеет» согласованием границы. Нужен **пакет для пинга соседей**: кто, какой YAML, какой статус, что просим подписать.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `docs/guides/contracts-owners.md`, правки `REGISTRY.md` (колонка owner / notes) | Live HTTP к Strategy/CRM/Order |
| Шаблон письма/issue «просьба agreed» | Breaking change полей YAML «заодно» |
| Статус `proposed` в заметках (текст) | Менять API/миграции «под будущее» |

---

## 3. Не делать

- Реализация live adapter.  
- Переименование событий без маппинга в REGISTRY.  
- Deep CRM / Gateway / Keycloak realm.  
- Большой рефактор `contracts/**` структуры.

---

## 4. Продуктовые правила (must-fix)

1. Файл **`docs/guides/contracts-owners.md`** с таблицей:

| Сосед | Контракты (файлы) | Владелец (имя/команда, TBD OK) | Канал пинга | Статус | Блокер для WL |
|-------|-------------------|--------------------------------|-------------|--------|---------------|
| Strategy | FounderHandoff, StrategyPublished, RoomCreated, RoomHealth | … | Slack/issue | draft/aligned | live handoff |
| Order | EntitlementGranted, StaffingUnlocked | … | … | … | live unlock |
| Talent | TalentRosterUpsert, MemberTerminated, TaskAccepted | … | … | … | live roster |
| CRM | HotLeadToCrm, CrmDealStatus | … | … | … | live hot |
| Keycloak / platform | JWT, service-token | … | … | … | Gateway |

2. Для каждой строки: **одна** ссылка на YAML + что просим (`agreed` на v1 stub as-is **или** список открытых вопросов ≤5).  
3. В **`contracts/REGISTRY.md`**: короткая секция «Owners / proposed» или колонка Owner (TBD допустим).  
4. Шаблон пинга (10–15 строк): «вот REGISTRY + ваш каталог `contracts/<svc>/`, просим review → `agreed`».  
5. Явно: **пока нет `agreed` — WL продолжает stubs** (цитата из зон).

---

## 5. Nice-to-have

- Чеклист «что сосед должен прогнать против нашего stub».  
- Список «не согласовываем сейчас» (Jira, deep CRM) со ссылкой на зоны §3.

---

## 6. DoD

- [ ] `docs/guides/contracts-owners.md` заполнен (TBD по людям OK, контракты — полные).  
- [ ] REGISTRY обновлён ссылкой на owners.  
- [ ] Шаблон пинга в том же файле или `docs/contracts-ping-template.md`.  
- [ ] Нет изменений live/backend (кроме опечаток в contracts README — по желанию).  
- [ ] PR.

---

## 7. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c33-contract-owners
База: origin/main после C26–C29.
Параллелен C30–C32: почти только docs; не пиши live adapters.
Задание: docs/261022 - задание C33 Contract owners.md
Канон: docs/261022 - зоны разработки до согласования контрактов.md §5.

Сделай: docs/guides/contracts-owners.md + ping template + ссылка/секция в REGISTRY.md.
План 3–5 шагов, маленькие коммиты.
```
