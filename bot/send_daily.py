"""Отправляет утреннее уведомление с кнопкой, которая открывает мини-приложение.

Запускается GitHub Actions каждый день (см. .github/workflows/daily.yml).
Нужные настройки репозитория:
  секреты   BOT_TOKEN, CHAT_ID
  переменная APP_URL  (адрес сайта на GitHub Pages)
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TZ = dt.timezone(dt.timedelta(hours=5))  # Екатеринбург / Алматы, UTC+5


def start_date() -> dt.date:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'const START = "(\d{4})-(\d{2})-(\d{2})"', html)
    if not m:
        sys.exit("Не нашла дату START в index.html")
    return dt.date(*map(int, m.groups()))


def api(token: str, method: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main() -> None:
    token = os.environ.get("BOT_TOKEN", "").strip()
    chat_id = os.environ.get("CHAT_ID", "").strip()
    app_url = os.environ.get("APP_URL", "").strip()
    force = os.environ.get("FORCE", "false").lower() == "true"
    if not (token and chat_id and app_url):
        sys.exit("Не заданы BOT_TOKEN, CHAT_ID или APP_URL — см. ИНСТРУКЦИЯ.md")

    cards = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
    today = dt.datetime.now(TZ).date()
    n = (today - start_date()).days + 1

    if not force and not (1 <= n <= len(cards)):
        print(f"Сегодня день {n}: карточек на этот день нет, ничего не отправляю.")
        return

    sent_file = ROOT / "last_sent.txt"
    if not force and sent_file.exists() and sent_file.read_text().strip() == today.isoformat():
        print("Сегодня уже отправляли, второй раз не шлю.")
        return

    if 1 <= n <= len(cards):
        text = f"💌 Доброе утро! Карточка № {n} уже ждёт тебя"
    else:
        text = "💌 Проверка связи: бот работает. Скоро здесь будут карточки ❤️"

    res = api(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": [[{"text": "Открыть ❤️", "web_app": {"url": app_url}}]]},
    })
    if not res.get("ok"):
        sys.exit(f"Telegram ответил ошибкой: {res}")
    if not force:
        sent_file.write_text(today.isoformat() + "\n")
    print("Отправлено:", text)


if __name__ == "__main__":
    main()
