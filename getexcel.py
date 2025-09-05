from io import BytesIO
import pandas as pd
import logging
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from admin import is_admin  # твоя проверка админов

logger = logging.getLogger(__name__)

# список всех команд (их имена совпадают с team_name в geo)
TEAMS = ["Team1", "Team2", "Team3", "Team4", "Team5", "Team6", "Team7"]

async def send_team_excel(message: types.Message, supabase):
    """
    Admin-only command to download request tables.
    Usage:
      /download Team1 Team2 ...
      /download all
    """
    try:
        user_id = message.from_user.id
        if not await is_admin(user_id):
            await message.reply("❌ У вас нет прав для этой команды.")
            return

        parts = message.text.split()
        if len(parts) == 1:
            # Нет аргументов — показать справку и кнопку "all"
            kb = InlineKeyboardBuilder()
            kb.button(text="📥 Скачать все", callback_data="download_all")
            await message.reply(
                "⚠️ Использование команды:\n"
                "`/download Team1 Team2 ...`\n"
                "или `/download all` чтобы скачать все таблицы.",
                parse_mode="Markdown",
                reply_markup=kb.as_markup()
            )
            return

        targets = parts[1:]
        tables = []

        if "all" in [t.lower() for t in targets]:
            tables = [f"{team.lower()}_requests" for team in TEAMS]
        else:
            tables = [f"{team.lower()}_requests" for team in targets if team in TEAMS]

        if not tables:
            await message.reply("⚠️ Таблицы не найдены. Проверьте названия команд.")
            return

        for table_name in tables:
            try:
                response = supabase.table(table_name)\
                    .select("*")\
                    .order("request_date", desc=True)\
                    .execute()
                
                if not response.data:
                    await message.reply(f"📊 В таблице {table_name} нет данных.")
                    continue

                # DataFrame → Excel
                df = pd.DataFrame(response.data)
                for col in df.columns:
                    df[col] = df[col].astype(str)

                buffer = BytesIO()
                df.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)

                file = types.BufferedInputFile(
                    buffer.getvalue(),
                    filename=f"{table_name}.xlsx"
                )

                await message.reply_document(
                    document=file,
                    caption=f"📊 Данные из {table_name}"
                )
                logger.info(f"✅ Sent {table_name} to admin {user_id}")

            except Exception as table_err:
                logger.error(f"Error exporting {table_name}: {str(table_err)}")
                await message.reply(f"❌ Ошибка при экспорте {table_name}")

    except Exception as e:
        logger.error(f"Error in send_team_excel: {str(e)}")
        await message.reply("❌ Ошибка при генерации отчета.")
