import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men YouTube va Instagram video/audio yuklovchi botman!\n\n"
        "📎 YouTube yoki Instagram linkini yuboring!"
    )

# Link qabul qilish
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtube.com" in url or "youtu.be" in url or "instagram.com" in url:
        keyboard = [
            [
                InlineKeyboardButton("🎬 MP4 (Video)", callback_data=f"mp4|{url}"),
                InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"mp3|{url}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📥 Qaysi formatda yuklab olmoqchisiz?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("❌ Iltimos, YouTube yoki Instagram linki yuboring!")

# Yuklab olish
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    fmt, url = query.data.split("|", 1)
    await query.edit_message_text("⏳ Yuklanmoqda, iltimos kuting...")

    try:
        if fmt == "mp4":
            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": "/tmp/%(title)s.%(ext)s",
            }
        else:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "/tmp/%(title)s.%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if fmt == "mp4":
                file_path = ydl.prepare_filename(info)
            else:
                file_path = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"

        await query.edit_message_text("📤 Yuborilmoqda...")

        if fmt == "mp4":
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=open(file_path, "rb"),
                caption="✅ Mana videongiz!"
            )
        else:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=open(file_path, "rb"),
                caption="✅ Mana audongiz!"
            )

        os.remove(file_path)

    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(download))
    app.run_polling()

if __name__ == "__main__":
    main()
