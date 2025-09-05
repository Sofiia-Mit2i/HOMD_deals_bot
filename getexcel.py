from io import BytesIO
import pandas as pd
import logging
from aiogram import types
from aiogram.filters import Command
from aiogram.types import FSInputFile, BufferedInputFile

logger = logging.getLogger(__name__)

async def get_team_by_user_id(supabase, user_id: int):
    """
    Returns team name for manager with given Telegram ID
    """
    try:
        response = supabase.table("geo") \
            .select("team_name") \
            .contains("M_Id", [str(user_id)]) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["team_name"]
        logger.info(f"No team found for user_id: {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error in get_team_by_user_id: {str(e)}")
        return None

async def send_team_excel(message: types.Message, supabase):
    """
    Sends Excel file with team data to the manager
    """
    try:
        user_id = message.from_user.id
        team_name = await get_team_by_user_id(supabase, user_id)
        
        logger.info(f"Processing download request for user {user_id}, team: {team_name}")

        if not team_name:
            await message.reply("❌ You are not authorized to download any data.")
            return

        # Get data from team-specific requests table
        table_name = f"{team_name.lower()}_requests"
        response = supabase.table(table_name)\
            .select("*")\
            .order("request_date", desc=True)\
            .execute()
        
        if not response.data:
            await message.reply("📊 No requests found for your team.")
            return

        # Create Excel in memory
        df = pd.DataFrame(response.data)
        
        # Convert all columns to string to prevent type errors
        for column in df.columns:
            df[column] = df[column].astype(str)

        # Save to BytesIO
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        # Convert BytesIO to BufferedInputFile
        excel_file = BufferedInputFile(
            buffer.getvalue(),
            filename=f"{team_name}_requests.xlsx"
        )

        # Send file through Telegram
        await message.reply_document(
            document=excel_file,
            caption=f"📊 Request data for team {team_name}"
        )
        logger.info(f"Successfully sent Excel file for team {team_name}")
        
    except Exception as e:
        error_msg = f"Error generating Excel for user {message.from_user.id}: {str(e)}"
        logger.error(error_msg)
        await message.reply("❌ Error generating report. Please try again later.")