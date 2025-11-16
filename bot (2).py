# 🔮 БОТ-ВІЩУНСЬКИЙ (оновлений під aiogram 3.x)
# Повна підтримка OpenRouter, BuyMeACoffee, щоденні ліміти й автооновлення

import aiohttp
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
import html
import time
import requests
import os
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton, Message,
                           CallbackQuery)

import asyncio
import json
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask
from threading import Thread
from datetime import date
from langdetect import detect, LangDetectException
import sqlite3
from contextlib import closing

# ---------------------
# ЗАВАНТАЖЕННЯ НАЛАШТУВАНЬ
# ---------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BUYME_LINK = os.getenv("BUYME_LINK", "https://buymeacoffee.com/manikse")

USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() in ("1", "true", "yes")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DAILY_HOUR = int(os.getenv("DAILY_HOUR", "9"))

if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN не знайдено у .env")

# ---------------------
# ІНІЦІАЛІЗАЦІЯ БОТА
# ---------------------

bot = Bot(token=BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()
dp.include_router(router)

DB_FILE = "users.db"
DAILY_LIMIT = 7  # ліміт на мотивації/віщування на день

LANGUAGES = {
    "uk": {
        "start":
        "Привіт, {name}! Я — Бот-Віщунський 🔮\nОбери, що хочеш сьогодні отримати:",
        "motivation": "Мотивація 💬",
        "prediction": "Віщування 🔮",
        "power": "⚡ Потужність 🇺🇦",
        "premium": "Преміум 💎",
        "language": "🌍 Мова",
        "support": "Підтримати ☕",
        "menu": "Головне меню:"
    },
    "en": {
        "start":
        "Hi, {name}! I'm the Fortune Bot 🔮\nChoose what you'd like today:",
        "motivation": "Motivation 💬",
        "prediction": "Prediction 🔮",
        "power": None,
        "premium": "Premium 💎",
        "language": "🌍 Language",
        "support": "Support ☕",
        "menu": "Main menu:"
    },
    "sk": {
        "start": "Ahoj, {name}! Som Veštecký bot 🔮\nVyber si, čo chceš dnes:",
        "motivation": "Motivácia 💬",
        "prediction": "Veštenie 🔮",
        "power": None,
        "premium": "Prémiové 💎",
        "language": "🌍 Jazyk",
        "support": "Podpora ☕",
        "menu": "Hlavné menu:"
    },
    "de": {
        "start":
        "Hallo, {name}! Ich bin der Wahrsage-Bot 🔮\nWähle, was du heute möchtest:",
        "motivation": "Motivation 💬",
        "prediction": "Vorhersage 🔮",
        "power": None,
        "premium": "Premium 💎",
        "language": "🌍 Sprache",
        "support": "Support ☕",
        "menu": "Hauptmenü:"
    },
    "ja": {
        "start": "こんにちは、{name}！私は占いボットです🔮\n今日は何が欲しいですか：",
        "motivation": "モチベーション 💬",
        "prediction": "予言 🔮",
        "power": None,
        "premium": "プレミアム 💎",
        "language": "🌍 言語",
        "support": "サポート ☕",
        "menu": "メインメニュー："
    }
}
DEFAULT_LANG = "uk"

# ---------------------
# ФРАЗИ
# ---------------------

MOTIVATION_QUOTES = [
    "Ти вже достатньо далеко — не зупиняйся.",
    "Кожен дрібний крок — це частина великої перемоги.",
    "Не чекай ідеального моменту — створюй його.",
    "Помилки — це просто дані. Вчися і рухайся далі.",
    "Навіть коли темно — саме тоді видно, як ти світлиш.",
    "Сьогодні ти працюєш на себе завтрашнього — не підведи його.",
    "Ти можеш більше, ніж здається. Просто зроби перший крок.",
    "Сумніви зникають, коли дієш. Почни зараз.",
    "Не порівнюй себе з іншими — ти йдеш своїм шляхом.",
    "Кожен день — нова сторінка. Напиши її сильно.",
]

PREDICTIONS = [
    "Твій день сьогодні — як міцна кава: бадьорить, але треба смакувати.",
    "Сьогодні Всесвіт підштовхне тебе до маленького вибору — обери сміливо.",
    "Неочікуваний комплімент наблизить тебе до нової можливості.",
    "День підходить для навчання — запиши одну корисну річ і застосуй її.",
    "Хтось сьогодні подумає про тебе з усмішкою — і це вже знак.",
    "Не дивуйся дрібним збігам — то не випадковість, то твій шлях вирівнюється.",
    "Сьогоднішній вечір подарує щось, що тебе здивує — у хорошому сенсі.",
    "Якщо серце каже 'так', — не шукай логіку, просто довірся.",
    "Новина, яку ти отримаєш, стане поштовхом до чогось більшого.",
    "Доля готує тобі маленький сюрприз. Прийми його з усмішкою.",
]

FUNNY_LINES = [
    "Ти знову прокинувся? Уже прогрес!",
    "Якщо лінь — це мистецтво, то ти художник. Але давай ще й зробимо щось корисне 😉",
    "Прокрастинація — це тренування волі. Ти в марафоні, тримай темп.",
    "Навіть комп’ютер перезавантажується — і ти можеш почати спочатку.",
    "Якщо життя — гра, то сьогодні в тебе бонусний рівень.",
    "Усміхнись. Це безкоштовно, але виглядає, як розкіш.",
    "Ти не лінивий — ти просто оптимізуєш витрати енергії.",
    "Якщо нічого не виходить — зроби вигляд, що це експеримент.",
    "Кава не вирішує проблеми, але допомагає не посилати людей.",
    "Не драматизуй — ти головний герой, а не жертва серіалу.",
]

POWER_QUOTES = [
    "Слава Україні! Героям Слава!",
    "Пес Патрон уже готовий до дії, а ти?",
    "Ніхто не зупинить українську потужність 💪🇺🇦",
    "Сьогодні день перемоги — хоча б маленької, але твоєї!",
    "Українець не здається, навіть коли втомився!",
    "Пам’ятай, ми — нація, яку не зламати.",
    "Кожен твій крок — частинка великої перемоги 💙💛",
    "Гімн України лунає в серці щодня.",
    "Сміливо, впевнено, по-українськи!",
    "Потужність у крові, а віра — в серці!",
    "Російськи немовлята - смачніші навіть за варенички зі сметаною😋",
    "Хто тримає цей район?",
    "Слава Україні, слава!",
    "Україна - це не країна, а нація, яка не здається!",
]

POWER_GIFS = []
POWER_STICKERS = []


# ---------------------
# ДОПОМІЖНІ ФУНКЦІЇ
# ---------------------
def init_db():
    """Створює таблицю користувачів, якщо її ще немає."""
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            premium INTEGER DEFAULT 0,
            motivation_used INTEGER DEFAULT 0,
            prediction_used INTEGER DEFAULT 0,
            date TEXT,
            lang TEXT DEFAULT 'uk'
        )
        """)
        conn.commit()


def upgrade_db():
    """Додає поле memory у базу, якщо його ще нема."""
    with closing(sqlite3.connect(DB_FILE)) as conn:
        cur = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cur.fetchall()]
        if "memory" not in columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN memory TEXT DEFAULT '{}'")
            conn.commit()
            print("🧠 Поле 'memory' додано до бази даних.")


def get_user(user_id: str):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        cur = conn.execute("SELECT * FROM users WHERE user_id = ?",
                           (user_id, ))
        row = cur.fetchone()
        if not row:
            return None
        columns = [d[0] for d in cur.description]
        return dict(zip(columns, row))


def save_user(user_id: str, data: dict):
    """Оновлює або створює користувача (включно з пам’яттю у JSON)."""
    memory_json = data.get("memory")
    if isinstance(memory_json, dict):
        memory_json = json.dumps(memory_json, ensure_ascii=False)
    elif memory_json is None:
        memory_json = "{}"

    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.execute(
            """
        INSERT INTO users (user_id, username, premium, motivation_used, prediction_used, date, lang, memory)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            premium=excluded.premium,
            motivation_used=excluded.motivation_used,
            prediction_used=excluded.prediction_used,
            date=excluded.date,
            lang=excluded.lang,
            memory=excluded.memory
        """,
            (
                user_id,
                data.get("username"),
                int(data.get("premium", False)),
                data.get("motivation_used", 0),
                data.get("prediction_used", 0),
                data.get("date"),
                data.get("lang", "uk"),
                memory_json,
            ),
        )
        conn.commit()


def get_memory(user_id: str) -> dict:
    """Отримати пам'ять користувача (JSON -> dict)."""
    u = get_user(user_id)
    if not u or not u.get("memory"):
        return {}
    try:
        return json.loads(u["memory"])
    except Exception:
        return {}


