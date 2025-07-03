import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)
import aiohttp

# Load .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

# Global state
bot_enabled = True
bot_mode = "sopan"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = {
    "sopan": "Balas dengan sopan:\n{msg}",
    "cool": "Balas dengan santai:\n{msg}",
    "marah": "Balas dengan nada marah:\n{msg}"
}

async def chat_with_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
            return "❌ Terjadi kesalahan saat menghubungi AI."

async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled, bot_mode
    if not bot_enabled:
        return
    msg = update.message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
        prompt = PROMPT_TEMPLATE[bot_mode].format(msg=msg.text)
        await msg.chat.send_action("typing")
        response = await chat_with_groq(prompt)
        await msg.reply_text(response)

async def toggle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Hanya owner yang boleh.")
    bot_enabled = not bot_enabled
    status = "aktif ✅" if bot_enabled else "nonaktif ❌"
    await update.message.reply_text(f"Bot sekarang dalam status: {status}")

async def mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_mode
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Hanya owner.")
    if not context.args:
        return await update.message.reply_text("Gunakan: /mode [sopan|cool|marah]")
    mode = context.args[0].lower()
    if mode in PROMPT_TEMPLATE:
        bot_mode = mode
        await update.message.reply_text(f"Mode diubah ke: {bot_mode}")
    else:
        await update.message.reply_text("Mode tidak dikenal.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("toggle", toggle_handler))
    app.add_handler(CommandHandler("mode", mode_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reply_handler))
    print("Bot aktif.")
    app.run_polling()
