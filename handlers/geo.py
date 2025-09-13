"""
import logging
from datetime import datetime
from itertools import combinations
from rapidfuzz import process, fuzz
from aiogram import types
from itertools import combinations

logger = logging.getLogger(__name__)

async def log_user_request(supabase, user_id, username, geo_list):
    
    Log user GEO requests to team-specific tables in Supabase.
    Each team gets a single entry with all GEOs it is responsible for.
    
    try:
        now = datetime.utcnow().isoformat()
        if not geo_list:
            return

        # Получаем все команды, которые соответствуют хотя бы одному GEO
        team_map = {}  # team_name -> list of GEOs
        for geo in geo_list:
            pg_array = "{" + geo + "}"  # для фильтрации в Supabase
            response = supabase.table("geo").select("*").filter("geos", "cs", pg_array).execute()
            for row in response.data:
                team_name = row['team_name'].lower()
                if team_name not in team_map:
                    team_map[team_name] = []
                team_map[team_name].append(geo)

        # Вставляем по каждой команде одну строку с объединёнными GEO
        for team_name, geos in team_map.items():
            team_table = f"{team_name}_requests"
            geo_text = " ".join(geos)  # объединяем GEO в одну строку
            supabase.table(team_table).insert({
                "user_id": user_id,
                "username": username,
                "geo": geo_text,
                "request_date": now
            }).execute()

        # Если нужно, можно добавить общую запись в team8_requests с полным списком GEO
        supabase.table("team8_requests").insert({
            "user_id": user_id,
            "username": username,
            "geo": " ".join(geo_list),
            "request_date": now
        }).execute()

    except Exception as e:
        import logging
        logging.error(f"Failed to log request: {str(e)}")

def normalize_geo(user_words, COUNTRY_MAP):
    
    Match user input with country codes using fuzzy matching
    
    correct = []
    incorrect = []

    for word in user_words:
        word_clean = word.strip().replace("ё", "е").upper()
        best_match = None
        best_score = 70

        if len(word_clean) < 2 or any(char.isdigit() for char in word_clean):
            continue

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

async def handle_geos(message: types.Message, supabase, COUNTRY_MAP):
    
    Handle incoming messages with GEO codes
    
    try:
        text = message.text.strip()
        user_words = text.replace(",", " ").split()

        correct_geos, incorrect_words = normalize_geo(user_words, COUNTRY_MAP)
        await log_user_request(supabase, message.from_user.id, message.from_user.username, correct_geos)

        # Build GEO -> teams mapping
        geo_team_map = {}
        for geo in correct_geos:
            pg_array = "{" + geo + "}"
            response = supabase.table("geo").select("*").filter("geos", "cs", pg_array).execute()
            geo_team_map[geo] = set()
            for row in response.data:
                team_contact = f"{row['team_name']} – {row['contact']}"
                geo_team_map[geo].add(team_contact)

        # Find GEO combinations with common teams
        used_teams = set()
        reply_parts = []

        for r in range(len(correct_geos), 0, -1):
            for geo_combo in combinations(correct_geos, r):
                combo_teams = set.intersection(*(geo_team_map[geo] for geo in geo_combo))
                combo_teams -= used_teams
                if combo_teams:
                    reply_parts.append(f"GEO: {', '.join(geo_combo)} – " + ", ".join(combo_teams))
                    used_teams.update(combo_teams)

        # Add incorrect GEOs to response
        for word in incorrect_words:
            reply_parts.append(f"❌ No managers found for {word}")

        reply_text = "\n".join(reply_parts)

        # Footer
        if correct_geos:
            footer = (
                "\n • IMPORTANT: DM each contact separately — every team has different offers and traffic from their own sites.\n"
                " • They’ll help you with the best deals for your GEOs ASAP.\n"
                " • If anything looks off or a link doesn’t work, ping @racketwoman\n"
                f" • Here is the message. Hey there 👋 I’m {message.from_user.username or '[Your Name]'} from {brand}. "
                f"Our affiliate program: {website}. We’re ready to talk GEOs and deal terms — when’s a good time for you?"
            )
            reply_text += footer

        await message.reply(reply_text)
        logger.info(f"Processed GEOs for user {message.from_user.id}: correct={correct_geos}, incorrect={incorrect_words}")

    except Exception as e:
        error_msg = f"Error processing GEOs: {str(e)}"
        logger.error(error_msg)
        await message.reply("❌ An error occurred while processing your request. Please try again later.")

async def cmd_start(message: types.Message):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Type GEOs Now", callback_data="geo")]
        ]
    )
    await message.answer(
        "👋Hi there! Welcome to HOMD🚀 We’ve got 7 powerhouse teams with top-tier SEO, PPC, and ASO traffic. "
        "Type your GEOs (e.g., UK, DE, PL) and we’ll hook you up with the right managers in seconds⚡️",
        reply_markup=keyboard
    )

async def geo_button(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("✍️ Please enter GEOs (e.g. AU, US, IT):")

__all__ = ['cmd_start', 'geo_button', 'handle_geos', 'normalize_geo', 'log_user_request']

"""