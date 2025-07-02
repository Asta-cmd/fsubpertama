import asyncio
import logging
import aiohttp
import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message

# === LOAD ENV ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("MODEL", "mixtral-8x7b-32768")

# === VARIABEL GLOBAL ===
BOT_ON = True
MODE = "cool"

# === SETUP LOGGER DAN BOT ===
logging.basicConfig(level=logging.INFO)
bot = Client("autoreply_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# === FUNSI AI GROQ ===
async def get_groq_reply(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            res = await resp.json()
            return res["choices"][0]["message"]["content"]

# === PROMPT PER MODE ===
def build_prompt(mode, user_message, is_owner=False):
    if mode == "sopan":
        return f"Kamu adalah asisten yang sangat sopan dan ramah. Balas ini dengan hormat:\n\n{user_message}"
    elif mode == "marah":
        return f"Balas pesan ini dengan gaya marah dan frontal:\n\n{user_message}"
    elif mode == "cool":
        return f"Balas dengan gaya santai dan kalem, sedikit nyentrik:\n\n{user_message}"
    elif mode == "drytext":
        return f"Balas pesan ini dengan singkat, kaku, dan datar:\n\n{user_message}"
    elif mode == "jaim":
        return f"Balas dengan gaya menjaga image, terkesan baik, rapi, dan profesional:\n\n{user_message}"
    else:
        return user_message

# === HANDLER REPLY PESAN (HANYA SAAT DI-REPLY) ===
@bot.on_message(filters.reply & filters.private)
async def handle_reply(client: Client, message: Message):
    print(">> Ada pesan REPLY masuk")
    print(">> Dari user ID:", message.from_user.id)
    print(">> ID yang dibalas:", message.reply_to_message.from_user.id)

    bot_id = (await client.get_me()).id
    print(">> ID bot:", bot_id)

    if not BOT_ON:
        print(">> Bot sedang OFF")
        return

    if message.reply_to_message.from_user.id != bot_id:
        print(">> Bukan membalas pesan dari bot. Diabaikan.")
        return

    is_owner = message.from_user.id == OWNER_ID
    mode = "sopan" if MODE == "sopan" and is_owner else MODE

    prompt = build_prompt(mode, message.text, is_owner)

    try:
        await message.chat.send_chat_action("typing")
        reply = await get_groq_reply(prompt)
        await message.reply_text(reply)
    except Exception as e:
        print(">> Error saat panggil AI:", e)
        await message.reply_text("❌ Gagal memproses pesan.")

# === ON / OFF HANYA UNTUK OWNER ===
@bot.on_message(filters.command("on") & filters.user(OWNER_ID))
async def turn_on(client, message):
    global BOT_ON
    BOT_ON = True
    print(">> Bot dihidupkan oleh owner.")
    await message.reply("✅ Bot diaktifkan.")

@bot.on_message(filters.command("off") & filters.user(OWNER_ID))
async def turn_off(client, message):
    global BOT_ON
    BOT_ON = False
    print(">> Bot dimatikan oleh owner.")
    await message.reply("🛑 Bot dinonaktifkan.")

# === GANTI MODE ===
@bot.on_message(filters.command("mode") & filters.user(OWNER_ID))
async def set_mode(client, message):
    global MODE
    if len(message.command) < 2:
        return await message.reply("Gunakan: `/mode [sopan|marah|cool|drytext|jaim]`")

    mode = message.command[1].lower()
    if mode in ["sopan", "marah", "cool", "drytext", "jaim"]:
        MODE = mode
        print(f">> Mode diubah ke: {mode}")
        await message.reply(f"✅ Mode diubah ke: {mode}")
    else:
        await message.reply("❌ Mode tidak dikenal.")

# === BROADCAST REPLY PESAN ===
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply pesan yang ingin dikirim ke semua user.")

    broadcast_text = message.reply_to_message.text
    count = 0
    async for dialog in bot.iter_dialogs():
        try:
            await bot.send_message(dialog.chat.id, broadcast_text)
            count += 1
            await asyncio.sleep(0.3)
        except:
            continue
    await message.reply(f"📣 Broadcast selesai ke {count} pengguna.")

# === DEBUG SEMUA PESAN MASUK ===
@bot.on_message(filters.all)
async def debug_all(client, message):
    print(">> Pesan masuk:", message.text)

# === JALANKAN BOT ===
bot.run()
    
