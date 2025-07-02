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
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"  # Model gratis yang aman

user_modes = {}

def log_user(user, text):
    try:
        with open("log.txt", "a") as f:
            f.write(f"[{datetime.now()}] {user.id} - {user.username}: {text}\n")
    except:
        pass

bot = Client("ai-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

@bot.on_message(filters.private & filters.text & ~filters.command("mode"))
async def auto_reply(client, message):
    user = message.from_user
    uid = user.id
    prompt = message.text
    mode = user_modes.get(uid, "sopan")

    log_user(user, prompt)
    await message.reply_chat_action(ChatAction.TYPING)

    # Gunakan sistem prompt yang sesuai
    if uid == OWNER_ID:
        system_prompt = "Kamu adalah asisten AI yang sopan dan menghormati pemilik bot ini."
    elif mode == "sopan":
        system_prompt = "Kamu adalah asisten AI yang sopan, membantu, dan ramah."
    else:
        system_prompt = (
            "Kamu adalah AI yang blak-blakan, ceplas-ceplos, kadang frontal dan suka bercanda. "
            "Jawab dengan gaya manusia dewasa yang nyablak dan jujur."
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

        # DEBUG LOGGING
        if "choices" not in data:
            await message.reply(f"❌ Gagal menjawab:\nOpenRouter response:\n`{data}`")
            return

        reply = data["choices"][0]["message"]["content"]
        await message.reply(reply)

    except Exception as e:
        await message.reply(f"❌ Exception:\n`{str(e)}`")

bot.run()
    
