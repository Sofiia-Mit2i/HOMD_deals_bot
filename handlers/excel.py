import logging
from aiogram import types
from aiogram.filters import Command
from getexcel import send_team_excel
logger = logging.getLogger(__name__)

async def handle_download(message: types.Message, supabase):
    """
    Handle the download command to generate Excel reports
    """
    
    try:
        logger.info(f"Download requested by user {message.from_user.id}")
        await send_team_excel(message, supabase)
    except Exception as e:
        logger.error(f"Error handling download: {str(e)}")
        await message.reply("❌ An error occurred while processing your request.")