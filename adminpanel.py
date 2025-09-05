import logging
from aiogram import types
from admin import is_admin

logger = logging.getLogger(__name__)

def normalize_value(value, numeric=False):
    """
    Приводим данные к массиву для Supabase
    """
    if isinstance(value, list):
        return value
    if numeric:
        try:
            return [int(value)]
        except ValueError:
            return [value]
    return [value]

async def change_contact(message: types.Message, supabase):
    """
    /change Team1 old_contact old_M_Id new_contact new_M_Id
    """
    if not await is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав для этой команды.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 6:
            await message.reply("⚠️ Формат: /change Team1 old_contact old_M_Id new_contact new_M_Id")
            return

        _, team, old_contact, old_m_id, new_contact, new_m_id = parts

        response = supabase.table("geo").update({
            "contact": normalize_value(new_contact),
            "M_Id": normalize_value(new_m_id, numeric=True)
        }).match({
            "team_name": team,
            "contact": normalize_value(old_contact),
            "M_Id": normalize_value(old_m_id, numeric=True)
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
    /add Team1 new_contact new_M_Id
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
            "contact": normalize_value(contact),
            "M_Id": normalize_value(m_id, numeric=True)
        }).execute()

        await message.reply(f"✅ Контакт {contact} добавлен в {team}")
    except Exception as e:
        logger.error(f"Error in add_contact: {str(e)}")
        await message.reply("❌ Ошибка при добавлении контакта.")


async def delete_contact(message: types.Message, supabase):
    """
    /delete Team1 contact M_Id
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
            "contact": normalize_value(contact),
            "M_Id": normalize_value(m_id, numeric=True)
        }).execute()

        if response.data:
            await message.reply(f"✅ Контакт {contact} удален из {team}")
        else:
            await message.reply("⚠️ Контакт не найден.")
    except Exception as e:
        logger.error(f"Error in delete_contact: {str(e)}")
        await message.reply("❌ Ошибка при удалении контакта.")
