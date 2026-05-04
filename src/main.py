"""Главный файл агента Публикатора."""

import logging
import time
from datetime import datetime

from config.settings import check_required_vars
from src.notion_client import NotionClient
from src.channels.telegram import TelegramPublisher

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
    
    def process_telegram_posts(self):
        """Обработать и опубликовать посты для Telegram."""
        logger.info("=== Проверка постов для Telegram ===\n")
        
        # 1. Получаем все страницы со статусом "Готово"
        all_ready = self.notion.get_ready_posts()
        logger.info(f"Всего страниц со статусом 'Готово': {len(all_ready)}")
        
        if not all_ready:
            logger.info("Нет постов для публикации\n")
            return
        
        # 2. Фильтруем только те, где Платформа содержит Telegram и Тип = Пост
        telegram_posts = []
        for page in all_ready:
            props = self.notion.get_page_properties(page)
            channels = props.get("channels", [])
            content_type = props.get("content_type", "")
            
            if "Telegram" in channels and content_type == "Пост":
                telegram_posts.append(page)
                logger.info(f"Найден пост для Telegram: {props.get('title', 'Без названия')}")
        
        if not telegram_posts:
            logger.info("Нет постов для Telegram (тип 'Пост')\n")
            return
        
        logger.info(f"Постов для публикации в Telegram: {len(telegram_posts)}\n")
        
        # 3. Обрабатываем каждый пост
        for page in telegram_posts:
            try:
                props = self.notion.get_page_properties(page)
                page_id = props["id"]
                title = props.get("title", "Без названия")
                
                logger.info(f"Обработка: {title}")
                
                # Получаем контент страницы (блоки)
                blocks = self.notion.get_page_content(page_id)
                logger.info(f"  Блоков в контенте: {len(blocks)}")
                
                # Извлекаем текст (без заголовка Name)
                text = self.notion.extract_text_from_blocks(blocks)
                images = self.notion.extract_images(blocks)
                
                logger.info(f"  Длина текста: {len(text)} символов")
                logger.info(f"  Картинок: {len(images)}")
                
                # Проверяем длину
                if len(text) > 4096:
                    logger.warning(f"  ⚠️ Текст слишком длинный ({len(text)} символов)")
                    self.telegram.send_error_to_admin(title, len(text))
                    continue
                
                # Публикуем в Telegram
                logger.info(f"  Отправка в Telegram...")
                result = self.telegram.publish(
                    title=title,  # Для логов и ошибок
                    text=text,    # Только текст без заголовка
                    images=images
                )
                
                if result:
                    # Обновляем статус
                    self.notion.update_post_status(page_id, "Опубликовано")
                    logger.info(f"  ✅ Успешно опубликовано\n")
                else:
                    logger.error(f"  ❌ Ошибка публикации\n")
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке поста: {e}\n")
                continue
    
    def run(self):
        """Запустить агента один раз."""
        logger.info("\n" + "="*60)
        logger.info("🚀 Агент Публикатор запущен")
        logger.info("="*60 + "\n")
        
        try:
            self.process_telegram_posts()
        except Exception as e:
            logger.error(f"Ошибка в главном цикле: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("🏁 Работа завершена")
        logger.info("="*60 + "\n")

def main():
    """Точка входа."""
    agent = PublisherAgent()
    agent.run()

if __name__ == "__main__":
    main()
