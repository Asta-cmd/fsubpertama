import logging
import os
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
import aiohttp

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Global states
bot_enabled = True
bot_mode = "sopan"  # default mode

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MODE TEMPLATES
PROMPT_TEMPLATE = {
    "sopan": "Balas pesan ini dengan sopan dan informatif:\n{msg}",
    "cool": "Balas dengan gaya santai, agak cuek, tapi tetap menjawab:\n{msg}",
    "marah": "Balas dengan nada marah, frontal, dan sedikit kasar tapi masih menjawab:\n{msg}"
}

# === GROQ API CALL ===
async def chat_with_groq(prompt: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data['choices'][0]['message']['content']
            else:
                return "Maaf, ada kesalahan saat menghubungi AI."

# === HANDLERS ===
async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled, bot_mode
    if not bot_enabled:
        return

    if update.message and update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            user_input = update.message.text
            prompt = PROMPT_TEMPLATE[bot_mode].format(msg=user_input)
            await update.message.chat.send_action("typing")
            response = await chat_with_groq(prompt)
            await update.message.reply_text(response)

async def toggle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Hanya owner yang bisa menggunakan perintah ini.")
    bot_enabled = not bot_enabled
    status = "aktif ✅" if bot_enabled else "nonaktif ❌"
    await update.message.reply_text(f"Bot sekarang dalam status: {status}")

async def mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_mode
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Hanya owner yang bisa mengubah mode.")
    if not context.args:
        return await update.message.reply_text("Gunakan: /mode [sopan|cool|marah]")
    mode = context.args[0].lower()
    if mode in PROMPT_TEMPLATE:
        bot_mode = mode
        await update.message.reply_text(f"Mode diubah ke: {bot_mode}")
    else:
        await update.message.reply_text("Mode tidak dikenal. Gunakan: sopan, cool, atau marah")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Hanya owner yang bisa menggunakan broadcast.")
    msg = ' '.join(context.args)
    if not msg:
        return await update.message.reply_text("Gunakan: /broadcast <pesan>")
    
    sent_count = 0
    async for dialog in context.bot.get_dialogs():
        try:
            await context.bot.send_message(chat_id=dialog.chat.id, text=msg)
            sent_count += 1
        except:
            continue
    await update.message.reply_text(f"Broadcast terkirim ke {sent_count} chat.")

# === MAIN ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("toggle", toggle_handler))
    app.add_handler(CommandHandler("mode", mode_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reply_handler))

    print("Bot is running...")
    app.run_polling()
                
