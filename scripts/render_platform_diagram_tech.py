# -*- coding: utf-8 -*-
"""Technical data-ownership diagram for stakeholders (PNG)."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "261024 - схема платформы WOWLANCE tech.png"
)

W, H = 1800, 1320
BG = (248, 250, 252)
INK = (15, 23, 42)
MUTED = (71, 85, 105)
WHITE = (255, 255, 255)
DB = (15, 118, 110)  # teal for DB badges

C_AUTH = ((224, 242, 254), (2, 132, 199))
C_STRAT = ((236, 253, 245), (5, 150, 105))
C_TAL = ((254, 243, 199), (180, 83, 9))
C_WL = ((238, 242, 255), (67, 56, 202))
C_CRM = ((252, 231, 243), (190, 24, 93))
C_MONEY = ((255, 247, 237), (194, 65, 12))
C_NOTE = ((241, 245, 249), (51, 65, 85))
C_RULE = ((254, 252, 232), (161, 98, 7))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = (
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    )
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_TITLE = font(32, True)
F_H = font(17, True)
F_B = font(15, True)
F_N = font(13)
F_S = font(12)
F_XS = font(11)
F_DB = font(11, True)


def round_box(draw, xy, fill, outline, radius=14, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_center(draw, cx, cy, text, fnt, fill=INK):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - th / 2), text, font=fnt, fill=fill)


def text_left(draw, x, y, text, fnt, fill=INK):
    draw.text((x, y), text, font=fnt, fill=fill)


def multilines_left(draw, x, y, lines, fnt, fill=MUTED, gap=2):
    cy = y
    for line in lines:
        draw.text((x, cy), line, font=fnt, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=fnt)
        cy += (bbox[3] - bbox[1]) + gap
    return cy


def arrow(draw, x1, y1, x2, y2, color, width=3):
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 11
    for da in (0.45, -0.45):
        bx = x2 - size * math.cos(ang + da)
        by = y2 - size * math.sin(ang + da)
        draw.line((x2, y2, bx, by), fill=color, width=width)


def poly_arrow(draw, points, color, width=3):
    for i in range(len(points) - 1):
        draw.line((*points[i], *points[i + 1]), fill=color, width=width)
    arrow(draw, *points[-2], *points[-1], color, width)


def label_box(draw, x, y, text, fnt=F_XS):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 6, 3
    rect = (x - tw / 2 - pad_x, y - th / 2 - pad_y, x + tw / 2 + pad_x, y + th / 2 + pad_y)
    draw.rounded_rectangle(rect, radius=6, fill=WHITE, outline=(203, 213, 225), width=1)
    text_center(draw, x, y, text, fnt, MUTED)


def db_badge(draw, cx, y, text="своя PostgreSQL"):
    bbox = draw.textbbox((0, 0), text, font=F_DB)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 8, 4
    # cylinder-ish pill
    rect = (cx - tw / 2 - pad_x, y, cx + tw / 2 + pad_x, y + th + pad_y * 2)
    draw.rounded_rectangle(rect, radius=10, fill=(204, 251, 241), outline=DB, width=2)
    text_center(draw, cx, y + th / 2 + pad_y, text, F_DB, DB)


def service_block(draw, x, y, w, h, title, role_lines, db_lines, colors, badge=None):
    fill, outline = colors
    round_box(draw, (x, y, x + w, y + h), fill, outline, radius=16, width=3 if badge else 2)
    text_center(draw, x + w / 2, y + 22, title, F_B, outline)
    if badge:
        bw, bh = 88, 20
        bx, by = x + w - bw - 10, y + 8
        round_box(draw, (bx, by, bx + bw, by + bh), outline, outline, radius=7, width=1)
        text_center(draw, bx + bw / 2, by + bh / 2, badge, F_XS, WHITE)

    # role
    y1 = multilines_left(draw, x + 14, y + 40, role_lines, F_S, MUTED, 2)

    # divider
    draw.line((x + 12, y1 + 6, x + w - 12, y1 + 6), fill=(203, 213, 225), width=1)

    # db section header
    text_left(draw, x + 14, y1 + 12, "В своей БД хранит:", F_XS, DB)
    multilines_left(draw, x + 14, y1 + 28, db_lines, F_XS, INK, 2)

    # db badge under card
    db_badge(draw, x + w / 2, y + h + 8)
    return x, y, w, h


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    text_center(draw, W / 2, 30, "WOWLANCE — технические потоки данных и владение БД", F_TITLE, INK)
    text_center(
        draw,
        W / 2,
        62,
        "Правило: сервисы НЕ читают чужие таблицы  ·  только API / события / снимки  ·  у каждого — своя PostgreSQL",
        F_N,
        MUTED,
    )

    # Auth
    ay, ah = 90, 70
    round_box(draw, (60, ay, W - 60, ay + ah), C_AUTH[0], C_AUTH[1], 14, 2)
    text_center(draw, W / 2, ay + 22, "Регистрация → Keycloak → Gateway", F_H, C_AUTH[1])
    text_center(
        draw,
        W / 2,
        ay + 48,
        "SoT личности: Keycloak (sub, роли). В сервисах — только shadow-пользователь / кэш по sub. Пароли и signup НЕ в WowLance.",
        F_S,
        MUTED,
    )

    # Domain cards — taller for DB details
    card_y = 190
    h = 210
    w_s, w_wl = 300, 360
    gap = 28
    total = 3 * w_s + w_wl + 3 * gap
    x0 = (W - total) / 2
    x_usc = x0
    x_tal = x_usc + w_s + gap
    x_wl = x_tal + w_s + gap
    x_crm = x_wl + w_wl + gap

    service_block(
        draw, x_usc, card_y, w_s, h, "US Closer",
        ["Стратегия · SOP · витрина", "фаундера"],
        [
            "• тексты стратегии, версии",
            "• ссылки на файлы (URI)",
            "• read-модель KPI комнаты",
            "  (копия/подписка, не БД WL)",
        ],
        C_STRAT,
    )
    service_block(
        draw, x_tal, card_y, w_s, h, "Talent",
        ["Маркетплейс verified", "фрилансеров"],
        [
            "• профили, skills, level",
            "• верификация, availability",
            "• рейтинг / MAU (если есть)",
            "• SoT по людям платформы",
        ],
        C_TAL,
    )
    service_block(
        draw, x_wl, card_y, w_wl, h, "WowLance",
        ["КОМНАТА исполнения", "все данные проекта/комнаты"],
        [
            "• room, snapshot стратегии (копия)",
            "• slots, roster-снимок, tasks, QG",
            "• лиды до Hot + история прогрева",
            "• earnings, chat, health-агрегаты",
            "• outbox событий наружу",
        ],
        C_WL,
        "наш сервис",
    )
    service_block(
        draw, x_crm, card_y, w_s, h, "CRM",
        ["Сделки после Hot", "работа менеджера"],
        [
            "• сделки, стадии, won/lost",
            "• копия Hot + история",
            "  из handoff WowLance",
            "• НЕ читает БД комнаты",
        ],
        C_CRM,
    )

    y_arrow_top = card_y - 14
    y_db = card_y + h + 36  # below db badges

    # ① US Closer → WL: strategy SNAPSHOT copy
    poly_arrow(
        draw,
        [
            (x_usc + w_s / 2, card_y),
            (x_usc + w_s / 2, y_arrow_top),
            (x_wl + w_wl / 2, y_arrow_top),
            (x_wl + w_wl / 2, card_y),
        ],
        C_STRAT[1],
        3,
    )
    label_box(
        draw,
        (x_usc + x_wl + w_wl / 2) / 2,
        y_arrow_top,
        "① FounderHandoff: КОПИЯ снимка стратегии → БД WowLance (immutable)",
    )

    # ② Talent → WL: roster SNAPSHOT
    y1 = card_y + 55
    arrow(draw, x_tal + w_s, y1, x_wl, y1, C_TAL[1], 3)
    label_box(
        draw,
        (x_tal + w_s + x_wl) / 2,
        y1 - 16,
        "② TalentRosterUpsert: снимок verified → локальный roster в БД WL",
    )

    # ③ WL → CRM: Hot + history (event/API, not DB)
    y2 = card_y + 95
    arrow(draw, x_wl + w_wl, y2, x_crm, y2, C_CRM[1], 3)
    label_box(
        draw,
        (x_wl + w_wl + x_crm) / 2,
        y2 - 16,
        "③ HotLeadToCrm: событие/API + история (не JOIN в БД WL)",
    )

    # ④ WL → US Closer: analytics pull/push for founder
    y_health = y_db + 8
    poly_arrow(
        draw,
        [
            (x_wl + w_wl * 0.3, card_y + h + 34),
            (x_wl + w_wl * 0.3, y_health),
            (x_usc + w_s / 2, y_health),
            (x_usc + w_s / 2, card_y + h + 34),
        ],
        C_STRAT[1],
        3,
    )
    label_box(
        draw,
        (x_usc + x_wl) / 2 + 10,
        y_health,
        "④ RoomHealth: фаундер читает аналитику в US Closer ← агрегаты из WL",
    )

    # ⑤ WL → Talent signals
    poly_arrow(
        draw,
        [
            (x_wl + w_wl * 0.55, card_y + h + 34),
            (x_wl + w_wl * 0.55, y_health + 28),
            (x_tal + w_s / 2, y_health + 28),
            (x_tal + w_s / 2, card_y + h + 34),
        ],
        C_TAL[1],
        3,
    )
    label_box(
        draw,
        (x_tal + x_wl + w_wl * 0.2) / 2 + 40,
        y_health + 28,
        "⑤ TaskAccepted / MemberTerminated → Talent (рейтинг), не в БД Talent напрямую",
    )

    # Money row
    money_y = 560
    mw, mh, mg = 320, 150, 40
    mt = 3 * mw + 2 * mg
    mx0 = (W - mt) / 2
    money_specs = [
        (
            "Order",
            ["Заказ пакета комнаты"],
            ["• order_id, пакет, слоты", "• статус заказа", "• связь order ↔ room"],
        ),
        (
            "Payment",
            ["Факт оплаты"],
            ["• платежи, статусы", "• сигнал «оплачено»", "• не entitlement комнаты"],
        ),
        (
            "Invoicing",
            ["Счета платформы"],
            ["• счета по заказу пакета", "• не счёт конечному лиду", "  (это контур CRM)"],
        ),
    ]
    mxs = []
    for i, (title, role, db) in enumerate(money_specs):
        x = mx0 + i * (mw + mg)
        mxs.append(x)
        service_block(draw, x, money_y, mw, mh, title, role, db, C_MONEY)

    # Payment → Order → entitlement in WL
    arrow(draw, mxs[1], money_y + 50, mxs[0] + mw, money_y + 50, C_MONEY[1], 3)
    label_box(draw, (mxs[0] + mw + mxs[1]) / 2, money_y + 34, "оплата OK")
    arrow(draw, mxs[0] + mw, money_y + 90, mxs[2], money_y + 90, C_MONEY[1], 3)
    label_box(draw, (mxs[0] + mw + mxs[2]) / 2, money_y + 106, "счёт по order")

    # Entitlement into WL DB flag
    poly_arrow(
        draw,
        [
            (mxs[0] + mw / 2, money_y),
            (mxs[0] + mw / 2, y_health + 56),
            (x_wl + w_wl * 0.75, y_health + 56),
            (x_wl + w_wl * 0.75, card_y + h + 34),
        ],
        C_MONEY[1],
        3,
    )
    label_box(
        draw,
        x_wl + w_wl * 0.75 + 20,
        y_health + 56,
        "⑥ EntitlementGranted → в БД WL флаг staffing_unlocked",
    )

    # Object storage note
    stor_y = 800
    round_box(draw, (60, stor_y, W - 60, stor_y + 56), (255, 255, 255), (148, 163, 184), 12, 2)
    text_center(
        draw,
        W / 2,
        stor_y + 28,
        "Object storage (общий файловый слой): SOP/вложения по URI + версия в пути + checksum  ·  "
        "в БД сервисов лежат ссылки, не байты файлов в брокере",
        F_S,
        MUTED,
    )

    # Golden rules
    ry = 880
    round_box(draw, (60, ry, W - 60, H - 40), C_RULE[0], C_RULE[1], 14, 2)
    text_left(draw, 80, ry + 14, "Как читать схему (владение данными)", F_H, C_RULE[1])

    rules_l = [
        "1. Talent — SoT людей. WowLance НЕ ходит в БД Talent;",
        "   при verified делает СНИМОК в свой roster и matching",
        "   читает только локальную копию.",
        "2. US Closer — SoT стратегии. В комнату уходит КОПИЯ",
        "   версии (snapshot). Новая версия — только через",
        "   Accept тимлида; чужую БД US Closer не читаем.",
        "3. Вся операционка проекта/комнаты (задачи, слоты,",
        "   лиды до Hot, чат, earned) — SoT в БД WowLance.",
    ]
    rules_r = [
        "4. Фаундер смотрит аналитику в US Closer: туда приходят",
        "   агрегаты RoomHealth из WowLance (pull/API или outbox),",
        "   а не прямой SELECT из БД комнаты.",
        "5. CRM получает Hot + историю handoff’ом; дальше сделка",
        "   живёт в БД CRM. Упрощённая воронка в WL — только прогрев.",
        "6. Order/Payment решают «пакет оплачен»; в WL пишется",
        "   entitlement / staffing_unlocked — без этого нет набора.",
        "7. Keycloak — единственный SoT логина; везде один sub.",
    ]
    y = ry + 46
    for a, b in zip(rules_l, rules_r):
        text_left(draw, 80, y, a, F_N, INK)
        text_left(draw, 920, y, b, F_N, INK)
        y += 22

    text_center(
        draw,
        W / 2,
        H - 22,
        "docs/261024 · перерисовать: python scripts/render_platform_diagram_tech.py",
        F_XS,
        MUTED,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
