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



async def main():
    # Initialize Bot instance
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    
    # Register all handlers
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.callback_query.register(geo_button, F.data == "geo")
    dp.message.register(download_handler, Command("download"))
    dp.message.register(messages_handler, Command("messages"))
    dp.message.register(
        message_handler,  # Use the wrapper function instead of lambda
        lambda message: message.text and not message.text.startswith('/')
    )

    # Start polling
    logger.info("🤖 Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())