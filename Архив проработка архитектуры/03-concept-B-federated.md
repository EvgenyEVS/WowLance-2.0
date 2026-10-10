# Концепция B — Federated Live («ссылки и живые API»)

| Поле | Значение |
|------|----------|
| **Код** | B / Federated |
| **Обзор** | [01-overview.md](01-overview.md) |
| **Идея** | WowLance почти не копирует стратегию и навыки. В БД комнаты — **идентификаторы и исполнение** (члены, спринты, таски). Контент стратегии/SOP/skills читается **live** из Strategy и Talent. |
| **Статус рекомендации** | Не default; только при жёстком требовании единого SoT без дублей |

---

## 1. Суть

Кнопка «в WowLance» создаёт тонкую оболочку:

- `room_id`, `strategy_id`, `founder_sub`;
- членство, спринты, задачи, activity — локально;
- при открытии вкладки «Стратегия» / «SOP» React (через WowLance BFF) ходит в Strategy API;
- карточка фрилансера в staffing подмешивает skills/video из Talent API по `freelancer_sub`.

Обновление оффера в Studio **сразу** видно в комнате (с оговорками кэша). Отдельного merge UX нет — SoT всегда снаружи.

---

## 2. Потоки данных

```text
[Founder Studio] <---live GET strategy/SOP--- [WowLance API]
       |                                         |
       +--- handoff: only IDs -------------------+
[Talent] <---live GET profile/skills-------------+
[WowLance PG]: rooms, members, sprints, tasks, refs
[Keycloak] JWT everywhere
[Adapters] CRM / Meet / Payment
```

**Критично:** Circuit breaker, timeouts, stale-while-revalidate, degraded UI («стратегия временно недоступна»).

---

## 3. Что хранит WowLance локально

| Хранить | Не хранить (в чистом B) |
|---------|-------------------------|
| `strategy_id`, optional etag | Полный текст оффера / SOP body |
| `freelancer_sub` в membership | Полная копия skills/video (кроме короткого cache) |
| Sprints, tasks, reports, chat refs | Master-профиль Talent |
| Integration ids (crm_deal_id, meet_url) | Биллинг-ledger |
| Кэш TTL (опционально) | «Вечный» snapshot как SoT |

Практически почти все команды всё равно введут **короткий кэш** (30–300 с) — иначе UX комнаты развалится. Тогда B незаметно дрейфует к плохому гибриду без версий → лучше сразу C.

---

## 4. Связь с текущим проектом

Текущий код **заточен под локальные данные**:

- matching — SQL по `FreelancerProfile` в той же БД;
- Обзор комнаты — `input_data`, documents, unit economics локально;
- менеджер открывает lead/task без чужих сервисов;
- QA и демо сиды — self-contained.

Переход на B означает **вырезание** локального SoT стратегии и профилей и замену каждого read-path на HTTP. Это не «тонкий рефакторинг», а смена характера сервиса на **orchestration shell**.

Что можно сохранить:

- модель Task / Sprint / membership / RBAC;
- паттерн Quality Gate (файлы отчётов — local or object storage комнаты);
- адаптеры внешних CRM/Meet.

Что ломается сильнее всего:

- `get_ranked_candidates` → распределённый запрос + exclude members;
- офлайн-демо / seed без поднятых Strategy/Talent;
- гарантии «тимлид открыл SOP в 2 ночи».

---

## 5. Плюсы

- Нет рассинхрона контента: Studio всегда права.
- Меньше дублирования больших документов.
- Фаундер правит стратегию без «ритуала импорта».
- Talent остаётся единственным местом навыков (GDPR: проще удалить в одном сервисе — *если* кэш и логи тоже чистятся).

## 6. Минусы и риски

- **Доступность:** падение Strategy = слепая комната.
- **Latency:** каждая вкладка = N сетевых вызовов; нужен BFF aggregation.
- **Консистентность исполнения:** задача ссылается на «шаг BP #3», а Studio уже удалил шаг.
- **Аудит/споры:** «по какой инструкции работали вчера?» — без снимка не доказать.
- **Нагрузка** на Talent при каталоге/matching.
- Сложнее контрактные тесты и локальная разработка (много моков).
- Юр. риск: исполнитель действовал по версии, которой уже нет.

---

## 7. Ключевые переделки (специфика B)

1. Handoff = create room shell + refs only.  
2. BFF endpoints: `GET /rooms/{id}/strategy` proxy+cache.  
3. Matching service: Talent search API + local exclusions.  
4. Жёсткие SLA/timeouts и UX degraded modes.  
5. Запрет «тихих» полных копий в коде (lint/ADR).  
6. Audit log: сохранять хотя бы **hash/version** прочитанной стратегии при ключевых действиях (иначе B юридически слаб) — по сути мини-снимок → снова клон C.

---

## 8. Вопросы к смежникам (специфика B)

**Strategy**

- Public read API с пагинацией SOP? ETag / `If-None-Match`?
- Гарантии availability (SLO) для зависимого WowLance?
- Сохраняется ли history versions API (хотя бы get-by-version)?
- AuthZ: тимлид комнаты имеет право читать strategy founder’а?

**Talent**

- Search/filter API под staffing (level, channel, skills) с пагинацией?
- Rate limits? Bulk get by ids?
- Поля video: embed-ready URL всегда?

**Gateway**

- Таймауты proxy, retry policy, correlation id?
- Кэш на edge?

**Security**

- Не утекает ли стратегия founder A тимлиду проекта B через баг ACL?

---

## 9. Вопросы PO (специфика B)

1. Допустимо ли, что при недоступности Studio комната не показывает SOP?
2. Нужна ли **юридическая** фиксация версии инструкции на момент задачи?
3. Может ли Studio **удалить** шаг BP, на который уже есть открытые tasks?
4. Готовы ли платить сложностью платформы за «всегда свежие данные»?
5. Develop-комната с теми же live SOP — тот же SLO?

---

## 10. Когда выбирать B

- PO/юристы требуют: единственная копия стратегии, без дублей.
- Strategy и Talent дают высокий SLO и versioned GET.
- Комната — тонкий task tracker, не «пакет исполнения».
- Команда готова к distributed systems operational cost.

**Не выбирать B**, если:

- нужен аудит «что исполняли»;
- соседние сервисы ещё alpha;
- staffing/matching — ядро UX (как в 1.0).

---

## 11. DoD концепции B

- [ ] Handoff создаёт room с refs; payload без полного SOP body  
- [ ] Вкладки strategy/SOP работают только через Strategy API (+ cache)  
- [ ] Degraded UI при 5xx/timeout Strategy покрыт тестом/контрактом  
- [ ] Matching не читает чужую БД; только Talent API  
- [ ] На create/close task пишется `strategy_version` / content hash (минимум для аудита)  
- [ ] Chaos-тест: Studio down ≠ 500 на весь /rooms (частичный UI жив)

---

## 12. Вердикт

**B максимизирует «чистоту» SoT и максимизирует хрупкость.** Для WowLance как комнаты исполнения с людьми и SOP это обычно плохой default. Если PO настаивает на B — минимум включить versioned read + запись hash в audit (тогда честнее назвать это **C-light**).
