import logging
from datetime import datetime
from itertools import combinations
from rapidfuzz import process, fuzz
from aiogram import types

logger = logging.getLogger(__name__)

async def log_user_request(supabase, user_id, username, geo_list):
    """
    Log user GEO requests to team-specific tables in Supabase
    """
    try:
        now = datetime.utcnow().isoformat()
        for geo in geo_list:
            response = supabase.table("geo").select("*").filter("geos", "cs", f'{{{geo}}}').execute()
            for row in response.data:
                team_table = f"{row['team_name'].lower()}_requests"
                supabase.table(team_table).insert({
                    "user_id": user_id,
                    "username": username,
                    "geo": geo,
                    "request_date": now
                }).execute()
        for geo in geo_list:
            supabase.table("team8_requests").insert({
                "user_id": user_id,
                "username": username,
                "geo": geo,
                "request_date": now
            }).execute()
        logger.info(f"Logged request for user {username} with GEOs: {geo_list}")
    except Exception as e:
        logger.error(f"Failed to log request: {str(e)}")

def normalize_geo(user_words, COUNTRY_MAP):
    """
    Match user input with country codes using fuzzy matching
    """
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
    """
    Handle incoming messages with GEO codes
    """
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
        
        # Add footer if there were any correct GEOs
        if correct_geos:
            footer = "\n\n✅ Next steps\n" \
                    " • Please message each contact separately (so nothing gets missed).\n" \
                    " • They'll help with the best deals for your GEOs as soon as possible.\n" \
                    " • If anything looks off or a link doesn't work, ping @racketwoman.\n" \
                    "Great to (e-)meet you—have a fantastic day! 🙌"
            reply_text += footer

        await message.reply(reply_text)
        logger.info(f"Processed GEOs for user {message.from_user.id}: correct={correct_geos}, incorrect={incorrect_words}")
        
    except Exception as e:
        error_msg = f"Error processing GEOs: {str(e)}"
        logger.error(error_msg)
        await message.reply("❌ An error occurred while processing your request. Please try again later.")

# Export the functions that will be used by other modules
__all__ = ['handle_geos', 'normalize_geo', 'log_user_request']