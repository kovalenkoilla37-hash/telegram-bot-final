import os
import re
import threading
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Настройки
TOKEN = os.environ.get("8313231784:AAHjAafo4lU-M7gPrAdcEVfyY5GxeSncLeo
")
ADMIN_CHAT_ID = os.environ.get("-4849060567")
if not TOKEN or not ADMIN_CHAT_ID:
    raise RuntimeError("Set TOKEN and ADMIN_CHAT_ID environment variables")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

# Веб-заглушка для Render
async def handle(request):
    return web.Response(text="OK")

def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle)
    web.run_app(app, host="0.0.0.0", port=port)

threading.Thread(target=start_web_server, daemon=True).start()

# Telegram bot
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

def is_valid_text(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-zА-Яа-я0-9\\s]+", text.strip()))

QUESTIONS = [
    ("name",    "Введите ваше имя (например: Иван):"),
    ("origin",  "Откуда вы? (например: Украина)"),
    ("age",     "Сколько вам лет? (только цифры, например: 18)"),
    ("kd",      "Сколько КД в игре? (только цифры, например: 50)"),
    ("source",  "Откуда узнали о нас? (например: Discord, друг)"),
    ("social",  "Насколько вы общительный человек? (например: очень общительный)"),
    ("modes",   "В какие режимы больше играете? (например: TDM, Метро, Классика)")
]

sessions = {}
completed = set()

@dp.message_handler(commands=["start", "анкета"])
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    if uid in completed:
        await message.reply("Вы уже отправили заявку.")
        return
    sessions[uid] = {"step": 0, "data": {}}
    await message.reply("Начнем анкету. Отвечайте только текстом (буквы/цифры).")
    await message.reply(QUESTIONS[0][1])

@dp.message_handler()
async def handle_message(message: types.Message):
    uid = message.from_user.id
    if uid not in sessions:
        await message.reply("Напишите /start или /анкета чтобы начать.")
        return

    state = sessions[uid]
    step = state["step"]
    key, prompt = QUESTIONS[step]

    text = message.text.strip()
    if key in ("age", "kd"):
        if not text.isdigit():
            await message.reply("Введите только цифры.")
            return
    else:
        if not is_valid_text(text):
            await message.reply("Допустимы только буквы, цифры и пробелы.")
            return

    state["data"][key] = text
    state["step"] += 1

    if state["step"] < len(QUESTIONS):
        await message.reply(QUESTIONS[state["step"]][1])
    else:
        if not message.from_user.username:
            await message.reply("Для завершения анкеты нужен Telegram username. Установите его в настройках и начните заново.")
            del sessions[uid]
            return

        data = state["data"]
        summary = f"""Новая заявка:
Имя: {data.get('name')}
Откуда: {data.get('origin')}
Возраст: {data.get('age')}
КД: {data.get('kd')}
Откуда узнал: {data.get('source')}
Общительность: {data.get('social')}
Режимы: {data.get('modes')}
Пользователь: @{message.from_user.username}"""
        await bot.send_message(ADMIN_CHAT_ID, summary, parse_mode="Markdown")
        await message.reply("Ваша заявка отправлена! Спасибо.")
        completed.add(uid)
        del sessions[uid]

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
