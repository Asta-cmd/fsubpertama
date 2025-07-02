import os
import openai
from pyrogram import Client, filters
from dotenv import load_dotenv
from datetime import datetime
from pyrogram.enums import ChatAction

# 🔄 Load .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# 🧠 Mode user
user_modes = {}  # {user_id: 'sopan' or 'ngerocos'}

# 📝 Log ke file
def log_user(user, text):
    try:
        with open("log.txt", "a") as f:
            f.write(f"[{datetime.now()}] {user.id} - {user.username}: {text}\n")
    except:
        pass

# ▶️ Inisialisasi bot
bot = Client("ai-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🔁 Perintah ganti mode
@bot.on_message(filters.command("mode") & filters.private)
async def set_mode(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Contoh: /mode ngerocos atau /mode sopan")
        return

    mode = args[1].lower()
    if mode not in ["sopan", "ngerocos"]:
        await message.reply("Mode tidak dikenali. Pilih: sopan atau ngerocos.")
        return

    user_modes[message.from_user.id] = mode
    await message.reply(f"✅ Mode kamu sekarang: **{mode}**")

# 🤖 Auto-reply AI
@bot.on_message(filters.private & filters.text & ~filters.command("mode"))
async def auto_reply(client, message):
    user = message.from_user
    prompt = message.text
    mode = user_modes.get(user.id, "sopan")  # default sopan

    log_user(user, prompt)
    await message.reply_chat_action(ChatAction.TYPING)

    # Pilih prompt berdasarkan mode
    if mode == "sopan":
        system_prompt = "Kamu adalah asisten AI yang sopan, membantu, dan ramah."
    elif mode == "ngerocos":
        system_prompt = (
            "Kamu adalah AI blak-blakan, frontal, ceplas-ceplos, kadang kasar dan bercanda. "
            "Jangan terlalu sopan, jawab seperti manusia dewasa yang nyablak dan cuek."
        )
    else:
        system_prompt = "Kamu adalah asisten AI yang netral dan membantu."

    # Kirim ke OpenAI
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        reply = res["choices"][0]["message"]["content"]
        await message.reply(reply)
    except Exception as e:
        await message.reply(f"❌ Error dari AI:\n`{str(e)}`")

# ▶️ Jalankan
bot.run()
        
