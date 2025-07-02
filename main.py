import asyncio
import logging
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# === KONFIGURASI ===
BOT_TOKEN = "ISI_BOT_TOKEN_KAMU"
API_ID = 12345678
API_HASH = "ISI_API_HASH_KAMU"
OWNER_ID = 123456789  # Ganti dengan ID Telegram kamu
GROQ_API_KEY = "ISI_GROQ_API_KEY_KAMU"
MODEL = "mixtral-8x7b-32768"

# === VARIABEL GLOBAL ===
BOT_ON = True
MODE = "cool"  # default mode

# === SETUP LOGGER DAN BOT ===
logging.basicConfig(level=logging.INFO)
bot = Client("autoreply_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# === FUNGSI GROQ CHAT ===
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

# === FORMAT PROMPT BERDASARKAN MODE ===
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

# === HANYA BALAS KETIKA DI-REPLY ===
@bot.on_message(filters.reply & filters.private)
async def handle_reply(client: Client, message: Message):
    global BOT_ON, MODE
    if not BOT_ON:
        return

    # Hanya respon jika balasannya untuk bot
    if message.reply_to_message.from_user.id != (await client.get_me()).id:
        return

    # Tentukan apakah user adalah owner
    is_owner = message.from_user.id == OWNER_ID

    # Gunakan mode sopan hanya untuk owner
    mode = "sopan" if MODE == "sopan" and is_owner else MODE

    prompt = build_prompt(mode, message.text, is_owner)
    try:
        await message.chat.action.send_chat_action("typing")
        reply = await get_groq_reply(prompt)
        await message.reply_text(reply)
    except Exception as e:
        await message.reply_text("❌ Gagal memproses pesan.")

# === HANYA OWNER: TOGGLE ON/OFF ===
@bot.on_message(filters.command("on") & filters.user(OWNER_ID))
async def turn_on(client, message):
    global BOT_ON
    BOT_ON = True
    await message.reply("✅ Bot diaktifkan.")

@bot.on_message(filters.command("off") & filters.user(OWNER_ID))
async def turn_off(client, message):
    global BOT_ON
    BOT_ON = False
    await message.reply("🛑 Bot dinonaktifkan.")

# === HANYA OWNER: GANTI MODE ===
@bot.on_message(filters.command("mode") & filters.user(OWNER_ID))
async def set_mode(client, message):
    global MODE
    if len(message.command) < 2:
        return await message.reply("Gunakan: `/mode [sopan|marah|cool|drytext|jaim]`")

    mode = message.command[1].lower()
    if mode in ["sopan", "marah", "cool", "drytext", "jaim"]:
        MODE = mode
        await message.reply(f"✅ Mode diubah ke: {mode}")
    else:
        await message.reply("❌ Mode tidak dikenal.")

# === HANYA OWNER: BROADCAST ===
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

# === JALANKAN BOT ===
bot.run()
        
