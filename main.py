import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont
import os
from flask import Flask
from threading import Thread

TOKEN = "8086061724:AAFNorWcbL71wKBYKecJQ-yaA60Sy6sIsAo"
bot = telebot.TeleBot(TOKEN)

user_elements = {}  # Rasmlar va matnli sahifalarni birgalikda saqlash uchun
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
    user_elements[message.chat.id] = []
    bot.reply_to(message, "Salom! Menga rasm yoki biron-bir matn yuboring. Men ulardan PDF yaratib beraman!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if chat_id not in user_elements:
        user_elements[chat_id] = []
        
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    file_name = f"img_{chat_id}_{len(user_elements[chat_id])}.jpg"
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
        
    user_elements[chat_id].append(('image', file_name))
    show_menu(message)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if message.text.startswith('/'):
        return  # Buyruqlarga javob bermaslik uchun
        
    if chat_id not in user_elements:
        user_elements[chat_id] = []
        
    text_content = message.text
    
    # Matnni oq sahifaga rasm ko'rinishida chizish (A4 formatga moslash)
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Standart shriftlardan foydalanamiz
    try:
        font = ImageFont.load_default()
    except:
        font = None
        
    # Matnni satrlarga bo'lib chiqish (chegaradan chiqib ketmasligi uchun)
    lines = []
    words = text_content.split()
    current_line = ""
    for word in words:
        if len(current_line + " " + word) < 50:
            current_line += " " + word
        else:
            lines.append(current_line.strip())
            current_line = word
    if current_line:
        lines.append(current_line.strip())
        
    # Matnni sahifaga yozish
    y = 50
    for line in lines:
        d.text((50, y), line, fill=(0, 0, 0), font=font)
        y += 25
        if y > 1000:  # Sahifa to'lsa to'xtash
            break
            
    file_name = f"txt_{chat_id}_{len(user_elements[chat_id])}.jpg"
    img.save(file_name)
    
    user_elements[chat_id].append(('text_img', file_name))
    show_menu(message)

def show_menu(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()
    btn_convert = InlineKeyboardButton("📄 PDF yaratish", callback_data="convert_pdf")
    btn_clear = InlineKeyboardButton("❌ Tozalash", callback_data="clear_elements")
    markup.add(btn_convert, btn_clear)
    
    bot.reply_to(message, f"Element qo'shildi! Jami sahifalar: {len(user_elements[chat_id])} ta.\nPDF qilish uchun bosing 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    
    if call.data == "convert_pdf":
        if chat_id not in user_elements or len(user_elements[chat_id]) == 0:
            bot.answer_callback_query(call.id, "Hech qanday element yuborilmagan!")
            return
            
        bot.answer_callback_query(call.id, "Ism kutilmoqda...")
        msg = bot.send_message(chat_id, "✍️ PDF faylga nima deb nom beramiz? (Nomini yozib yuboring):")
        bot.register_next_step_handler(msg, process_pdf_name)
            
    elif call.data == "clear_elements":
        if chat_id in user_elements:
            for el_type, path in user_elements[chat_id]:
                if os.path.exists(path): os.remove(path)
            user_elements[chat_id] = []
        bot.answer_callback_query(call.id, "Hamma elementlar tozalandi.")

def process_pdf_name(message):
    chat_id = message.chat.id
    pdf_name = message.text.strip()
    
    for char in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>']:
        pdf_name = pdf_name.replace(char, '')
        
    if not pdf_name:
        pdf_name = f"fayl_{chat_id}"
        
    bot.send_message(chat_id, f"Fayl nomi: {pdf_name}.pdf\nPDF tayyorlanmoqda... ⏳")
    
    pdf_path = f"{pdf_name}.pdf"
    images_list = []
    
    try:
        for el_type, path in user_elements[chat_id]:
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images_list.append(img)
            
        if images_list:
            images_list[0].save(pdf_path, save_all=True, append_images=images_list[1:])
            with open(pdf_path, 'rb') as pdf_file:
                bot.send_document(chat_id, pdf_file, caption=f"Tayyor! 🎉\n📄 Fayl nomi: {pdf_name}.pdf")
                
        # Fayllarni o'chirish (tozalash)
        for el_type, path in user_elements[chat_id]:
            if os.path.exists(path): os.remove(path)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        user_elements[chat_id] = []
        
    except Exception as e:
        bot.send_message(chat_id, "Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        if os.path.exists(pdf_path): os.remove(pdf_path)
        user_elements[chat_id] = []

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
