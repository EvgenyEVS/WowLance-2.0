# Тесты и QA

---

## Автотесты

```powershell
cd backend
.\.venv\Scripts\pytest -q
```

- Реальная PostgreSQL `wowlance_test` (не SQLite).  
- Ориентир: **200+** passed (срез C38 / аудит: 206).  
- Фикстуры берут examples из `contracts/**/examples/` (после раскладки по сервисам — пути `strategy/examples/...`).

Задание pytest-окружения: [phases/assignments/…pytest…](../phases/assignments/261018%20-%20задание%20pytest%20wowlance_test.md).

---

## Ручной / demo QA

| Артефакт | Путь |
|----------|------|
| Founder demo | [demo/founder-demo.md](../demo/founder-demo.md) · `scripts/founder-demo.ps1` |
| QA C0–C13 | [phases/qa/](../phases/qa/) |
| QA C0–C25 | там же |
| QA C0–C33 / C0–C37 | там же |
| UI parity vs 1.0 | [ui-parity/](../ui-parity/) · [отчёт C39–C41](../status/261026%20-%20UI%20parity%20C39-C41%20отчёт.md) · C42 visual QA |

---

## Золотой путь (G1–G10, смысл)

1. Handoff → комната + snapshot  
2. Entitlement → staffing_unlocked  
3. Materialize / assign  
4. Tasks + QG (proof → accept)  
5. Lead → hot → CRM stub + outbox  
6. Health (+ earnings)  
7. (Опционально) Strategy Accept / rematerialize / chat / meet  

Не ломать этот путь при новых фичах.
