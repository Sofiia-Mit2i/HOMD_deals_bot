import logging
import os
import asyncio
import json
from aiogram import Bot, Dispatcher,  types 
from aiogram.filters import Command
from aiogram import F
from supabase import create_client
from dotenv import load_dotenv

from handlers.geo import handle_geos, normalize_geo
from handlers import cmd_start, geo_button
from handlers.excel import handle_download, handle_messages_download
from handlers.other import handle_other_message

from adminpanel import change_contact, add_contact, delete_contact
from admin import is_admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables and configuration
load_dotenv()

try:
    with open('COUNTRY_MAP.json', 'r', encoding='utf-8') as f:
        COUNTRY_MAP = json.load(f)
    logger.info("Successfully loaded country map")
except Exception as e:
    logger.error(f"Failed to load country map: {str(e)}")
    raise SystemExit(1)

# Initialize bot configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_TOKEN]):
    logger.error("Missing required environment variables")
    raise SystemExit(1)

# Initialize Supabase
try:
    supabase = create_client(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
    logger.info("Successfully connected to Supabase")
except Exception as e:
    logger.error(f"Failed to connect to Supabase: {str(e)}")
    raise SystemExit(1)

# Callback для кнопки "Скачать все"
async def download_all_callback(callback: types.CallbackQuery, supabase):
    user_id = callback.from_user.id
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав для этой команды.", show_alert=True)
        return

    # Передаём текст напрямую и бот
    await send_team_excel_from_callback(callback, supabase)

    await callback.answer()  # убрать "часики"

# новая версия send_team_excel для callback
async def send_team_excel_from_callback(callback: types.CallbackQuery, supabase):
    """
    Скачивание всех таблиц по кнопке "Скачать все"
    """
    TEAMS = ["Team1", "Team2", "Team3", "Team4", "Team5", "Team6", "Team7"]
    user_id = callback.from_user.id

    tables = [f"{team.lower()}_requests" for team in TEAMS]

    for table_name in tables:
        try:
            response = supabase.table(table_name)\
                .select("*")\
                .order("request_date", desc=True)\
                .execute()

            if not response.data:
                await callback.message.answer(f"📊 В таблице {table_name} нет данных.")
                continue

            # DataFrame → Excel
            import pandas as pd
            from io import BytesIO
            df = pd.DataFrame(response.data)
            for col in df.columns:
                df[col] = df[col].astype(str)

            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            from aiogram.types import BufferedInputFile
            file = BufferedInputFile(buffer.getvalue(), filename=f"{table_name}.xlsx")

            await callback.message.answer_document(
                document=file,
                caption=f"📊 Данные из {table_name}"
            )
        except Exception as e:
            logging.error(f"Ошибка при экспорте {table_name}: {e}")
            await callback.message.answer(f"❌ Ошибка при экспорте {table_name}")


async def message_handler(message: types.Message):
    """Route messages to appropriate handlers"""
    try:
        text = message.text.strip()
        words = text.replace(",", " ").split()
        
        # Try to normalize as GEOs first
        correct_geos, incorrect_words = normalize_geo(words, COUNTRY_MAP)
        
        # Route to appropriate handler:
        # 1. If we have correct GEOs, handle as GEO message
        # 2. If message is likely not a GEO attempt, handle as other message
        if correct_geos:
            await handle_geos(message, supabase, COUNTRY_MAP)
        elif len(words) > 3 or not any(len(word) == 2 for word in words):
            logger.info(f"Processing other message from user {message.from_user.id}")
            await handle_other_message(message, supabase)
        else:
            # Treat as failed GEO attempt
            await handle_geos(message, supabase, COUNTRY_MAP)
    except Exception as e:
        logger.error(f"Error in message_handler: {str(e)}")
        await message.reply("An error occurred while processing your message.")

async def download_handler(message: types.Message):
    """Wrapper function for handle_download to properly pass supabase"""
    await handle_download(message, supabase)

async def messages_handler(message: types.Message):
    """Wrapper function for handle_messages_download to properly pass supabase"""
    await handle_messages_download(message, supabase)

async def change_handler(message: types.Message):
    """Wrapper function for change_contact command"""
    await change_contact(message, supabase)

async def add_handler(message: types.Message):
    """Wrapper function for add_contact command"""
    await add_contact(message, supabase)

async def delete_handler(message: types.Message):
    """Wrapper function for delete_contact command"""
    await delete_contact(message, supabase)

async def download_all_wrapper(callback: types.CallbackQuery):
    await download_all_callback(callback, supabase)

async def main():
    # Initialize Bot instance
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    await dp.start_polling(bot)
    
    # Register all handlers
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.callback_query.register(geo_button, F.data == "geo")
    dp.message.register(download_handler, Command("download"))
    dp.message.register(messages_handler, Command("messages"))
    dp.message.register(
        message_handler,  # Use the wrapper function instead of lambda
        lambda message: message.text and not message.text.startswith('/')
    )

    dp.message.register(change_handler, Command("change"))
    dp.message.register(add_handler, Command("add"))
    dp.message.register(delete_handler, Command("delete"))

    dp.callback_query.register(
    download_all_wrapper,
    lambda c: c.data == "download_all"
)

    
    # Start polling
    logger.info("🤖 Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Render требует, чтобы мы "слушали" порт
    port = int(os.environ.get("PORT", 8000))
    # создаём простой async сервер-затычку
    import aiohttp
    from aiohttp import web

    async def handle(request):
        return web.Response(text="Bot is running")

    app = web.Application()
    app.router.add_get("/", handle)

    loop = asyncio.get_event_loop()
    loop.create_task(web._run_app(app, port=port))
    loop.run_until_complete(main())