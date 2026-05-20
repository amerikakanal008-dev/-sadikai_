import io
import telebot
from PIL import Image
from flask import Flask
from threading import Thread

# 1. Telegram Bot qismi
API_TOKEN = '8086061724:AAFNorWcbL71wKBYKecJQ-yaA60Sy6sIsAo'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Bot onlayn rejimda ishlayapti! Menga rasm yuboring. 📄")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        status_msg = bot.reply_to(message, "PDF tayyorlanmoqda... ⏳")
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_stream = io.BytesIO(downloaded_file)
        img = Image.open(image_stream)
        img_converted = img.convert('RGB')
        
        pdf_stream = io.BytesIO()
        img_converted.save(pdf_stream, "PDF")
        pdf_stream.seek(0)
        pdf_stream.name = f"hujjat_{message.from_user.id}.pdf"
        
        bot.send_document(message.chat.id, pdf_stream, caption="Sizning PDF faylingiz! ✅")
        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"Xatolik: {str(e)}")

# 2. Server uchun Flask qismi (Render o'chirib qo'ymasligi uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot tirik va ishlayapti!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

if __name__ == "__main__":
    keep_alive() # Veb-serverni ishga tushirish
    print("Bot server rejimida yonmoqda...")
    bot.infinity_polling()
  
