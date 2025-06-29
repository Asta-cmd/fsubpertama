# 🤖 Telegram Bot: FSUB + Menfess

Bot Telegram yang hanya mengizinkan pengguna mengirim pesan anonim (menfess) ke channel jika sudah bergabung ke channel tertentu (force subscribe).

---

## ✅ Fitur
- Wajib join channel (@asupanmenfesmu2)
- Menfess anonim ke channel tujuan (@tarothasupan)
- Tanpa webhook (gunakan polling)

---

## 🚀 Cara Deploy di Railway

1. **Fork repo ini** atau upload ke GitHub
2. Masuk ke [https://railway.app](https://railway.app)
3. Klik `New Project` → `Deploy from GitHub`
4. Tambahkan Environment Variables berikut:

```env
API_ID=24946786
API_HASH=a7bb54f7f9cb222294e85803b395c7fb
BOT_TOKEN=7979742075:AAF3yyPO0KBdLTSgjeG7LGJWQ859masX0Ek
CHANNEL_FSUB=@asupanmenfesmu2
CHANNEL_TARGET=@tarothasupan
