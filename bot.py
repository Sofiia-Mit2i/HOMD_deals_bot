import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from supabase import create_client, Client
from rapidfuzz import process, fuzz
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# подключение к Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

COUNTRY_MAP = {
    "AU": ["AU", "AUSTRALIA", "АВСТРАЛИЯ", "АВСТРАЛІЯ"],
    "AZ": ["AZ", "AZERBAIJAN", "АЗЕРБАЙДЖАН"],
    "CA": ["CA", "CANADA", "КАНАДА"],
    "CZ": ["CZ", "CZECH REPUBLIC", "ЧЕХИЯ", "ЧЕХІЯ"],
    "DE": ["DE", "GERMANY", "ГЕРМАНИЯ", "НІМЕЧЧИНА"],
    "HU": ["HU", "HUNGARY", "ВЕНГРИЯ", "УГОРЩИНА"],
    "NZ": ["NZ", "NEW ZEALAND", "НОВАЯ ЗЕЛАНДИЯ", "НОВА ЗЕЛАНДІЯ"],
    "SK": ["SK", "SLOVAKIA", "СЛОВАКИЯ", "СЛОВАЧЧИНА"],
    "US": ["US", "USA", "UNITED STATES", "США"],
    "GB": ["GB", "UNITED KINGDOM", "ВЕЛИКОБРИТАНИЯ", "ВЕЛИКА БРИТАНІЯ"],
    "NL": ["NL", "NETHERLANDS", "НИДЕРЛАНДЫ", "НІДЕРЛАНДИ"],
    "GR": ["GR", "GREECE", "ГРЕЦИЯ", "ГРЕЦІЯ"],
    "AT": ["AT", "AUSTRIA", "АВСТРИЯ", "АВСТРІЯ"],
    "BE": ["BE", "BELGIUM", "БЕЛЬГИЯ", "БЕЛЬГІЯ"],
    "BR": ["BR", "BRAZIL", "БРАЗИЛИЯ", "БРАЗИЛІЯ"],
    "BG": ["BG", "BULGARIA", "БОЛГАРИЯ", "БОЛГАРІЯ"],
    "CL": ["CL", "CHILE", "ЧИЛИ", "ЧИЛІ"],
    "DK": ["DK", "DENMARK", "ДАНИЯ", "ДАНІЯ"],
    "EE": ["EE", "ESTONIA", "ЭСТОНИЯ", "ЕСТОНІЯ"],
    "FI": ["FI", "FINLAND", "ФИНЛЯНДИЯ", "ФІНЛЯНДІЯ"],
    "FR": ["FR", "FRANCE", "ФРАНЦИЯ", "ФРАНЦІЯ"],
    "IE": ["IE", "IRELAND", "ИРЛАНДИЯ", "ІРЛАНДІЯ"],
    "IT": ["IT", "ITALY", "ИТАЛИЯ", "ІТАЛІЯ"],
    "JP": ["JP", "JAPAN", "ЯПОНИЯ", "ЯПОНІЯ"],
    "MY": ["MY", "MALAYSIA", "МАЛАЙЗИЯ", "МАЛАЙЗІЯ"],
    "NO": ["NO", "NORWAY", "НОРВЕГИЯ", "НОРВЕГІЯ"],
    "PH": ["PH", "PHILIPPINES", "ФИЛИППИНЫ", "ФІЛІППІНИ"],
    "PL": ["PL", "POLAND", "ПОЛЬША", "ПОЛЬЩА"],
    "PT": ["PT", "PORTUGAL", "ПОРТУГАЛИЯ", "ПОРТУГАЛІЯ"],
    "SI": ["SI", "SLOVENIA", "СЛОВЕНИЯ", "СЛОВЕНІЯ"],
    "ES": ["ES", "SPAIN", "ИСПАНИЯ", "ІСПАНІЯ"],
    "CH": ["CH", "SWITZERLAND", "ШВЕЙЦАРИЯ", "ШВЕЙЦАРІЯ"],
    "BD": ["BD", "BANGLADESH", "БАНГЛАДЕШ"],
    "ZA": ["ZA", "SOUTH AFRICA", "ЮАР", "ПАР"],
    "IN": ["IN", "INDIA", "ИНДИЯ", "ІНДІЯ"],
    "MM": ["MM", "MYANMAR", "МЬЯНМА", "М'ЯНМА"],
    "LV": ["LV", "LATVIA", "ЛАТВИЯ", "ЛАТВІЯ"],
    "PK": ["PK", "PAKISTAN", "ПАКИСТАН"],
    "BA": ["BA", "BOSNIA AND HERZEGOVINA", "БОСНИЯ И ГЕРЦЕГОВИНА", "БОСНІЯ І ГЕРЦЕГОВИНА"],
    "LT": ["LT", "LITHUANIA", "ЛИТВА"],
    "HR": ["HR", "CROATIA", "ХОРВАТИЯ", "ХОРВАТІЯ"],
    "RO": ["RO", "ROMANIA", "РУМЫНИЯ", "РУМУНІЯ"],
    "MX": ["MX", "MEXICO", "МЕКСИКА"],
    "ID": ["ID", "INDONESIA", "ИНДОНЕЗИЯ", "ІНДОНЕЗІЯ"],
    "CY": ["CY", "CYPRUS", "КИПР", "КІПР"],
    "UA": ["UA", "UKRAINE", "УКРАИНА", "УКРАЇНА"],
    "TH": ["TH", "THAILAND", "ТАЙЛАНД", "ТАЙЛАНД"],
    "TR": ["TR", "TURKEY", "ТУРЦИЯ", "ТУРЕЧЧИНА"],
    "NP": ["NP", "NEPAL", "НЕПАЛ"],
    "ET": ["ET", "ETHIOPIA", "ЭФИОПИЯ", "ЕФІОПІЯ"],
    "RU": ["RU", "RUSSIA", "РОССИЯ", "РОСІЯ"],
    "GE": ["GE", "GEORGIA", "ГРУЗИЯ", "ГРУЗІЯ"],
    "RS": ["RS", "SERBIA", "СЕРБИЯ", "СЕРБІЯ"],
    "AE": ["AE", "UNITED ARAB EMIRATES", "ОАЭ", "ОАЕ"],
    "SG": ["SG", "SINGAPORE", "СИНГАПУР", "СІНГАПУР"],
    "PG": ["PG", "PAPUA NEW GUINEA", "ПАПУА — НОВАЯ ГВИНЕЯ", "ПАПУА — НОВА ГВІНЕЯ"],
    "IR": ["IR", "IRAN", "ИРАН", "ІРАН"],
    "AR": ["AR", "ARGENTINA", "АРГЕНТИНА"],
    "AL": ["AL", "ALBANIA", "АЛБАНИЯ", "АЛБАНІЯ"],
    "LU": ["LU", "LUXEMBOURG", "ЛЮКСЕМБУРГ"],
    "MK": ["MK", "NORTH MACEDONIA", "СЕВЕРНАЯ МАКЕДОНИЯ", "ПІВНІЧНА МАКЕДОНІЯ"],
    "SA": ["SA", "SAUDI ARABIA", "САУДОВСКАЯ АРАВИЯ", "САУДІВСЬКА АРАВІЯ"],
    "NG": ["NG", "NIGERIA", "НИГЕРИЯ", "НІГЕРІЯ"],
    "MT": ["MT", "MALTA", "МАЛЬТА"],
    "MA": ["MA", "MOROCCO", "МАРОККО"],
    "KW": ["KW", "KUWAIT", "КУВЕЙТ"],
    "KE": ["KE", "KENYA", "КЕНИЯ", "КЕНІЯ"],
    "BN": ["BN", "BRUNEI", "БРУНЕЙ"],
    "LK": ["LK", "SRI LANKA", "ШРИ-ЛАНКА", "ШРІ-ЛАНКА"],
    "ME": ["ME", "MONTENEGRO", "ЧЕРНОГОРИЯ", "ЧОРНОГОРІЯ"],
    "IL": ["IL", "ISRAEL", "ИЗРАИЛЬ", "ІЗРАЇЛЬ"],
    "NA": ["NA", "NAMIBIA", "НАМИБИЯ", "НАМІБІЯ"],
    "AM": ["AM", "ARMENIA", "АРМЕНИЯ", "ВІРМЕНІЯ"],
    "CM": ["CM", "CAMEROON", "КАМЕРУН"],
    "TN": ["TN", "TUNISIA", "ТУНИС", "ТУНІС"],
    "KR": ["KR", "SOUTH KOREA", "ЮЖНАЯ КОРЕЯ", "ПІВДЕННА КОРЕЯ"],
    "VN": ["VN", "VIETNAM", "ВЬЕТНАМ", "В'ЄТНАМ"],
    "EG": ["EG", "EGYPT", "ЕГИПЕТ", "ЄГИПЕТ"],
    "UG": ["UG", "UGANDA", "УГАНДА"],
    "MD": ["MD", "MOLDOVA", "МОЛДАВИЯ", "МОЛДОВА"],
    "ZM": ["ZM", "ZAMBIA", "ЗАМБИЯ", "ЗАМБІЯ"],
    "ZW": ["ZW", "ZIMBABWE", "ЗИМБАБВЕ", "ЗІМБАБВЕ"],
    "KZ": ["KZ", "KAZAKHSTAN", "КАЗАХСТАН"],
    "UY": ["UY", "URUGUAY", "УРУГВАЙ"],
    "IS": ["IS", "ICELAND", "ИСЛАНДИЯ", "ІСЛАНДІЯ"],
    "KH": ["KH", "CAMBODIA", "КАМБОДЖА"],
    "LB": ["LB", "LEBANON", "ЛИВАН", "ЛІВАН"],
    "DZ": ["DZ", "ALGERIA", "АЛЖИР"],
    "RE": ["RE", "RÉUNION", "РЕЮНЬОН"],
    "QA": ["QA", "QATAR", "КАТАР"],
    "LA": ["LA", "LAOS", "ЛАОС"],
    "PR": ["PR", "PUERTO RICO", "ПУЭРТО-РИКО", "ПУЕРТО-РІКО"],
    "HK": ["HK", "HONG KONG", "ГОНКОНГ"],
    "CO": ["CO", "COLOMBIA", "КОЛУМБИЯ", "КОЛУМБІЯ"],
    "SY": ["SY", "SYRIA", "СИРИЯ", "СИРІЯ"],
    "XK": ["XK", "KOSOVO", "КОСОВО"]
}

