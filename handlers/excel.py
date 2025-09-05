import logging
import pandas as pd
from aiogram import types
from aiogram.filters import Command

from getexcel import send_team_excel
from admin import is_admin
from io import BytesIO

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

async def handle_messages_download(message: types.Message, supabase):
    """Handle the messages command to generate Excel reports for admins"""
    try:
        user_id = message.from_user.id
        
        # Check if user is admin
        if not await is_admin(user_id):
            await message.reply("❌ You are not authorized to use this command.")
            return

        logger.info(f"Messages download requested by admin {user_id}")
        
        # Get data from messages table
        response = supabase.table("messages")\
            .select("*")\
            .order("message_date", desc=True)\
            .execute()
        
        if not response.data:
            await message.reply("📊 No messages found in the database.")
            return

        # Create Excel in memory
        df = pd.DataFrame(response.data)
        
        # Convert all columns to string
        for column in df.columns:
            df[column] = df[column].astype(str)

        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        excel_file = BufferedInputFile(
            buffer.getvalue(),
            filename="messages.xlsx"
        )

        await message.reply_document(
            document=excel_file,
            caption="📊 Messages database export"
        )
        logger.info(f"Successfully sent messages Excel file to admin {user_id}")
    
    except Exception as e:
        error_msg = f"Error handling messages download: {str(e)}"
        logger.error(error_msg)
        await message.reply("❌ Error generating report. Please try again later.")