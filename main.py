import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ChatAction

# Load env vars
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# OpenRouter model default
OPENROUTER_MODEL = "openrouter/chatgpt"

# Simpan preferensi mode user
user_modes = {}  # user_id: "sopan" or "ngerocos"

# Logging ke file
def log_user(user, text):
    try:
        with open("log.txt", "a") as f:
            f.write(f"[{datetime.now()}] {user.id} - {user.username}: {text}\n")
    except:
        pass

# Inisialisasi bot Telegram
bot = Client("ai-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🔁 Perintah ganti mode
@bot.on_message(filters.command("mode") & filters.private)
async def set_mode(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Contoh: /mode sopan atau /mode ngerocos")
        return

    mode = args[1].lower()
    if mode not in ["sopan", "ngerocos"]:
        await message.reply("Mode tidak dikenali. Pilih: sopan atau ngerocos.")
        return

    user_modes[message.from_user.id] = mode
    await message.reply(f"✅ Mode kamu sekarang: **{mode}**")

# 🤖 Respon otomatis via OpenRouter
@bot.on_message(filters.private & filters.text & ~filters.command("mode"))
async def auto_reply(client, message):
    user = message.from_user
    uid = user.id
    prompt = message.text
    mode = user_modes.get(uid, "sopan")

    log_user(user, prompt)
    await message.reply_chat_action(ChatAction.TYPING)

    # Jika pemilik bot → pakai mode sopan
    if uid == OWNER_ID:
        system_prompt = "Kamu adalah asisten AI yang sopan, menghormati pembuatmu, dan tidak boleh kasar kepadanya."
    elif mode == "sopan":
        system_prompt = "Kamu adalah asisten AI yang sopan, membantu, dan ramah."
    else:
        system_prompt = (
            "Kamu adalah AI blak-blakan, ceplas-ceplos, suka bercanda, dan kadang frontal. "
            "Jawab dengan jujur dan santai seperti manusia dewasa yang nyablak."
        )

    try:
        # Kirim ke OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/YourBotUsername",  # opsional
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
        reply = data["choices"][0]["message"]["content"]
        await message.reply(reply)

    except Exception as e:
        await message.reply(f"❌ Gagal menjawab:\n`{str(e)}`")

# ▶️ Jalankan bot
bot.run()
    