# -----------------------
# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Type GEOs Now", callback_data="geo")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Welcome! Please type your GEOs:", reply_markup=reply_markup)

# -----------------------
# inline кнопка → вызывает /geo
async def geo_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✍️ Please enter GEOs (e.g. AU, US, IT):")

async def log_user_request(user_id, username, geo_list):
    """
    geo_list = ['AU', 'US', 'PL'] – список ISO кодов, которые запросил пользователь
    """
    now = datetime.utcnow().isoformat()

    for geo in geo_list:
        # Определяем команды, которые отвечают за GEO
        response = supabase.table("geo").select("*").filter("geos", "cs", f'{{{geo}}}').execute()
        for row in response.data:
            team_table = f"{row['team_name'].lower()}_requests"  # имя таблицы команды
            supabase.table(team_table).insert({
                "user_id": user_id,
                "username": username,
                "geo": geo,
                "request_date": now
            }).execute()

# -----------------------
# обработка сообщений с GEO
def normalize_geo(user_words):
    """
    Принимает список слов пользователя.
    Возвращает:
        - корректные ISO GEO-коды (список)
        - некорректные слова (список)
    """
    correct = []
    incorrect = []

    # Нормализуем COUNTRY_MAP для поиска (все значения в верхнем регистре

    for word in user_words:
        word_clean = word.strip().replace("ё", "е").upper() # очистка ввода
        best_match = None
        best_score = 70  # уменьшенный порог для частичных совпадений

        for geo_code, names in COUNTRY_MAP.items():
            score = process.extractOne(word_clean, names, scorer=fuzz.ratio)
            if score and score[1] >= best_score:
                best_match = geo_code
                best_score = score[1]

        if best_match:
            correct.append(best_match)
        else:
            incorrect.append(word)

    return correct, incorrect

