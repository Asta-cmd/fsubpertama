import os
import sys
import logging
import requests
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Konfigurasi ENV
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = os.environ.get("GROQ_MODEL", "mixtral-8x7b-32768")

# Status & Mode AI
active = True
ai_mode = "kalem"
chats = set()

logging.basicConfig(level=logging.INFO)

# Gaya balasan AI
def generate_prompt(user_msg: str) -> str:
    styles = {
        "kalem": f"Balas pesan ini dengan sopan dan tenang:\n{user_msg}",
        "marah": f"Balas dengan kasar, frontal, dan tidak ramah:\n{user_msg}",
        "ngeselin": f"Balas dengan gaya nyebelin, sarkas, menyindir:\n{user_msg}",
        "drytext": f"Balas dengan cuek, singkat, tanpa basa-basi:\n{user_msg}",
    }
    return styles.get(ai_mode, user_msg)

# Fungsi ke Groq (sync)
def ask_groq_sync(message: str, sender_id: int) -> str:
    if sender_id == OWNER_ID:
        prompt = (
            "Mohon balas dengan tutur kata yang sangat sopan dan penuh hormat, "
            "seakan-akan Anda sedang berbicara kepada Raja yang mulia:\n"
            f"{message}"
        )
    else:
        prompt = generate_prompt(message)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": GROQ_MODEL
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()

# Respon pesan (reply ke bot saja)
async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active
    msg = update.message
    if not active or not msg or not msg.text:
        return

    sender_id = update.effective_user.id
    chat_type = msg.chat.type

    if chat_type in ["group", "supergroup"]:
        if not msg.reply_to_message or msg.reply_to_message.from_user.id != context.bot.id:
            return

    await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
    try:
        response = await context.application.run_in_executor(None, ask_groq_sync, msg.text, sender_id)
        await msg.reply_text(response)
        chats.add(msg.chat_id)
    except Exception:
        await msg.reply_text("❌ Bot gagal membalas.")

# /mode command
async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_mode
    if update.effective_user.id != OWNER_ID:
        return
    if context.args:
        new_mode = context.args[0].lower()
        if new_mode in ["kalem", "marah", "ngeselin", "drytext"]:
            ai_mode = new_mode
            await update.message.reply_text(f"✅ Mode diubah ke: {ai_mode}")
        else:
            await update.message.reply_text("❌ Mode tidak dikenal.")
    else:
        await update.message.reply_text("Gunakan: /mode <kalem|marah|ngeselin|drytext>")

# /broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("❌ Masukkan isi pesan.")
    count = 0
    for chat_id in chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ Broadcast dikirim ke {count} chat.")

# /on & /off
async def turn_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active
    if update.effective_user.id == OWNER_ID:
        active = True
        await update.message.reply_text("✅ Bot diaktifkan.")

async def turn_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active
    if update.effective_user.id == OWNER_ID:
        active = False
        await update.message.reply_text("🛑 Bot dinonaktifkan.")

# /restart
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("🔄 Restarting bot...")
        sys.exit(0)

# Run polling
def run():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("on", turn_on))
    app.add_handler(CommandHandler("off", turn_off))
    app.add_handler(CommandHandler("restart", restart_bot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_handler))

    print("🚀 Bot aktif dalam mode polling.")
    app.run_polling()

if __name__ == "__main__":
    run()
    