def save_memory(user_id: str, memory: dict):
    """Зберегти пам'ять користувача (dict -> JSON)."""
    u = get_user(user_id)
    if not u:
        return
    u["memory"] = json.dumps(memory, ensure_ascii=False)
    save_user(user_id, u)


def get_all_users():
    """Повертає список усіх user_id з бази."""
    with closing(sqlite3.connect(DB_FILE)) as conn:
        cur = conn.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]


def load_users():
    """Повертає всіх користувачів у форматі словника {user_id: дані}."""
    users = {}
    with closing(sqlite3.connect(DB_FILE)) as conn:
        cur = conn.execute("SELECT * FROM users")
        columns = [d[0] for d in cur.description]
        for row in cur.fetchall():
            user = dict(zip(columns, row))
            users[user["user_id"]] = user
    return users


async def ensure_user(user_id, username=None):
    today = str(date.today())
    s = str(user_id)
    user = get_user(s)
    if not user:
        user = {
            "username": username,
            "premium": False,
            "motivation_used": 0,
            "prediction_used": 0,
            "date": today,
            "lang": DEFAULT_LANG,
            "memory": {},  # ✅ об’єкт, не строка
        }
    else:
        if user["date"] != today:
            user["date"] = today
            user["motivation_used"] = 0
            user["prediction_used"] = 0
        if not user.get("lang"):
            user["lang"] = DEFAULT_LANG
        if user.get("username") != username:
            user["username"] = username
        # 🔥 гарантія, що пам’ять існує
        if isinstance(user.get("memory"), str):
            try:
                user["memory"] = json.loads(user["memory"])
            except:
                user["memory"] = {}

    save_user(s, user)


