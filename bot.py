import logging
import os
import asyncio
import json
from aiogram import Bot, Dispatcher,  types 
from aiogram.filters import Command
from aiogram import F
from supabase import create_client
from dotenv import load_dotenv

from handlers.geo import handle_geos
from handlers import cmd_start, geo_button
from handlers.excel import handle_download

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

async def message_handler(message: types.Message):
    """Wrapper function for handle_geos to properly await it"""
    await handle_geos(message, supabase, COUNTRY_MAP)

async def download_handler(message: types.Message):
    """Wrapper function for handle_download to properly pass supabase"""
    await handle_download(message, supabase)

async def main():
    # Initialize Bot instance
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    
    # Register all handlers
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.callback_query.register(geo_button, F.data == "geo")
    dp.message.register(download_handler, Command("download"))
    dp.message.register(
        message_handler,  # Use the wrapper function instead of lambda
        lambda message: message.text and not message.text.startswith('/')
    )

    # Start polling
    logger.info("🤖 Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())