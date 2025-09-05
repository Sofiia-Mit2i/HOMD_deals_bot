""""
from rapidfuzz import process, fuzz
from datetime import datetime

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
            """