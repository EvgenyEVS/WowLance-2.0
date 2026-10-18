# Задание: Pytest всегда на `wowlance_test` (follow-up Q2)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-18 |
| **Источник** | [QA отчёт C0–C13](261017%20-%20QA%20полный%20прогон%20C0-C13%20отчёт.md) находка **Q2** |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | правки в `main` / `fix/pytest-wowlance-test` (мини-фикс) |
| **Срок** | ≤ 0.5 дня |
| **Исполнитель** | любой стажёр / ИИ |

---

## 1. Зачем

На полном прогоне C0–C13 QA форсировал `DATABASE_URL=…/wowlance_test`, потому что
при ошибке конфигурации pytest мог бить в app-БД `wowlance` и делать `drop_all`
(UI/Swagger «отваливаются»). Нужно, чтобы **по умолчанию** suite никогда не
трогал `wowlance`.

---

## 2. DoD

- [ ] `backend/tests/conftest.py`: URL тестов всегда с именем БД `wowlance_test`
      (ремап с `DATABASE_URL`; если `TEST_DATABASE_URL` указывает на `wowlance` —
      rewrite или `pytest.exit` с понятной ошибкой).
- [ ] `backend/README.md` — раздел «Тесты» описывает правило (без ручной подмены
      `DATABASE_URL` для обычного `pytest -q`).
- [ ] `pytest -q` зелёный; после прогона `GET` golden/dev room на `wowlance` жив.

---

## 3. Статус

**Сделано в том же коммите/PR, что и правки по отчёту QA (2026-10-18):** hardening
в `conftest.py` + текст в README. Этот файл — канон follow-up для трекинга Q2.
