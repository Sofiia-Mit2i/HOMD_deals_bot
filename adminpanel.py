import logging
from aiogram import types
from admin import is_admin

logger = logging.getLogger(__name__)

async def change_contact(message: types.Message, supabase):
    """
    Change contact for a given Team
    Example: /change Team1 contact123 M_Id123 new_contact456 M_Id456
    """
    if not await is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав для этой команды.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 5:
            await message.reply("⚠️ Формат: /change Team1 old_contact old_M_Id new_contact new_M_Id")
            return

        _, team, old_contact, old_m_id, new_contact, new_m_id = parts

        # Update in Supabase
        response = supabase.table("geo").update({
            "contact": new_contact,
            "M_Id": new_m_id
        }).match({
            "team_name": team,
            "contact": old_contact,
            "M_Id": old_m_id
        }).execute()

        if response.data:
            await message.reply(f"✅ Контакт обновлен для {team}")
        else:
            await message.reply("⚠️ Контакт не найден.")
    except Exception as e:
        logger.error(f"Error in change_contact: {str(e)}")
        await message.reply("❌ Ошибка при обновлении контакта.")


async def add_contact(message: types.Message, supabase):
    """
    Add new contact for a team
    Example: /add Team1 contact123 M_Id123
    """
    if not await is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав для этой команды.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("⚠️ Формат: /add Team1 new_contact new_M_Id")
            return

        _, team, contact, m_id = parts

        response = supabase.table("geo").insert({
            "team_name": team,
            "contact": contact,
            "M_Id": m_id
        }).execute()

        await message.reply(f"✅ Контакт {contact} добавлен в {team}")
    except Exception as e:
        logger.error(f"Error in add_contact: {str(e)}")
        await message.reply("❌ Ошибка при добавлении контакта.")


async def delete_contact(message: types.Message, supabase):
    """
    Delete contact for a team
    Example: /delete Team1 contact123 M_Id123
    """
    if not await is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав для этой команды.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("⚠️ Формат: /delete Team1 contact M_Id")
            return

        _, team, contact, m_id = parts

        response = supabase.table("geo").delete().match({
            "team_name": team,
            "contact": contact,
            "M_Id": m_id
        }).execute()

        if response.data:
            await message.reply(f"✅ Контакт {contact} удален из {team}")
        else:
            await message.reply("⚠️ Контакт не найден.")
    except Exception as e:
        logger.error(f"Error in delete_contact: {str(e)}")
        await message.reply("❌ Ошибка при удалении контакта.")
