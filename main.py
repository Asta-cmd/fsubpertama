import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ChatAction

# Load .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"

user_modes = {}
bot_enabled = True  # Global toggle ON/OFF

def log_user(user, text):
    try:
        with open("log.txt", "a") as f:
            f.write(f"[{datetime.now()}] {user.id} - {user.username}: {text}\n")
    except:
        pass

bot = Client("ai-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🔘 ON/OFF CONTROL (OWNER ONLY)
@bot.on_message(filters.command("bot") & filters.user(OWNER_ID))
async def toggle_bot(client, message):
    global bot_enabled
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Ketik `/bot on` atau `/bot off`")
        return

    cmd = args[1].lower()
    if cmd == "on":
        bot_enabled = True
        await message.reply("✅ Bot diaktifkan.")
    elif cmd == "off":
        bot_enabled = False
        await message.reply("🛑 Bot dimatikan sementara.")
    else:
        await message.reply("❌ Gunakan `/bot on` atau `/bot off`")

# 🔁 /mode sopan / ngerocos
@bot.on_message(filters.command("mode") & filters.private)
async def set_mode(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Contoh: /mode sopan atau /mode ngerocos")
        return
    mode = args[1].lower()
    if mode not in ["sopan", "ngerocos"]:
        await message.reply("Mode tidak dikenali. Gunakan: sopan atau ngerocos.")
        return
    user_modes[message.from_user.id] = mode
    await message.reply(f"✅ Mode kamu sekarang: **{mode}**")

# 🤖 PRIVATE
@bot.on_message(filters.private & filters.text & ~filters.command(["mode", "bot"]))
async def auto_reply(client, message):
    global bot_enabled
    if not bot_enabled:
        return

    user = message.from_user
    uid = user.id
    prompt = message.text
    mode = user_modes.get(uid, "sopan")

    log_user(user, prompt)
    await message.reply_chat_action(ChatAction.TYPING)

    if uid == OWNER_ID:
        system_prompt = "Kamu adalah AI yang sopan dan menghormati pemilik bot ini. Jawab singkat dan ramah."
    elif mode == "sopan":
        system_prompt = "Kamu adalah AI sopan, membantu, dan ramah. Jawablah dengan singkat dan to the point."
    else:
        system_prompt = (
            "Kamu adalah AI blak-blakan, ceplas-ceplos, dan suka marah-marah. "
            "Jawab nyolot dan tidak sopan, tapi tetap singkat dan jelas."
        )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=30
        )

        data = response.json()
        if "choices" not in data:
            await message.reply(f"❌ Gagal:\n`{data}`")
            return

        reply = data["choices"][0]["message"]["content"]
        await message.reply(reply)

    except Exception as e:
        await message.reply(f"❌ Error:\n`{str(e)}`")

# 💬 GRUP — Balas semua teks
@bot.on_message(filters.group & filters.text)
async def auto_group_reply(client, message):
    global bot_enabled
    if not bot_enabled:
        return

    prompt = message.text
    await message.reply_chat_action(ChatAction.TYPING)

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": "Kamu adalah AI grup yang singkat, pintar, dan to the point. Jawab setiap pesan yang masuk secara jelas dan ringkas."},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=30
        )

        data = response.json()
        if "choices" not in data:
            await message.reply(f"❌ Gagal:\n`{data}`")
            return

        reply = data["choices"][0]["message"]["content"]
        await message.reply(reply)

    except Exception as e:
        await message.reply(f"❌ Error:\n`{str(e)}`")

# ▶️ Jalankan
bot.run()
    
