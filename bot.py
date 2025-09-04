import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from rapidfuzz import process

# Конфигурация
DATA_FILE = "data.json"

# Основные страны для отображения на кнопках
MAIN_GEO = ["казахстан", "испания", "германия", "франция"]

# Загружаем базу данных из файла
def load_data():
    if not os.path.exists(DATA_FILE):
        # Создаем файл с базовой структурой, если его нет
        default_data = {
            "admins": [39],
            "geo": {
                "казахстан": ["@manager_kz1", "@manager_kz2"],
                "испания": ["@manager_es1", "@manager_es2"],
                "германия": ["@manager_de1"],
                "италия": ["@itmanger"],
                "франция": ["@francemanger"],
                "америка": ["@usman"],
                "польша": ["@plmanager"]
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Сохраняем данные в файл
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загрузка данных
data = load_data()
ADMINS = data["admins"]
GEO_CONTACTS = data["geo"]

# Функция для создания основной клавиатуры
def create_main_keyboard(user_id=None):
    keyboard = []
    row = []
    
    for i, geo in enumerate(MAIN_GEO):
        if geo not in GEO_CONTACTS:
            continue
            
        # Определяем флаг для страны
        flags = {
            "казахстан": "🇰🇿",
            "испания": "🇪🇸", 
            "германия": "🇩🇪",
            "франция": "🇫🇷"
        }
        
        flag = flags.get(geo, "📍")
        button_text = f"{flag} {geo.title()}"
        
        row.append(InlineKeyboardButton(button_text, callback_data=geo))
        
        # Размещаем по 2 кнопки в строке
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    
    # Добавляем последнюю строку, если она не пустая
    if row:
        keyboard.append(row)
    
    # Добавляем кнопку администрирования для админов
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")])
    
    return keyboard

# Проверка прав администратора
def is_admin(user_id):
    return user_id in ADMINS

# Поиск GEO (fuzzy search)
def find_geo(user_input: str):
    choices = list(GEO_CONTACTS.keys())
    if not choices:
        return None
        
    best_match, score, _ = process.extractOne(user_input.lower(), choices)
    if score > 70:
        return best_match
    return None

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = create_main_keyboard(update.effective_user.id)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Привет! Напиши свой GEO или выбери одну из основных стран ниже:\n"
        "Для других стран используй поиск (например, 'италия', 'америка', 'польша')",
        reply_markup=reply_markup
    )

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Обработка админ-панели
    if data == "admin_panel":
        if not is_admin(query.from_user.id):
            await query.edit_message_text("⛔ У вас нет прав доступа к админ-панели.")
            return
            
        keyboard = [
            [InlineKeyboardButton("➕ Добавить GEO", callback_data="add_geo")],
            [InlineKeyboardButton("✏️ Редактировать GEO", callback_data="edit_geo_menu")],
            [InlineKeyboardButton("❌ Удалить GEO", callback_data="delete_geo_menu")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚙️ Админ-панель:", reply_markup=reply_markup)
        return
    
    # Меню редактирования GEO
    if data == "edit_geo_menu":
        keyboard = []
        for geo in GEO_CONTACTS.keys():
            keyboard.append([InlineKeyboardButton(geo.title(), callback_data=f"edit_{geo}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите GEO для редактирования:", reply_markup=reply_markup)
        return
    
    # Меню удаления GEO
    if data == "delete_geo_menu":
        keyboard = []
        for geo in GEO_CONTACTS.keys():
            keyboard.append([InlineKeyboardButton(geo.title(), callback_data=f"delete_{geo}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите GEO для удаления:", reply_markup=reply_markup)
        return
    
    # Обработка удаления GEO
    if data.startswith("delete_"):
        geo = data.replace("delete_", "")
        
        if geo in GEO_CONTACTS:
            # Сохраняем контакты для возможного отката
            contacts = GEO_CONTACTS[geo]
            
            # Удаляем GEO
            del GEO_CONTACTS[geo]
            save_data({"admins": ADMINS, "geo": GEO_CONTACTS})
            
            await query.edit_message_text(
                f"✅ GEO '{geo}' удалено.\n"
                f"Контакты: {', '.join(contacts)}"
            )
        else:
            await query.edit_message_text(f"❌ GEO '{geo}' не найдено.")
        return
    
    # Обработка редактирования GEO
    if data.startswith("edit_"):
        geo = data.replace("edit_", "")
        
        if geo in GEO_CONTACTS:
            context.user_data["editing_geo"] = geo
            await query.edit_message_text(
                f"✏️ Редактирование GEO '{geo}':\n"
                f"Текущие контакты: {', '.join(GEO_CONTACTS[geo])}\n\n"
                f"Отправьте новые контакты в формате:\n"
                f"@contact1 @contact2 @contact3"
            )
        else:
            await query.edit_message_text(f"❌ GEO '{geo}' не найдено.")
        return
    
    # Добавление нового GEO
    if data == "add_geo":
        context.user_data["adding_geo"] = True
        await query.edit_message_text(
            "➕ Добавление нового GEO:\n"
            "Отправьте название GEO и контакты в format:\n"
            "название_гео @contact1 @contact2"
        )
        return
    
    # Возврат к главному меню
    if data == "back_to_main":
        keyboard = create_main_keyboard(query.from_user.id)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "👋 Выбери одну из основных стран или напиши название другой страны:",
            reply_markup=reply_markup
        )
        return
    
    # Обработка выбора GEO
    if data in GEO_CONTACTS:
        contacts = GEO_CONTACTS.get(data, [])
        response = f"📍 Менеджеры для {data.title()}:\n" + "\n".join(contacts)
        
        # Добавляем кнопку "Назад" после выбора страны
        keyboard = [[InlineKeyboardButton("🔙 Назад к выбору", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(response, reply_markup=reply_markup)
    else:
        await query.edit_message_text("❌ GEO не найдено.")

# Обработка текста (fuzzy search)
async def geo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Игнорируем команды
    if user_input.startswith("/"):
        return

    # Проверяем, находится ли пользователь в режиме добавления/редактирования GEO
    if context.user_data.get("adding_geo"):
        parts = user_input.split()
        if len(parts) < 2:
            await update.message.reply_text("❌ Неверный формат. Нужно: название_гео @contact1 @contact2")
            return
            
        geo = parts[0].lower()
        contacts = parts[1:]
        
        # Проверяем, что контакты начинаются с @
        for contact in contacts:
            if not contact.startswith("@"):
                await update.message.reply_text("❌ Все контакты должны начинаться с @")
                return
        
        GEO_CONTACTS[geo] = contacts
        save_data({"admins": ADMINS, "geo": GEO_CONTACTS})
        
        del context.user_data["adding_geo"]
        await update.message.reply_text(
            f"✅ GEO '{geo}' добавлено с контактами: {', '.join(contacts)}\n"
            f"💾 База успешно обновлена. Всего GEO: {len(GEO_CONTACTS)}"
        )
        return
    
    # Проверяем, находится ли пользователь в режиме редактирования GEO
    if context.user_data.get("editing_geo"):
        geo = context.user_data["editing_geo"]
        contacts = user_input.split()
        
        # Проверяем, что контакты начинаются с @
        for contact in contacts:
            if not contact.startswith("@"):
                await update.message.reply_text("❌ Все контакты должны начинаться с @")
                return
        
        GEO_CONTACTS[geo] = contacts
        save_data({"admins": ADMINS, "geo": GEO_CONTACTS})
        
        del context.user_data["editing_geo"]
        await update.message.reply_text(
            f"✅ Контакты для GEO '{geo}' обновлены: {', '.join(contacts)}"
        )
        return

    # Обычный поиск GEO
    geo = find_geo(user_input)

    if geo:
        contacts = GEO_CONTACTS[geo]
        response = f"📍 Похоже, ты имел в виду *{geo.title()}*:\n" + "\n".join(contacts)
        
        # Добавляем кнопку "Назад" для текстового поиска
        keyboard = [[InlineKeyboardButton("🔙 Назад к выбору", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        response = "❌ Не удалось найти GEO. Попробуй выбрать из кнопок ниже или уточни запрос."
        await update.message.reply_text(response)

# Команда для админов (добавить GEO)
async def add_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⛔ У тебя нет прав использовать эту команду.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Используй: /addgeo <ГЕО> <контакт1> <контакт2> ...")
        return

    geo = context.args[0].lower()
    contacts = context.args[1:]

    GEO_CONTACTS[geo] = contacts
    save_data({"admins": ADMINS, "geo": GEO_CONTACTS})

    await update.message.reply_text(
        f"✅ GEO '{geo}' добавлено с контактами: {', '.join(contacts)}\n"
        f"💾 База успешно обновлена. Всего GEO: {len(GEO_CONTACTS)}"
    )

# Команда для админов (удалить GEO)
async def remove_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⛔ У тебя нет прав использовать эту команду.")
        return

    if not context.args:
        await update.message.reply_text("Используй: /removegeo <ГЕО>")
        return

    geo = context.args[0].lower()
    
    if geo in GEO_CONTACTS:
        contacts = GEO_CONTACTS[geo]
        del GEO_CONTACTS[geo]
        save_data({"admins": ADMINS, "geo": GEO_CONTACTS})
        await update.message.reply_text(
            f"✅ GEO '{geo}' удалено.\n"
            f"Контакты: {', '.join(contacts)}"
        )
    else:
        await update.message.reply_text(f"❌ GEO '{geo}' не найдено.")

# Команда для админов (список всех GEO)
async def list_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⛔ У тебя нет прав использовать эту команду.")
        return

    if not GEO_CONTACTS:
        await update.message.reply_text("❌ База GEO пуста.")
        return

    # Разделяем основные и дополнительные GEO
    main_geo = []
    other_geo = []
    
    for geo in GEO_CONTACTS.keys():
        if geo in MAIN_GEO:
            main_geo.append(geo)
        else:
            other_geo.append(geo)
    
    response = "📋 Список всех GEO:\n\n"
    response += "🌟 Основные GEO (на кнопках):\n"
    for geo in main_geo:
        contacts = GEO_CONTACTS[geo]
        response += f"• {geo.title()}: {', '.join(contacts)}\n"
    
    response += "\n🔍 Дополнительные GEO (через поиск):\n"
    for geo in other_geo:
        contacts = GEO_CONTACTS[geo]
        response += f"• {geo.title()}: {', '.join(contacts)}\n"

    await update.message.reply_text(response)

# Команда для админов (редактировать контакты GEO)
async def edit_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⛔ У тебя нет прав использовать эту команду.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Используй: /editgeo <ГЕО> <новый_контакт1> <новый_контакт2> ...")
        return

    geo = context.args[0].lower()
    
    if geo not in GEO_CONTACTS:
        await update.message.reply_text(f"❌ GEO '{geo}' не найдено.")
        return

    contacts = context.args[1:]
    GEO_CONTACTS[geo] = contacts
    save_data({"admins": ADMINS, "geo": GEO_CONTACTS})

    await update.message.reply_text(
        f"✅ Контакты для GEO '{geo}' обновлены: {', '.join(contacts)}"
    )

def main():
    # Вставь свой токен
    TOKEN = "8358530594:AAEXLL2IyEInhs7ruykTrtgxClcR0WhzkMw"
    
    app = Application.builder().token(TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addgeo", add_geo))
    app.add_handler(CommandHandler("removegeo", remove_geo))
    app.add_handler(CommandHandler("listgeo", list_geo))
    app.add_handler(CommandHandler("editgeo", edit_geo))
    
    # Обработчики callback-кнопок и сообщений
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, geo_handler))

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()