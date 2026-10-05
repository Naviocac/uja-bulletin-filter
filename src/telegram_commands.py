"""
telegram_commands.py

Runs once, checks Telegram for anything new since the last run (new /start
or /intereses commands, button taps), updates data/subscribers.json
accordingly, and edits the relevant messages in place to show the result.

Meant to be called every ~15 minutes by a scheduled GitHub Actions workflow
(handle_commands.yml), which also commits data/subscribers.json and
data/telegram_offset.json back to the repo afterwards. There's no
always-on bot process — this script just "catches up" on whatever
happened since it last ran.

Usage:
    python src/telegram_commands.py
"""

import json
import os

import requests
from dotenv import load_dotenv

from categories import CATEGORIES

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSCRIBERS_PATH = os.path.join(BASE_DIR, "data", "subscribers.json")
OFFSET_PATH = os.path.join(BASE_DIR, "data", "telegram_offset.json")

CATEGORY_ROW_WIDTH = 1  # one category per row keeps long labels readable


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_updates(offset):
    response = requests.get(
        f"{API_BASE}/getUpdates",
        params={"offset": offset, "timeout": 0},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("result", [])


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{API_BASE}/sendMessage", data=payload, timeout=10)


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{API_BASE}/editMessageText", data=payload, timeout=10)


def answer_callback(callback_query_id, text=None):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    requests.post(f"{API_BASE}/answerCallbackQuery", data=payload, timeout=10)


def main_menu_markup(interests):
    buttons = []
    for cat_key, category in CATEGORIES.items():
        count = len(interests.get(cat_key, []))
        label = f"{category['label']} ({count})" if count else category["label"]
        buttons.append([{"text": label, "callback_data": f"cat:{cat_key}"}])
    return {"inline_keyboard": buttons}


def submenu_markup(cat_key, interests):
    category = CATEGORIES[cat_key]
    selected = set(interests.get(cat_key, []))
    buttons = []
    for sub_key, sub_label in category["subtopics"].items():
        mark = "✅" if sub_key in selected else "⬜"
        buttons.append(
            [{"text": f"{mark} {sub_label}", "callback_data": f"sub:{cat_key}:{sub_key}"}]
        )
    buttons.append([{"text": "⬅ Volver a categorías", "callback_data": "back"}])
    return {"inline_keyboard": buttons}


MAIN_MENU_TEXT = (
    "Elige las categorías que te interesan. Toca una para ver y marcar sus "
    "temas concretos. Puedes volver cuando quieras y cambiar lo que sea."
)


def handle_message(subscribers, message):
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "")
    username = message["chat"].get("username") or message["chat"].get("first_name", "")

    if text in ("/start", "/intereses"):
        if chat_id not in subscribers:
            subscribers[chat_id] = {"username": username, "interests": {}}
        else:
            subscribers[chat_id]["username"] = username
        send_message(chat_id, MAIN_MENU_TEXT, main_menu_markup(subscribers[chat_id]["interests"]))


def handle_callback(subscribers, callback_query):
    chat_id = str(callback_query["message"]["chat"]["id"])
    message_id = callback_query["message"]["message_id"]
    data = callback_query.get("data", "")

    if chat_id not in subscribers:
        subscribers[chat_id] = {"username": "", "interests": {}}
    interests = subscribers[chat_id]["interests"]

    if data == "back":
        edit_message(chat_id, message_id, MAIN_MENU_TEXT, main_menu_markup(interests))
        answer_callback(callback_query["id"])
        return

    if data.startswith("cat:"):
        cat_key = data.split(":", 1)[1]
        if cat_key not in CATEGORIES:
            answer_callback(callback_query["id"])
            return
        category = CATEGORIES[cat_key]
        edit_message(
            chat_id,
            message_id,
            f"{category['label']} — marca tus temas:",
            submenu_markup(cat_key, interests),
        )
        answer_callback(callback_query["id"])
        return

    if data.startswith("sub:"):
        _, cat_key, sub_key = data.split(":", 2)
        if cat_key not in CATEGORIES or sub_key not in CATEGORIES[cat_key]["subtopics"]:
            answer_callback(callback_query["id"])
            return
        chosen = interests.setdefault(cat_key, [])
        if sub_key in chosen:
            chosen.remove(sub_key)
            feedback = "Quitado"
        else:
            chosen.append(sub_key)
            feedback = "Añadido ✅"
        if not chosen:
            interests.pop(cat_key, None)
        category = CATEGORIES[cat_key]
        edit_message(
            chat_id,
            message_id,
            f"{category['label']} — marca tus temas:",
            submenu_markup(cat_key, interests),
        )
        answer_callback(callback_query["id"], feedback)
        return

    answer_callback(callback_query["id"])


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in your .env file.")

    subscribers = load_json(SUBSCRIBERS_PATH, {})
    offset_data = load_json(OFFSET_PATH, {"offset": 0})
    offset = offset_data.get("offset", 0)

    updates = get_updates(offset)
    if not updates:
        print("No new Telegram updates.")
        return

    for update in updates:
        if "message" in update:
            handle_message(subscribers, update["message"])
        elif "callback_query" in update:
            handle_callback(subscribers, update["callback_query"])
        offset = update["update_id"] + 1

    save_json(SUBSCRIBERS_PATH, subscribers)
    save_json(OFFSET_PATH, {"offset": offset})
    print(f"Processed {len(updates)} update(s). {len(subscribers)} total subscriber(s).")


if __name__ == "__main__":
    main()