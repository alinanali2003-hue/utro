"""Разовая настройка бота.

1) Показывает, кто нажал «Start» в боте, и их CHAT_ID.
2) Ставит кнопку меню «Открыть 💌» рядом с полем ввода, чтобы приложение
   можно было открыть в любой момент, а не только из утреннего сообщения.
"""
import json
import os
import sys
import urllib.request


def api(token: str, method: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main() -> None:
    token = os.environ.get("BOT_TOKEN", "").strip()
    app_url = os.environ.get("APP_URL", "").strip()
    if not token:
        sys.exit("Не задан секрет BOT_TOKEN — см. ИНСТРУКЦИЯ.md")

    me = api(token, "getMe")
    print("Бот:", "@" + me["result"]["username"])

    updates = api(token, "getUpdates").get("result", [])
    chats = {}
    for u in updates:
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat")
        if chat and chat.get("type") == "private":
            name = " ".join(x for x in [chat.get("first_name"), chat.get("last_name")] if x)
            chats[chat["id"]] = f'{name} (@{chat.get("username", "—")})'
    print()
    if chats:
        print("Кто писал боту за последние сутки:")
        for cid, name in chats.items():
            print(f"  CHAT_ID = {cid}   ←  {name}")
    else:
        print("Пока никто не нажимал Start (или это было больше суток назад).")
        print("Нажмите Start в боте и запустите эту настройку ещё раз.")

    # Для всех остальных — обычное меню без приложения, чтобы посторонний,
    # случайно нашедший бота, ничего не увидел.
    api(token, "setChatMenuButton", {"menu_button": {"type": "default"}})

    chat_id = os.environ.get("CHAT_ID", "").strip()
    print()
    if app_url and chat_id:
        r = api(token, "setChatMenuButton", {
            "chat_id": int(chat_id),
            "menu_button": {"type": "web_app", "text": "Открыть 💌", "web_app": {"url": app_url}},
        })
        print(f"Кнопка меню «Открыть 💌» для CHAT_ID {chat_id}:", "готово" if r.get("ok") else r)
    else:
        print("Кнопку меню «Открыть 💌» поставлю, когда будут заданы APP_URL и CHAT_ID —")
        print("тогда просто запустите эту настройку ещё раз.")


if __name__ == "__main__":
    main()
