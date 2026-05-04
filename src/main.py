"""Главный файл агента Публикатора."""

import asyncio
import logging
import time
from datetime import datetime

from config.settings import check_required_vars
from src.notion_client import NotionClient
from src.channels.telegram import TelegramPublisher
from src.channels.vk import VKPublisher

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class PublisherAgent:
    def __init__(self):
        check_required_vars()
        self.notion = NotionClient()
        self.telegram = TelegramPublisher()
        self.vk = VKPublisher()
    
    async def process_ready_posts(self):
        """Обработать посты, готовые к публикации."""
        logger.info("Проверка новых постов в Notion...")
        
        # Получаем посты со статусом "Готово к публикации"
        posts = self.notion.get_ready_posts()
        
        if not posts:
            logger.info("Нет постов для публикации")
            return
        
        logger.info(f"Найдено постов для публикации: {len(posts)}")
        
        for post in posts:
            try:
                # Получаем свойства поста
                properties = self.notion.get_page_properties(post)
                page_id = properties["id"]
                title = properties.get("title", "")
                channels = properties.get("channels", [])
                
                logger.info(f"Обработка поста: {title}")
                
                # Получаем контент страницы
                blocks = self.notion.get_page_content(page_id)
                text = self.notion.extract_text_from_blocks(blocks)
                images = self.notion.extract_images(blocks)
                
                # Публикуем в выбранные каналы
                success = True
                
                if "Telegram" in channels:
                    logger.info("Публикация в Telegram...")
                    telegram_result = await self.telegram.publish(title, text, images)
                    if not telegram_result:
                        success = False
                
                if "VK" in channels:
                    logger.info("Публикация в VK...")
                    vk_result = self.vk.publish(title, text, images)
                    if not vk_result:
                        success = False
                
                # Обновляем статус
                if success:
                    self.notion.update_post_status(page_id, "Опубликовано")
                    logger.info(f"Пост '{title}' успешно опубликован")
                else:
                    logger.warning(f"Пост '{title}' опубликован с ошибками")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке поста: {e}")
                continue
    
    async def run(self):
        """Запустить агента в режиме ожидания."""
        logger.info("=== Агент Публикатор запущен ===")
        logger.info("Ожидание постов со статусом 'Готово к публикации'...")
        
        while True:
            try:
                await self.process_ready_posts()
            except Exception as e:
                logger.error(f"Ошибка в главном цикле: {e}")
            
            # Проверяем каждые 5 минут
            logger.info("Ожидание 5 минут до следующей проверки...")
            await asyncio.sleep(300)

async def main():
    """Точка входа."""
    agent = PublisherAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