def make_main_keyboard(lang="uk"):
    L = LANGUAGES.get(lang, LANGUAGES["uk"])
    buttons = [
        [KeyboardButton(text=L["motivation"])],
        [KeyboardButton(text=L["prediction"])],
    ]
    if L.get("power"):
        buttons.append([KeyboardButton(text=L["power"])])
    buttons.append([KeyboardButton(text=L["premium"])])
    buttons.append([KeyboardButton(text=L["language"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def make_premium_inline():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Підтримати ☕", url=BUYME_LINK)
    ]])


# ---------------------
# OPENROUTER / GENERATION
# ---------------------


def _system_prompt_for_lang(lang: str, mode: str) -> str:
    """
    Повертає system prompt під потрібну мову/режим.
    """
    if lang == "en":
        if mode == "motivation":
            return ("You are a calm fortune-teller. "
                    "Write one short motivating sentence in English. "
                    "Keep it natural, no emojis, no long metaphors.")
        elif mode == "prediction":
            return ("You are a calm fortune-teller. "
                    "Write one short realistic daily prediction in English. "
                    "Keep it natural and concise, no emojis.")
        else:
            return (
                "You are a calm fortune-teller. "
                "Write one short inspirational or predictive sentence in English."
            )
    elif lang == "sk":
        if mode == "motivation":
            return (
                "Si pokojný veštec. Napíš jednu krátku motivačnú vetu po slovensky. "
                "Prirodzene, bez emotikonov a bez rozsiahlych metafor.")
        elif mode == "prediction":
            return (
                "Si pokojný veštec. Napíš jednu krátku realistickú dennú predpoveď po slovensky. "
                "Krátko a prirodzene.")
        else:
            return (
                "Si pokojný veštec. Napíš krátku inšpiratívnu alebo predikčnú vetu po slovensky."
            )
    elif lang == "de":
        if mode == "motivation":
            return (
                "Du bist ein ruhiger Wahrsager. Schreibe einen kurzen motivierenden Satz auf Deutsch. "
                "Natürlich und kurz, keine Emojis.")
        elif mode == "prediction":
            return (
                "Du bist ein ruhiger Wahrsager. Schreibe eine kurze realistische Tagesvorhersage auf Deutsch."
            )
        else:
            return (
                "Du bist ein ruhiger Wahrsager. Schreibe einen kurzen inspirierenden oder vorhersagenden Satz auf Deutsch."
            )
    elif lang == "ja":
        if mode == "motivation":
            return ("あなたは冷静な占い師です。日本語で短い励ましの文を書いてください。絵文字は使わず、簡潔に。")
        elif mode == "prediction":
            return ("あなたは冷静な占い師です。日本語で短い現実的な一日の予言を書いてください。簡潔に。")
        else:
            return ("あなたは冷静な占い師です。日本語で短いインスピレーションや予言の文を書いてください。")
    else:  # default ukrainian
        if mode == "motivation":
            return (
                "Ти — спокійний бот-віщун. Напиши одне коротке мотивуюче речення українською. "
                "Без емодзі, без містичних образів, природно.")
        elif mode == "prediction":
            return (
                "Ти — спокійний бот-віщун. Напиши одне коротке реалістичне передбачення на день українською."
            )
        else:
            return (
                "Ти — спокійний бот-віщун. Напиши одне коротке натхненне або передбачальне речення українською."
            )


async def generate_openrouter_prediction(name: str | None,
                                         mode: str = "both",
                                         lang: str = "uk") -> str | None:
    """
    Генерує коротке речення через OpenRouter (або іншу сумісну модель).
    Повертає None у разі помилки / відсутності результату.
    """
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY не задано — пропускаю генерацію.")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Сформуємо user prompt у тій же мові (коротко)
    if lang == "en":
        user_text = f"Write one short { 'motivating' if mode=='motivation' else 'predictive' } sentence in English for {name or 'a person'}."
    elif lang == "sk":
        user_text = f"Napíš jednu krátku {'motivačnú' if mode=='motivation' else 'predikčnú'} vetu po slovensky pre {name or 'osobu'}."
    elif lang == "de":
        user_text = f"Schreibe einen kurzen {'motivierenden' if mode=='motivation' else 'vorhersagenden'} Satz auf Deutsch für {name or 'eine Person'}."
    elif lang == "ja":
        user_text = f"{name or '人'}のために日本語で短い{'励まし' if mode=='motivation' else '予言'}の文を書いてください。"
    else:
        user_text = f"Напиши одне коротке {'мотивуюче' if mode=='motivation' else 'передбачення'} речення українською для {name or 'людини'}."

    system_message = {
        "role": "system",
        "content": _system_prompt_for_lang(lang, mode)
    }
    user_message = {"role": "user", "content": user_text}

    # Пробуємо кілька моделей (тобто список моделей можна коригувати)
    models = [
        "gpt-4o-mini",  # якщо доступний
        "meta-llama/llama-3.1-8b-instruct",
        "mistralai/mistral-7b-instruct",
    ]

    for model in models:
        try:
            payload = {
                "model": model,
                "messages": [system_message, user_message],
                "max_tokens": 60,
                "temperature": 0.8
            }
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            r.raise_for_status()
            res = r.json()

            text = None
            # стандартний формат OpenRouter
            if "choices" in res and res["choices"]:
                choice = res["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    text = choice["message"]["content"]
                elif "text" in choice:
                    text = choice["text"]
                else:
                    text = None

            if "choices" in res and res["choices"]:
                choice = res["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    text = choice["message"]["content"]
                elif "text" in choice:
                    text = choice["text"]
                else:
                    text = None

            if text:
                clean = text.strip().replace("\n", " ").replace("  ",
                                                                " ").strip()
                if len(clean.split()) >= 2:
                    print(f"✅ {model} ({lang}): {clean}")
                    return clean

        except Exception as e:
            print(f"⚠️ Помилка {model}: {e}")
        time.sleep(0.3)

    print("❌ Усі моделі OpenRouter не дали результату.")
    return None


# ---------------------
# ПЕРЕКЛАД (як fallback)
# ---------------------


async def translate_text(text: str, target_lang: str) -> str:
    """Перекладає текст через OpenRouter (як сервіс), повертає оригінал якщо немає ключа."""
    if target_lang == "uk" or not OPENROUTER_API_KEY:
        return text

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # системне повідомлення задає роль перекладача
    lang_name = {
        "en": "English",
        "sk": "Slovak",
        "de": "German",
        "ja": "Japanese"
    }.get(target_lang, "English")
    system = {
        "role":
        "system",
        "content":
        f"You are a translator. Translate the user's text into {lang_name}. Keep style and do not add anything."
    }
    user = {"role": "user", "content": text}

    try:
        r = requests.post(url,
                          headers=headers,
                          json={
                              "model": "gpt-4o-mini",
                              "messages": [system, user],
                              "max_tokens": 200
                          },
                          timeout=20)
        r.raise_for_status()
        res = r.json()
        if "choices" in res and res["choices"]:
            msg = res["choices"][0].get("message") or res["choices"][0].get(
                "text")
            translated = (msg.get("content")
                          if isinstance(msg, dict) else msg) or ""
            return translated.strip()
    except Exception as e:
        print("⚠️ Помилка перекладу:", e)
    return text


# ---------------------
# ХЕНДЛЕРИ (команди)
# ---------------------


@router.message(Command("broadcast"))
async def manual_broadcast(message: Message):
    # тільки ти (замінити на свій Telegram ID)
    if message.from_user.id != 665877665:
        await message.answer("⛔ Тобі не можна це робити.")
        return

    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("Використай формат:\n<b>/broadcast текст</b>")
        return

    text = parts[1]
    await message.answer("🚀 Починаю розсилку...")
    await mass_broadcast(text)
    await message.answer("✅ Розсилку завершено.")


async def generate_openrouter_reply(prompt: str, lang="uk"):
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model":
            "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a kind, magical fortune-telling AI."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ]
        }
        async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)) as response:
            r = await response.json()
            return r["choices"][0]["message"]["content"]


