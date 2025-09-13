import logging
from datetime import datetime
from itertools import combinations
from rapidfuzz import process, fuzz

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# --- Определяем шаги сценария ---
class StartFlow(StatesGroup):
    waiting_for_website = State()
    waiting_for_brand = State()
    waiting_for_geo = State()

async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(StartFlow.waiting_for_website)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Type your Affiliate Website", callback_data="website")]]
    )
    await message.answer(
        "👋Hi there! Welcome to HOMD🚀 We’ve got 7 powerhouse teams with top-tier SEO, PPC, and ASO traffic.\n\n"
        #"Type your Affiliate Website (URL):",
        #reply_markup=keyboard
    )
# --- Пользователь вводит сайт ---
async def website_handler(message: types.Message, state: FSMContext):
    await state.update_data(website=message.text.strip())
    await state.set_state(StartFlow.waiting_for_brand)
    await message.answer("👌 Got it!\n\nNow type your Brand name:")

# --- Пользователь вводит бренд ---
async def brand_handler(message: types.Message, state: FSMContext):
    await state.update_data(brand=message.text.strip())
    await state.set_state(StartFlow.waiting_for_geo)
    await message.answer("👍 Great! Now type your GEOs (e.g. AU, US, IT):")

# --- Пользователь вводит GEO ---
async def geo_handler(message: types.Message, state: FSMContext, supabase, COUNTRY_MAP):
    data = await state.get_data()
    website = data.get("website", "[URL]")
    brand = data.get("brand", "[Brand]")

   # Запускаем geo-логику
    await handle_geos(message, supabase, COUNTRY_MAP, website=website, brand=brand)

    # После обработки очищаем state
    await state.clear()
"""
async def geo_button(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("✍️ Please enter GEOs (e.g. AU, US, IT):")
"""
async def log_user_request(supabase, user_id, username, geo_list, website="[URL]", brand="[Brand]"):
    try:
        now = datetime.utcnow().isoformat()
        if not geo_list:
            return

        team_map = {}  # team_name -> list of GEOs
        for geo in geo_list:
            pg_array = "{" + geo + "}"
            response = supabase.table("geo").select("*").filter("geos", "cs", pg_array).execute()
            for row in response.data:
                # team_table = f"{row['team_name'].lower()}_requests"
                team_name = row['team_name'].lower()
                if team_name not in team_map:
                    team_map[team_name] = []
                team_map[team_name].append(geo)
        for team_name, geos in team_map.items():
            team_table = f"{team_name}_requests"
            geo_text = " ".join(geos)  # объединяем GEO в одну строку
            supabase.table(team_table).insert({
                "user_id": user_id,
                "username": username,
                "geo": geo_text,
                "site": website,
                "brand": brand,
                "request_date": now
            }).execute()

        supabase.table("team8_requests").insert({
            "user_id": user_id,
            "username": username,
            "geo": " ".join(geo_list),
            "site": website,
            "brand": brand,
            "request_date": now
        }).execute()
            
    except Exception as e:
        logging.error(f"Failed to log request: {str(e)}")


def normalize_geo(user_words, COUNTRY_MAP):
    correct = []
    incorrect = []

    for word in user_words:
        word_clean = word.strip().replace("ё", "е").upper()
        best_match = None
        best_score = 70

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

async def handle_geos(message: types.Message, supabase, COUNTRY_MAP, website="[URL]", brand="[Brand]"):
    try:
        text = message.text.strip()
        user_words = text.replace(",", " ").split()

        correct_geos, incorrect_words = normalize_geo(user_words, COUNTRY_MAP)
        await log_user_request(
            supabase,
            message.from_user.id,
            message.from_user.username,
            correct_geos,
            website=website,
            brand=brand
        )

        geo_team_map = {}
        for geo in correct_geos:
            pg_array = "{" + geo + "}"
            response = supabase.table("geo").select("*").filter("geos", "cs", pg_array).execute()
            geo_team_map[geo] = set()
            for row in response.data:
                team_contact = f"{row['team_name']} – {row['contact']}"
                geo_team_map[geo].add(team_contact)

        used_teams = set()
        reply_parts = []

        for r in range(len(correct_geos), 0, -1):
            for geo_combo in combinations(correct_geos, r):
                combo_teams = set.intersection(*(geo_team_map[geo] for geo in geo_combo))
                combo_teams -= used_teams
                if combo_teams:
                    reply_parts.append(f"GEO: {', '.join(geo_combo)} – " + ", ".join(combo_teams))
                    used_teams.update(combo_teams)

        for word in incorrect_words:
            reply_parts.append(f"❌ No managers found for {word}")

        reply_text = "\n".join(reply_parts)

        if correct_geos:
            footer = (
                "\n • IMPORTANT: DM each contact separately — every team has different offers and traffic from their own sites.\n"
                " • They’ll help you with the best deals for your GEOs ASAP.\n"
                " • If anything looks off or a link doesn’t work, ping @racketwoman\n"
                f" • Example message:\n"
                f"Hey there 👋 I’m {message.from_user.username or '[Your Name]'} from {brand}. "
                f"Our affiliate program: {website}. We’re ready to talk GEOs and deal terms — when’s a good time for you?"
            )
            reply_text += footer

        await message.reply(reply_text)
        logger.info(f"GEO processed for {message.from_user.id}: {correct_geos}")

    except Exception as e:
        logger.error(f"Error processing GEOs: {e}")
        await message.reply("❌ An error occurred while processing your request. Please try again later.")

# Export all handlers
__all__ = [
    'cmd_start',
    'website_handler',
    'brand_handler',
    'geo_handler',
    #'geo_button',
    'handle_geos',
    'normalize_geo',
    'log_user_request'
]