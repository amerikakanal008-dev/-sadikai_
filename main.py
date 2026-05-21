import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
import os
from flask import Flask
from threading import Thread

TOKEN = "8086061724:AAFNorWcbL71wKBYKecJQ-yaA60Sy6sIsAo"
bot = telebot.TeleBot(TOKEN)

user_images = {}
user_pdf_names = {}
app = Flask('')

@app.route('/')
def home():
    return "Bot onlayn!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_images[message.chat.id] = []
    bot.reply_to(message, "Salom! Menga bir nechta rasm yuboring va pastdagi tugmani bosing!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if chat_id not in user_images:
        user_images[chat_id] = []
        
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    file_name = f"img_{chat_id}_{len(user_images[chat_id])}.jpg"
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
        
    user_images[chat_id].append(file_name)
    
    markup = InlineKeyboardMarkup()
    btn_convert = InlineKeyboardButton("📄 PDF yaratish", callback_data="convert_pdf")
    btn_clear = InlineKeyboardButton("❌ Tozalash", callback_data="clear_images")
    markup.add(btn_convert, btn_clear)
    
    bot.reply_to(message, f"Rasm keldi! Jami: {len(user_images[chat_id])} ta.\nPDF qilish uchun bosing 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    
    if call.data == "convert_pdf":
        if chat_id not in user_images or len(user_images[chat_id]) == 0:
            bot.answer_callback_query(call.id, "Rasm yo'q!")
            return
            
        bot.answer_callback_query(call.id, "Ism kutilmoqda...")
        # Foydalanuvchidan nom so'rash
        msg = bot.send_message(chat_id, "✍️ PDF faylga nima deb nom beramiz? (Faqat nomini yozib yuboring):")
        bot.register_next_step_handler(msg, process_pdf_name)
            
    elif call.data == "clear_images":
        if chat_id in user_images:
            for img_path in user_images[chat_id]:
                if os.path.exists(img_path): os.remove(img_path)
            user_images[chat_id] = []
        bot.answer_callback_query(call.id, "Tozalandi.")

def process_pdf_name(message):
    chat_id = message.chat.id
    pdf_name = message.text.strip()
    
    # Belgilarni tekshirish (fayl nomida taqiqlangan belgilarni o'chirish)
    for char in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>']:
        pdf_name = pdf_name.replace(char, '')
        
    if not pdf_name:
        pdf_name = f"fayl_{chat_id}"
        
    bot.send_message(chat_id, f"Clfayl nomi: {pdf_name}.pdf\nPDF tayyorlanmoqda... ⏳")
    
    pdf_path = f"{pdf_name}.pdf"
    images_list = []
    
    try:
        for img_path in user_images[chat_id]:
            img = Image.open(img_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images_list.append(img)
            
        if images_list:
            images_list[0].save(pdf_path, save_all=True, append_images=images_list[1:])
            with open(pdf_path, 'rb') as pdf_file:
                bot.send_document(chat_id, pdf_file, caption=f"Tayyor! 🎉\n📄 Fayl nomi: {pdf_name}.pdf")
                
        # Tozalash
        for img_path in user_images[chat_id]:
            if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        user_images[chat_id] = []
        
    except Exception as e:
        bot.send_message(chat_id, "Xatolik bo'ldi. Qaytadan urinib ko'ring.")
        if os.path.exists(pdf_path): os.remove(pdf_path)
        user_images[chat_id] = []

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