@router.message(lambda m: "Потужність" in m.text)
async def power_cmd(message: Message):
    quote = random.choice(POWER_QUOTES)
    await message.answer(f"⚡ {quote}")


@router.message(Command("start"))
async def start_cmd(message: Message):
    await ensure_user(message.from_user.id, message.from_user.username)
    uid = str(message.from_user.id)
    u = get_user(uid) or {}

    # 1️⃣ Визначаємо мову з Telegram
    tg_lang = (message.from_user.language_code or "").lower()
    print(f"🌐 Telegram language code: {tg_lang}")

    # 2️⃣ Мапимо її на підтримувану
    if tg_lang.startswith("uk"):
        initial_lang = "uk"
    elif tg_lang.startswith("sk") or tg_lang.startswith("cs"):
        initial_lang = "sk"
    elif tg_lang.startswith("de"):
        initial_lang = "de"
    elif tg_lang.startswith("ja") or tg_lang.startswith("jp"):
        initial_lang = "ja"
    else:
        initial_lang = "en"  # fallback

    # 3️⃣ Якщо користувач ще не має обрану мову — встановлюємо
    if "lang" not in u or u["lang"] not in LANGUAGES:
        u["lang"] = initial_lang
        save_user(uid, u)

        # одразу пропонуємо вибрати іншу мову (одноразово)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Українська 🇺🇦",
                                     callback_data="lang_uk")
            ],
            [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")],
            [
                InlineKeyboardButton(text="Slovenčina 🇸🇰",
                                     callback_data="lang_sk")
            ],
            [InlineKeyboardButton(text="Deutsch 🇩🇪", callback_data="lang_de")],
            [InlineKeyboardButton(text="日本語 🇯🇵", callback_data="lang_ja")],
        ])
        await message.answer(LANGUAGES[initial_lang]["start"].format(
            name=message.from_user.first_name or "друже"),
                             reply_markup=make_main_keyboard(initial_lang))
        await asyncio.sleep(0.3)
        await message.answer(
            "🌍 Обери мову для спілкування / Choose your language:",
            reply_markup=kb)
        return

    # 4️⃣ Інакше — просто вітаємо користувача з його мовою
    lang = u["lang"]
    L = LANGUAGES.get(lang, LANGUAGES["uk"])
    await message.answer(
        L["start"].format(name=message.from_user.first_name or "друже"),
        reply_markup=make_main_keyboard(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def change_lang(callback_query: types.CallbackQuery):
    lang_code = callback_query.data.split("_", 1)[1]
    user_id = str(callback_query.from_user.id)
    user = get_user(user_id) or {}
    user["lang"] = lang_code
    save_user(user_id, user)

    messages = {
        "uk": "✅ Мову змінено на українську!",
        "en": "✅ Language changed to English!",
        "sk": "✅ Jazyk bol zmenený na slovenčinu!",
        "de": "✅ Sprache wurde auf Deutsch geändert!",
        "ja": "✅ 言語が日本語に変更されました！"
    }

    await callback_query.message.delete(
    )  # ❌ видаляємо старе повідомлення з кнопками
    await callback_query.message.answer(  # ✅ надсилаємо нове повідомлення з reply-клавіатурою
        messages.get(lang_code, "✅ Language changed."),
        reply_markup=make_main_keyboard(lang_code))
    await callback_query.answer()
    return


@router.message(lambda m: any(
    word in (m.text or "")
    for word in ["Мотивація", "Motivation", "Motivácia", "Motivation 💬"]))
async def motivation_cmd(message: Message):
    uid = str(message.from_user.id)
    username = message.from_user.username
    await ensure_user(uid, username)

    user = get_user(uid)
    if not user:
        await message.answer("⚠️ Сталася помилка. Спробуй ще раз.")
        return

    lang = user.get("lang", DEFAULT_LANG)
    today = str(date.today())

    # якщо новий день — обнулити ліміти
    if user["date"] != today:
        user["date"] = today
        user["motivation_used"] = 0
        user["prediction_used"] = 0

    if not user.get("premium") and user["motivation_used"] >= DAILY_LIMIT:
        await message.answer(
            "☕ Твій денний ліміт мотивацій вичерпано! Підтримай бота, щоб отримати необмежений доступ 💎",
            reply_markup=make_premium_inline())
        return

    # збільшуємо лічильник
    user["motivation_used"] += 1
    save_user(uid, user)

    # отримуємо випадкову мотивацію
    quote = random.choice(MOTIVATION_QUOTES)

    # пробуємо отримати генерацію з OpenRouter
    ai_quote = await generate_openrouter_prediction(
        name=message.from_user.first_name, mode="motivation", lang=lang)

    if ai_quote:
        quote = ai_quote

    await message.answer(f"💬 {quote}")


@router.message(lambda m: any(
    word in (m.text or "")
    for word in ["Віщування", "Prediction", "Veštenie", "Prediction 🔮"]))
async def prediction_cmd(message: Message):
    uid = str(message.from_user.id)
    username = message.from_user.username
    await ensure_user(uid, username)
    u = get_user(uid)
    if not u:
        await message.answer("⚠️ Помилка бази даних. Спробуй ще раз.")
        return
    lang = u.get("lang", DEFAULT_LANG)

    if not u.get("premium", False) and u.get("prediction_used",
                                             0) >= DAILY_LIMIT:
        await message.answer(
            f"Твій денний ліміт ({DAILY_LIMIT}) на віщування вичерпано ☹️\nОтримай <b>Преміум</b> ☕ тут:",
            reply_markup=make_premium_inline())
        return

    u["prediction_used"] = u.get("prediction_used", 0) + 1
    save_user(uid, u)

    ai_text = None
    if OPENROUTER_API_KEY:
        ai_text = await generate_openrouter_prediction(
            message.from_user.first_name, mode="prediction", lang=lang)

    if ai_text:
        safe_text = html.escape(ai_text)
        await message.answer(safe_text, parse_mode=None)
    else:
        text = random.choice(PREDICTIONS)
        if lang != "uk" and OPENROUTER_API_KEY:
            text = await translate_text(text, lang)
        await message.answer(text)


@router.message(lambda m: any(word in (m.text or "")
                              for word in ["Преміум", "Premium", "Prémiové"]))
async def premium_cmd(message: Message):
    await message.answer(
        "Підтримай Бота-Віщунського ☕\nОтримай безлімітну мотивацію та віщування!\n",
        reply_markup=make_premium_inline())


@router.message(lambda m: any(word in (m.text or "")
                              for word in ["Мова", "Language", "Jazyk"]))
async def language_cmd(message: Message):

    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", DEFAULT_LANG)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Українська 🇺🇦", callback_data="lang_uk")],
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton(text="Slovenčina 🇸🇰", callback_data="lang_sk")],
        [InlineKeyboardButton(text="Deutsch 🇩🇪", callback_data="lang_de")],
        [InlineKeyboardButton(text="日本語 🇯🇵", callback_data="lang_ja")],
    ])
    await message.answer("Оберіть мову / Choose language / Vyber jazyk:",
                         reply_markup=kb)


