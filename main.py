import os
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from openai import OpenAI

# Load .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID"))

client_ai = OpenAI(api_key=OPENAI_API_KEY)
user_modes = {}  # user_id: mode

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
        await message.reply("Mode tidak dikenali. Gunakan: sopan atau ngerocos.")
        return

    user_modes[message.from_user.id] = mode
    await message.reply(f"✅ Mode kamu sekarang: **{mode}**")

@bot.on_message(filters.private & filters.text & ~filters.command("mode"))
async def auto_reply(client, message):
    user = message.from_user
    prompt = message.text
    uid = user.id
    mode = user_modes.get(uid, "sopan")

    log_user(user, prompt)
    await message.reply_chat_action(ChatAction.TYPING)

    # Owner override: selalu pakai sopan
    if uid == OWNER_ID:
        system_prompt = "Kamu adalah asisten AI yang sopan, perhatian, dan tidak boleh kasar terhadap pembuatmu."
    elif mode == "sopan":
        system_prompt = "Kamu adalah asisten AI yang sopan, membantu, dan ramah."
    elif mode == "ngerocos":
        system_prompt = (
            "Kamu adalah AI blak-blakan, frontal, ceplas-ceplos, suka bercanda, kadang kasar. "
            "Jawab seperti manusia dewasa yang nyablak dan cuek. Jangan terlalu sopan."
        )
    else:
        system_prompt = "Kamu adalah AI netral."

    try:
        res = client_ai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        reply = res.choices[0].message.content
        await message.reply(reply)
    except Exception as e:
        await message.reply(f"❌ Gagal menjawab:\n`{e}`")

bot.run()
    
