import os
import logging
import httpx
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Konfigurasi
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = os.environ.get("GROQ_MODEL", "mixtral-8x7b-32768")
WEBHOOK = os.environ["WEBHOOK"]
PORT = int(os.environ.get("PORT", 8080))

# Status & mode
active = True
ai_mode = "kalem"
chats = set()

logging.basicConfig(level=logging.INFO)

# Gaya mode umum
def generate_prompt(user_msg: str) -> str:
    styles = {
        "kalem": f"Balas pesan ini dengan sopan dan tenang:\n{user_msg}",
        "marah": f"Balas dengan kasar, frontal, dan tidak ramah:\n{user_msg}",
        "ngeselin": f"Balas dengan gaya nyebelin, sarkas, menyindir:\n{user_msg}",
        "drytext": f"Balas dengan cuek, singkat, tanpa basa-basi:\n{user_msg}",
    }
    return styles.get(ai_mode, user_msg)

# Request ke Groq
async def ask_groq(message: str, sender_id: int) -> str:
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

    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

# Respon otomatis (hanya jika reply ke bot)
async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active
    if not active:
        return
    msg = update.message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
        user_input = msg.text
        sender_id = update.effective_user.id
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        try:
            response = await ask_groq(user_input, sender_id)
            await msg.reply_text(response)
            chats.add(msg.chat_id)
        except Exception as e:
            await msg.reply_text("❌ Bot gagal membalas.")

# Perintah: /mode
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

# Perintah: /broadcast
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

# Perintah: /on dan /off
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

# Main Webhook
def run():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("on", turn_on))
    app.add_handler(CommandHandler("off", turn_off))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_handler))

    print(f"🔗 Webhook aktif di port {PORT}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK
    )

if __name__ == "__main__":
    run()
    
