import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from rapidfuzz import process

ADMINS =  [333192979]  # Замените на реальные ID админов

# Загружаем базу GEO из файла
def load_data():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Сохраняем базу GEO в файл
def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Инициализация базы
GEO_CONTACTS = load_data()

# Поиск GEO (fuzzy search)
def find_geo(user_input: str):
    choices = list(GEO_CONTACTS.keys())
    best_match, score, _ = process.extractOne(user_input.lower(), choices)
    if score > 70:
        return best_match
    return None

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("kz Казахстан", callback_data="казахстан")],
        [InlineKeyboardButton("🇪🇸 Испания", callback_data="испания")],
        [InlineKeyboardButton("🇩🇪 Германия", callback_data="германия")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Привет! Напиши свой GEO или выбери страну ниже:",
        reply_markup=reply_markup
    )

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    geo = query.data
    contacts = GEO_CONTACTS.get(geo, [])
    response = "📍 Менеджеры для региона:\n" + "\n".join(contacts)

    await query.edit_message_text(response)

# Обработка текста (fuzzy search)
async def geo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Игнорируем команды
    if user_input.startswith("/"):
        return

    geo = find_geo(user_input)

    if geo:
        contacts = GEO_CONTACTS[geo]
        response = f"📍 Похоже, ты имел в виду *{geo.title()}*:\n" + "\n".join(contacts)
    else:
        response = "❌ Не удалось найти GEO. Попробуй выбрать из кнопок ниже."

    await update.message.reply_text(response, parse_mode="Markdown")


# Команда для админов (добавить GEO)
# Команда для админов (добавить GEO)
async def add_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Проверка: если не админ → отказ
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ У тебя нет прав использовать эту команду.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Используй: /addgeo <ГЕО> <контакт1> <контакт2> ...")
        return

    geo = context.args[0].lower()
    contacts = context.args[1:]

    GEO_CONTACTS[geo] = contacts
    save_data(GEO_CONTACTS)

    # Сообщение об успешном добавлении
    await update.message.reply_text(f"✅ GEO '{geo}' добавлено с контактами: {', '.join(contacts)}")

    # Дополнительно: сообщение об успешном обновлении базы
    await update.message.reply_text("💾 База успешно обновлена.")

def main():
    # Вставь свой токен
    TOKEN = "8499168190:AAFjzUhHqHK1ZOQQlthMVbmotWIW_yBosLw"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addgeo", add_geo))  # только для админов
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, geo_handler))

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
