from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from itertools import combinations

async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Type GEOs Now", callback_data="geo")]
        ]
    )
    await message.answer("👋Hi there! Welcome to HOMD🚀 We’ve got 7 powerhouse teams with top-tier SEO , PPC, and ASO traffic.Type your GEOs (e.g., UK, DE, PL) and we’ll hook you up with the right managers in seconds⚡️", reply_markup=keyboard)

async def geo_button(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("✍️ Please enter GEOs (e.g. AU, US, IT):")

async def log_user_request(supabase, user_id, username, geo_list):
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

async def handle_geos(message: types.Message, supabase, COUNTRY_MAP):
    text = message.text.strip()
    user_words = text.replace(",", " ").split()

    correct_geos, incorrect_words = normalize_geo(user_words, COUNTRY_MAP)
    await log_user_request(supabase, message.from_user.id, message.from_user.username, correct_geos)

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
        footer = "\n\n✅ Next steps\n" \
                " • IMPORTANT: DM each contact separately — every team has different offers and traffic from their own sites.\n" \
                " Here is the message.  Hey there 👋 I’m [Your Name] from [Brand]. Our affiliate program: [URL]. We’re ready to talk GEOs and deal terms—when’s a good time for you?" \
                " • They’ll help you with the best deals for your GEOs ASAP.\n" 
                " • If anything looks off or a link doesn’t work, ping @racketwoman\n" \
                "Great to (e-)meet you—have a fantastic day! 🙌"
        reply_text += footer

    await message.reply(reply_text)

# Export all handlers
__all__ = ['cmd_start', 'geo_button', 'handle_geos', 'normalize_geo', 'log_user_request']
