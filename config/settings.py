"""Конфигурация проекта."""

import os
from dotenv import load_dotenv

load_dotenv()

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# VK
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")
VK_API_VERSION = "5.199"

# Проверка обязательных переменных
def check_required_vars():
    """Проверить, что все обязательные переменные заданы."""
    required = {
        "NOTION_TOKEN": NOTION_TOKEN,
        "NOTION_DATABASE_ID": NOTION_DATABASE_ID,
    }
    
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(
            f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}\n"
            f"Скопируй .env.example в .env и заполни своими данными."
        )
    
    return True
