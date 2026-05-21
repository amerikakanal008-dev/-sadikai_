import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
import os
from flask import Flask
from threading import Thread

# Bot tokenini shu yerga yozing
TOKEN = "7727181515:AAFYCby9Y6_b-O0v6R3e4X1zD8-VIsbZtms" # O'zingizning bot tokenigizni o'zgartirmasdan qoldiring
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchilarning rasmlarini vaqtincha saqlash uchun lug'at
user_images = {}

# Render uchun oddiy Web Server (o'chib qolmasligi uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot onlayn rejimda ishlamoqda!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# /start buyrug'i
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_images[message.chat.id] = [] # Rasmlar ro'yxatini tozalash
    bot.reply_to(message, "Salom! Men rasmlarni bitta PDF faylga jamlab beruvchi botman. 📸\n\n"
                          "Menga bitta yoki ketma-ket bir nechta rasm yuboring, so'ng pastdagi tugmani bosing!")

# Rasm qabul qilish xandleri
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    
    # Agar foydalanuvchi ro'yxati ochilmagan bo'lsa, ochamiz
    if chat_id not in user_images:
        user_images[chat_id] = []
        
    # Rasmni eng yuqori sifatda yuklab olish
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Rasmni vaqtincha saqlash
    file_name = f"img_{chat_id}_{len(user_images[chat_id])}.jpg"
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
        
    user_images[chat_id].append(file_name)
    
    # Tugmalarni yaratish
    markup = InlineKeyboardMarkup()
    btn_convert = InlineKeyboardButton("📄 PDF yaratish", callback_data="convert_pdf")
    btn_clear = InlineKeyboardButton("❌ Tozalash", callback_data="clear_images")
    markup.add(btn_convert, btn_clear)
    
    bot.reply_to(message, f"Rasm qabul qilindi! Hozircha jami: {len(user_images[chat_id])} ta rasm bo'ldi.\n"
                          f"Yana rasm yuborishingiz mumkin yoki PDF-ga aylantiring 👇", reply_markup=markup)

# Tugmalar bosilganda ishlaydigan qism
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    
    if call.data == "convert_pdf":
        if chat_id not in user_images or len(user_images[chat_id]) == 0:
            bot.answer_callback_query(call.id, "Hech qanday rasm yuborilmagan!", show_alert=True)
            return
            
        bot.answer_callback_query(call.id, "PDF tayyorlanmoqda, iltimos kuting...")
        bot.send_message(chat_id, "⌛️ Rasmlar qayta ishlanmoqda...")
        
        pdf_path = f"fayl_{chat_id}.pdf"
        images_list = []
        
        try:
            # Barcha rasmlarni RGB formatga o'tkazib ro'yxatga yig'ish
            for img_path in user_images[chat_id]:
                img = Image.open(img_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images_list.append(img)
                
            if images_list:
                # Birinchi rasm asosida PDF yaratish va qolganlarini unga qo'shish
                images_list[0].save(pdf_path, save_all=True, append_images=images_list[1:])
                
                # PDF faylni foydalanuvchiga yuborish
                with open(pdf_path, 'rb') as pdf_file:
                    bot.send_document(chat_id, pdf_file, caption="Sizning tayyor PDF faylingiz! 🎉\n@pdf_konverter_bot")
                    
            # Vaqtinchalik fayllarni o'chirish (tozalash)
            for img_path in user_images[chat_id]:
                if os.path.exists(img_path):
                    os.remove(img_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                
            user_images[chat_id] = [] # Ro'yxatni bo'shatish
            
        except Exception as e:
            bot.send_message(chat_id, "Kechirasiz, PDF yaratishda xatolik yuz berdi. Qaytadan urinib ko'ring.")
            user_images[chat_id] = []
            
    elif call.data == "clear_images":
        if chat_id in user_images:
            for img_path in user_images[chat_id]:
                if os.path.exists(img_path):
                    os.remove(img_path)
            user_images[chat_id] = []
            
        bot.answer_callback_query(call.id, "Barcha yuborilgan rasmlar o'chirildi.")
        bot.send_message(chat_id, "🔄 Rasmlar ro'yxati tozalandi. Yangitdan rasm yuborishingiz mumkin.")

if __name__ == "__main__":
    keep_alive()
    print("Bot yangi rejimda yoqilmoqda...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
            