# ---------------------
# ВІЛЬНИЙ ЧАТ (відповідає на те, що пишуть боту) — повинен бути останнім
# ---------------------


@router.message()
async def chat_with_fortune_bot(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    user = get_user(uid) or {"lang": DEFAULT_LANG}
    lang = user.get("lang", DEFAULT_LANG)

    text = (message.text or "").strip().lower()
    if not text:
        return

    memory = get_memory(uid)

    # 🧠 прості патерни для запам'ятовування
    if text.startswith("мене звати ") or text.startswith(
            "я ") or text.startswith("моє ім'я "):
        name = text.replace("мене звати",
                            "").replace("моє ім'я",
                                        "").replace("я",
                                                    "").strip().capitalize()
        memory["name"] = name
        save_memory(uid, memory)
        await message.answer(f"Приємно познайомитись, {name}! 😊")
        return

    if "люблю" in text:
        fav = text.split("люблю", 1)[1].strip().rstrip(".")
        memory["favorite"] = fav
        save_memory(uid, memory)
        await message.answer(f"О, {fav}? Класний вибір 😋")
        return

    # 🧠 якщо питає щось, що вже знаємо
    if "як мене звати" in text and "name" in memory:
        await message.answer(f"Тебе звати {memory['name']}! 😉")
        return

    if "що я люблю" in text and "favorite" in memory:
        await message.answer(f"Ти казав, що любиш {memory['favorite']} 🍽️")
        return

    # решта — стандартна логіка з OpenRouter
    ai_reply = await generate_openrouter_reply(message.text, lang=lang)
    if ai_reply:
        await message.answer(ai_reply)
    else:
        await message.answer(
            "Ммм... цікаво 🤔 Але я відчуваю, що сьогодні все буде добре!")


@router.callback_query()
async def debug_callback(call: types.CallbackQuery):
    print("🔥 CALLBACK:", call.data)
    await call.answer("✅ Callback received!")


# ---------------------
# ЩОДЕННІ ФУНКЦІЇ / ПЛАНУВАЛЬНИК
# ---------------------


async def daily_reset():
    today = datetime.now().strftime("%Y-%m-%d")
    users = load_users()
    for uid, u in users.items():
        u["date"] = today
        u["motivation_used"] = 0
        u["prediction_used"] = 0
        save_user(uid, u)
    print("✅ Денне оновлення лімітів виконано.")


async def mass_broadcast(text: str):
    """
    Надсилає всім користувачам у базі одне повідомлення.
    """
    users = get_all_users()  # твоя функція, яка повертає список user_id
    sent = 0
    failed = 0

    for i, user_id in enumerate(users, 1):
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception as e:
            print(f"⚠️ Помилка для {user_id}: {e}")
            failed += 1
        if i % 20 == 0:
            await asyncio.sleep(1)  # контроль швидкості

    print(f"✅ Розіслано {sent}, не вдалося {failed}")


async def send_to_user(user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
        print(f"✅ Надіслано користувачу {user_id}")
    except Exception as e:
        print(f"⚠️ Не вдалося надіслати {user_id}: {e}")


async def daily_broadcast():
    users = load_users()
    for uid in users:
        try:
            # надсилаємо мотивацію українською — або локалізувати можна додатково
            await bot.send_message(
                int(uid),
                f"🌞 Новий день — нові можливості!\n{random.choice(MOTIVATION_QUOTES)}"
            )
        except:
            continue


async def scheduler_start():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_reset, "cron", hour=DAILY_HOUR, minute=0)
    scheduler.add_job(daily_broadcast, "cron", hour=DAILY_HOUR, minute=5)
    scheduler.start()
    print("✅ Планувальник запущено")


# ---------------------
# KEEP ALIVE (для Replit)
# ---------------------

app = Flask("keep_alive")


@app.route("/")
def home():
    return "Бот працює 🔮"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# ---------------------
# ЗАПУСК
# ---------------------


async def main():
    print("🤖 Бот запущено!")
    await scheduler_start()  # запускаємо один спільний планувальник
    await dp.start_polling(bot)


if __name__ == "__main__":
    keep_alive()
    try:
        init_db()
        upgrade_db()
    except Exception as e:
        print("⚠️ Помилка ініціалізації БД:", e)
    asyncio.run(main())