async def handle_geos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # Разделяем по пробелам и запятым
    user_words = text.replace(",", " ").split()

    # Нормализуем введённые страны
    correct_geos, incorrect_words = normalize_geo(user_words)

    await log_user_request(update.message.from_user.id, update.message.from_user.username, correct_geos)

    print("DEBUG: Correct GEOs:", correct_geos)
    print("DEBUG: Incorrect words:", incorrect_words)

    results = {}

    if correct_geos:
        # формируем массив для Postgres text[]
        pg_array = "{" + ",".join(correct_geos) + "}"
        response = supabase.table("geo").select("*").filter("geos", "ov", pg_array).execute()

        for geo in correct_geos:
    # массив с одним элементом, чтобы использовать фильтр Postgres 'cs' (contains)
            pg_array = "{" + geo + "}"
            response = supabase.table("geo").select("*").filter("geos", "cs", pg_array).execute()

            results[geo] = []
            for row in response.data:
                team_name = row["team_name"]
                contacts = row["contact"]
                contacts_str = ", ".join(contacts) if isinstance(contacts, list) else str(contacts)
                results[geo].append(f"{team_name} – {contacts_str}")

    
    # Формируем сообщение с контактами
    reply_parts = []

    for geo, managers in results.items():
        if managers:
            reply_parts.append(f"{geo}:\n" + "\n".join(managers))
        else:
            reply_parts.append(f"❌ No managers found for {geo}")

    for word in incorrect_words:
        reply_parts.append(f"❌ No managers found for {word}")

    # Объединяем в один текст
    reply_text = "\n\n".join(reply_parts)

    # Добавляем сообщение с инструкциями
    if correct_geos:
        reply_text += "\n\n✅ Next steps\n" \
                    " • Please message each contact separately (so nothing gets missed).\n" \
                    " • They’ll help with the best deals for your GEOs as soon as possible.\n" \
                    " • If anything looks off or a link doesn’t work, ping @racketwoman.\n" \
                    "Great to (e-)meet you—have a fantastic day!"

    await update.message.reply_text(reply_text)

# -----------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(geo_button, pattern="^geo$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_geos))

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
