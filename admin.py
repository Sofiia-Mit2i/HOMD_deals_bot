import logging
from typing import List

logger = logging.getLogger(__name__)

# Hardcoded admin Telegram IDs as integers
ADMIN_IDS: List[int] = [
    923423138,
    333192979
]

async def is_admin(user_id: int) -> bool:
    """
    Check if user is an admin
    Args:
        user_id (int): Telegram user ID
    Returns:
        bool: True if user is in admin list, False otherwise
    """
    try:
        return user_id in ADMIN_IDS
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return False