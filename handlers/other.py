import logging
from datetime import datetime
from aiogram import types

logger = logging.getLogger(__name__)

async def log_other_messages(message: types.Message, supabase):
    """Log messages that are not GEO codes or GEO errors"""
    try:
        now = datetime.utcnow().isoformat()
        
        response = supabase.table("messages").insert({
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "text": message.text,
            "message_date": now
        }).execute()
        
        logger.info(f"Logged other message from user {message.from_user.username}")
        return True
    except Exception as e:
        logger.error(f"Failed to log other message: {str(e)}")
        return False

async def handle_other_message(message: types.Message, supabase):
    """Handler for non-GEO messages"""
    try:
        await log_other_messages(message, supabase)
        await message.reply(
            "👋 Hi! I'm designed to help with GEO codes. "
            "Please send country codes like US, UK, AU etc. "
            "Type /start if you need help!"
        )
    except Exception as e:
        logger.error(f"Error handling other message: {str(e)}")
        await message.reply("An error occurred. Please try again later.")

# Export the functions
__all__ = ['handle_other_message', 'log_other_messages']