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
    /change Team1 old_contact new_contact
    """
    if not await is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав для этой команды.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("⚠️ Формат: /change Team1 old_contact new_contact")
            return

        _, team, old_contact, new_contact = parts

        # Получаем текущий массив контактов
        resp = supabase.table("geo").select("contact").eq("team_name", team).execute()
        if not resp.data:
            await message.reply("⚠️ Команда не найдена.")
            return

        current_contacts = resp.data[0]["contact"]  # обычно это список
        if old_contact not in current_contacts:
            await message.reply("⚠️ Старый контакт не найден в списке.")
            return

        # Заменяем старый контакт на новый
        updated_contacts = [
            new_contact if c == old_contact else c
            for c in current_contacts
        ]

        # Обновляем таблицу, преобразовав в Postgres array literal
        array_literal = "{" + ",".join(updated_contacts) + "}"

        supabase.table("geo").update({
            "contact": array_literal
        }).eq("team_name", team).execute()

        await message.reply(f"✅ Контакт обновлен для {team}")

    except Exception as e:
        logger.error(f"Error in change_contact: {str(e)}")
        await message.reply("❌ Ошибка при обновлении контакта.")

async def add_contact(message: types.Message, supabase):
    """
    /add Team1 new_contact
    Добавляет новый контакт к существующему массиву контактов.
    Если команда не существует, создаёт новую запись.
    """
    if not await is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав для этой команды.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply("⚠️ Формат: /add Team1 new_contact")
            return

        _, team, contact = parts

        # Проверяем, есть ли уже запись для команды
        existing = supabase.table("geo").select("contact").eq("team_name", team).execute()

        if existing.data and len(existing.data) > 0:
            old_contacts = existing.data[0].get("contact", [])
            if contact in old_contacts:
                await message.reply(f"⚠️ Контакт {contact} уже существует в {team}")
                return

            new_contacts = old_contacts + [contact]  # объединяем массивы
            supabase.table("geo").update({
                "contact": new_contacts
            }).eq("team_name", team).execute()
            await message.reply(f"✅ Контакт {contact} добавлен к {team}")
        else:
            # Если команды нет — создаём новую запись
            supabase.table("geo").insert({
                "team_name": team,
                "contact": [contact],
                "geos": []  # можно оставить пустым массивом
            }).execute()
            await message.reply(f"✅ Команда {team} создана с контактом {contact}")

    except Exception as e:
        logger.error(f"Error in add_contact: {str(e)}")
        await message.reply("❌ Ошибка при добавлении контакта.")



async def delete_contact(message: types.Message, supabase):
    """
    /delete Team1 contact
    """
    if not await is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав для этой команды.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply("⚠️ Формат: /delete Team1 contact")
            return

        _, team, *contact_parts = parts
        contact = " ".join(contact_parts)

        # Получаем текущий массив контактов
        resp = supabase.table("geo").select("contact").eq("team_name", team).execute()
        if not resp.data:
            await message.reply("⚠️ Команда не найдена.")
            return

        current_contacts = resp.data[0]["contact"]
        if contact not in current_contacts:
            await message.reply("⚠️ Контакт не найден.")
            return

        # Удаляем контакт
        updated_contacts = [c for c in current_contacts if c != contact]

        # Формируем корректный Postgres array literal
        array_literal = "{" + ",".join(updated_contacts) + "}" if updated_contacts else "{}"

        supabase.table("geo").update({
            "contact": array_literal
        }).eq("team_name", team).execute()

        await message.reply(f"✅ Контакт {contact} удален из {team}")

    except Exception as e:
        logger.error(f"Error in delete_contact: {str(e)}")
        await message.reply("❌ Ошибка при удалении контакта.")
