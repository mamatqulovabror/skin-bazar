import asyncio
import os
import json
import time
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from database import create_db, save_user, get_stats, get_all_users

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://skin-bazar-production.up.railway.app")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "746409702"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    save_user(message.from_user.id, message.from_user.username or "")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Open Skin Bazar", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])
    await message.answer("Welcome to Skin Bazar!", reply_markup=keyboard)

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("No access.")
        return
    total, online = get_stats()
    users = get_all_users()
    import datetime
    lines = ["ADMIN PANEL", "Jami: " + str(total), "Online: " + str(online), ""]
    for u in users[:20]:
        uid, uname, first_seen, last_seen = u
        uname_str = "@" + uname if uname else "ID:" + str(uid)
        last = datetime.datetime.fromtimestamp(last_seen).strftime("%d.%m %H:%M")
        status = "online" if (int(time.time()) - last_seen) < 300 else "offline"
        lines.append(status + " " + uname_str + " | " + last)
    await message.answer("\n".join(lines))

async def handle_index(request):
    import pathlib
    index_path = pathlib.Path(__file__).parent / "webapp" / "index.html"
    return web.FileResponse(index_path)

async def handle_stats(request):
    total, online = get_stats()
    return web.Response(
        text=json.dumps({"total": total, "online": online}),
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )

async def run_web():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/index.html", handle_index)
    app.router.add_get("/api/stats", handle_stats)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print("Web server started on port " + str(port))

async def run_bot():
    while True:
        try:
            print("Bot polling started...")
            await dp.start_polling(bot, allowed_updates=["message"])
        except Exception as e:
            print("Polling error: " + str(e) + ", retry in 5s...")
            await asyncio.sleep(5)

async def main():
    create_db()
    await asyncio.gather(run_web(), run_bot())

if __name__ == "__main__":
    asyncio.run(main())
