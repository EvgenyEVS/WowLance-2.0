# -*- coding: utf-8 -*-
"""Render stakeholder platform flow diagram (PNG)."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "261024 - схема платформы WOWLANCE.png"
)

W, H = 1680, 1180
BG = (248, 250, 252)
INK = (15, 23, 42)
MUTED = (71, 85, 105)
LINE = (100, 116, 139)
WHITE = (255, 255, 255)

C_AUTH = ((224, 242, 254), (2, 132, 199))
C_STRAT = ((236, 253, 245), (5, 150, 105))
C_TAL = ((254, 243, 199), (180, 83, 9))
C_WL = ((238, 242, 255), (67, 56, 202))
C_CRM = ((252, 231, 243), (190, 24, 93))
C_MONEY = ((255, 247, 237), (194, 65, 12))
C_NOTE = ((241, 245, 249), (51, 65, 85))


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


F_TITLE = font(34, True)
F_H = font(18, True)
F_B = font(16, True)
F_N = font(14)
F_S = font(13)
F_XS = font(11)


def round_box(draw, xy, fill, outline, radius=16, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_center(draw, cx, cy, text, fnt, fill=INK):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - th / 2), text, font=fnt, fill=fill)


def text_left(draw, x, y, text, fnt, fill=INK):
    draw.text((x, y), text, font=fnt, fill=fill)


def multilines(draw, cx, top, lines, fnt, fill=MUTED, gap=3):
    y = top
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fnt)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw / 2, y), line, font=fnt, fill=fill)
        y += th + gap


def arrow(draw, x1, y1, x2, y2, color=LINE, width=3):
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 12
    for da in (0.45, -0.45):
        bx = x2 - size * math.cos(ang + da)
        by = y2 - size * math.sin(ang + da)
        draw.line((x2, y2, bx, by), fill=color, width=width)


def poly_arrow(draw, points, color=LINE, width=3):
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        draw.line((x1, y1, x2, y2), fill=color, width=width)
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    arrow(draw, x1, y1, x2, y2, color, width)


def label_box(draw, x, y, text, fnt=F_XS):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 7, 4
    rect = (x - tw / 2 - pad_x, y - th / 2 - pad_y, x + tw / 2 + pad_x, y + th / 2 + pad_y)
    draw.rounded_rectangle(rect, radius=7, fill=WHITE, outline=(203, 213, 225), width=1)
    text_center(draw, x, y, text, fnt, MUTED)


def service_card(draw, x, y, w, h, title, lines, colors, badge=None):
    fill, outline = colors
    round_box(draw, (x, y, x + w, y + h), fill, outline, radius=18, width=3 if badge else 2)
    text_center(draw, x + w / 2, y + 30, title, F_B, outline)
    multilines(draw, x + w / 2, y + 52, lines, F_S, MUTED, gap=3)
    if badge:
        bw, bh = 92, 24
        bx, by = x + w - bw - 12, y + 10
        round_box(draw, (bx, by, bx + bw, by + bh), outline, outline, radius=8, width=1)
        text_center(draw, bx + bw / 2, by + bh / 2, badge, F_XS, WHITE)
    return x, y, w, h


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    text_center(draw, W / 2, 34, "WOWLANCE — движение людей и информации", F_TITLE, INK)
    text_center(
        draw,
        W / 2,
        68,
        "WowLance = микросервис комнаты  ·  соседи: US Closer · Talent · CRM · Keycloak · Order / Payment / Invoicing",
        F_N,
        MUTED,
    )

    # Auth
    ay, ah = 100, 78
    round_box(draw, (70, ay, W - 70, ay + ah), C_AUTH[0], C_AUTH[1], 16, 2)
    text_center(draw, W / 2, ay + 26, "Регистрация  →  Keycloak  →  API Gateway", F_H, C_AUTH[1])
    text_center(
        draw,
        W / 2,
        ay + 54,
        "Один вход: директор · тимлид · менеджер · фрилансер · админ   |   JWT с единым sub на всю платформу",
        F_S,
        MUTED,
    )

    # Domain row — WowLance centered as hero, larger
    card_y = 220
    h_side, h_wl = 148, 168
    w_side, w_wl = 260, 320
    gap = 36
    # layout: USC | Talent | WL | CRM
    total = w_side + gap + w_side + gap + w_wl + gap + w_side
    x0 = (W - total) / 2
    x_usc = x0
    x_tal = x_usc + w_side + gap
    x_wl = x_tal + w_side + gap
    x_crm = x_wl + w_wl + gap
    y_side = card_y + (h_wl - h_side) / 2

    service_card(
        draw, x_usc, y_side, w_side, h_side, "US Closer",
        ["Стратегия продаж", "SOP / документы", "Витрина результатов"],
        C_STRAT,
    )
    service_card(
        draw, x_tal, y_side, w_side, h_side, "Talent",
        ["Маркетплейс", "Verified фрилансеры", "Навыки · уровень"],
        C_TAL,
    )
    service_card(
        draw, x_wl, card_y, w_wl, h_wl, "WowLance",
        ["КОМНАТА команды", "Задачи · прогрев лидов", "Операционная аналитика", "Сводки «как дела»"],
        C_WL,
        "наш сервис",
    )
    service_card(
        draw, x_crm, y_side, w_side, h_side, "CRM",
        ["Продажи после Hot", "Стадии сделки", "Менеджер · Won/Lost"],
        C_CRM,
    )

    # --- Info arrows (clear routing above/below cards) ---
    # 1) US Closer → WL (over the top): handoff
    y_top = card_y - 8
    poly_arrow(
        draw,
        [
            (x_usc + w_side / 2, y_side),
            (x_usc + w_side / 2, y_top),
            (x_wl + w_wl / 2, y_top),
            (x_wl + w_wl / 2, card_y),
        ],
        C_STRAT[1],
        3,
    )
    label_box(draw, (x_usc + x_wl + w_wl / 2) / 2 + 40, y_top, "① снимок стратегии (handoff)")

    # 2) Talent → WL (direct)
    y1 = y_side + h_side * 0.45
    arrow(draw, x_tal + w_side, y1, x_wl, y1, C_TAL[1], 3)
    label_box(draw, (x_tal + w_side + x_wl) / 2, y1 - 18, "② verified roster")

    # 3) WL → CRM
    y2 = y_side + h_side * 0.55
    arrow(draw, x_wl + w_wl, y2, x_crm, y2, C_CRM[1], 3)
    label_box(draw, (x_wl + w_wl + x_crm) / 2, y2 - 18, "③ Hot + история лида")

    # 4) WL → US Closer health (below)
    y_bot = card_y + h_wl + 28
    poly_arrow(
        draw,
        [
            (x_wl + w_wl * 0.35, card_y + h_wl),
            (x_wl + w_wl * 0.35, y_bot),
            (x_usc + w_side / 2, y_bot),
            (x_usc + w_side / 2, y_side + h_side),
        ],
        C_STRAT[1],
        3,
    )
    label_box(draw, (x_usc + x_wl) / 2 + 20, y_bot, "④ сводки health / KPI → витрина")

    # Money row
    money_y = 500
    mw, mh, mg = 300, 112, 48
    mt = 3 * mw + 2 * mg
    mx0 = (W - mt) / 2
    money = [
        ("Order", ["Заказ пакета комнаты", "Слоты / тариф"]),
        ("Payment", ["Оплата прошла", "Деньги платформы"]),
        ("Invoicing", ["Счета / закрывающие", "По заказу пакета"]),
    ]
    mxs = []
    for i, (title, lines) in enumerate(money):
        x = mx0 + i * (mw + mg)
        mxs.append(x)
        service_card(draw, x, money_y, mw, mh, title, lines, C_MONEY)

    # Payment → Order
    arrow(draw, mxs[1], money_y + mh * 0.4, mxs[0] + mw, money_y + mh * 0.4, C_MONEY[1], 3)
    label_box(draw, (mxs[0] + mw + mxs[1]) / 2, money_y + mh * 0.4 - 16, "оплата OK")
    # Order → Invoicing
    arrow(draw, mxs[0] + mw, money_y + mh * 0.65, mxs[2], money_y + mh * 0.65, C_MONEY[1], 3)
    label_box(draw, (mxs[0] + mw + mxs[2]) / 2, money_y + mh * 0.65 + 16, "счёт по заказу")

    # Order → WL entitlement (up)
    poly_arrow(
        draw,
        [
            (mxs[0] + mw / 2, money_y),
            (mxs[0] + mw / 2, y_bot + 36),
            (x_wl + w_wl * 0.65, y_bot + 36),
            (x_wl + w_wl * 0.65, card_y + h_wl),
        ],
        C_MONEY[1],
        3,
    )
    label_box(draw, x_wl + w_wl * 0.65 + 70, y_bot + 36, "⑤ entitlement → можно staff’ить")

    # People strip
    py = 660
    round_box(draw, (70, py, W - 70, py + 88), WHITE, (203, 213, 225), 14, 2)
    text_left(draw, 90, py + 14, "Движение людей", F_H, INK)
    people = (
        "1. Регистрация / Keycloak   →   "
        "2. Директор в US Closer   →   "
        "3. Фрилансер в Talent (verify)   →   "
        "4. Команда в комнату WowLance   →   "
        "5. Менеджер в CRM после Hot"
    )
    text_left(draw, 90, py + 52, people, F_N, MUTED)

    # Tech
    ty = 780
    round_box(draw, (70, ty, W - 70, H - 36), C_NOTE[0], C_NOTE[1], 14, 2)
    text_left(draw, 90, ty + 14, "Основные технические решения", F_H, C_NOTE[1])
    left = [
        "• Своя БД у каждого сервиса",
        "• Связь по контрактам (API / события), не чужие таблицы",
        "• Снимок стратегии в комнате + Accept тимлида",
        "• Файлы в object storage — в событиях URI + версия",
    ]
    right = [
        "• Staffing только после entitlement (оплата пакета)",
        "• Outbox: RoomCreated · HotLeadToCrm · health · TaskAccepted",
        "• В WL — упрощённый прогрев; сделка — во внешней CRM",
        "• Gateway + JWT снаружи; service-token между сервисами",
    ]
    y = ty + 48
    for a, b in zip(left, right):
        text_left(draw, 90, y, a, F_N, INK)
        text_left(draw, 860, y, b, F_N, INK)
        y += 30

    text_center(
        draw,
        W / 2,
        H - 18,
        "docs/261024 - схема платформы для стейкхолдеров.md   ·   перерисовать: python scripts/render_platform_diagram.py",
        F_XS,
        MUTED,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
