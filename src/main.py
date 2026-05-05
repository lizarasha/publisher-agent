"""Главный файл агента Публикатора."""

import logging
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
    
    def process_posts(self):
        """Обработать и опубликовать посты для всех платформ."""
        logger.info("=== Проверка постов для публикации ===\n")
        
        stats = {
            'total_ready': 0,
            'telegram_posts': 0,
            'vk_posts': 0,
            'published': 0,
            'errors': 0
        }
        
        # 1. Получаем все страницы со статусом "Готово"
        all_ready = self.notion.get_ready_posts()
        stats['total_ready'] = len(all_ready)
        logger.info(f"Всего страниц со статусом 'Готово': {len(all_ready)}")
        
        if not all_ready:
            logger.info("Нет постов для публикации\n")
            self.telegram.send_notification_to_admin(
                "ℹ️ Проверка завершена\n\n"
                "Нет постов со статусом 'Готово' для публикации."
            )
            return stats
        
        # 2. Фильтруем посты по платформам
        telegram_posts = []
        vk_posts = []
        
        for page in all_ready:
            props = self.notion.get_page_properties(page)
            channels = props.get("channels", [])
            content_type = props.get("content_type", "")
            
            if "Telegram" in channels and content_type == "Пост":
                telegram_posts.append(page)
                logger.info(f"Найден пост для Telegram: {props.get('title', 'Без названия')}")
            
            if "VK" in channels and content_type == "Пост":
                vk_posts.append(page)
                logger.info(f"Найден пост для VK: {props.get('title', 'Без названия')}")
        
        stats['telegram_posts'] = len(telegram_posts)
        stats['vk_posts'] = len(vk_posts)
        
        if not telegram_posts and not vk_posts:
            logger.info("Нет постов для публикации\n")
            self.telegram.send_notification_to_admin(
                f"ℹ️ Проверка завершена\n\n"
                f"Найдено постов со статусом 'Готово': {stats['total_ready']}\n"
                f"Из них для Telegram: 0\n"
                f"Из них для VK: 0\n\n"
                f"Нет постов для публикации."
            )
            return stats
        
        # 3. Обрабатываем Telegram
        if telegram_posts:
            logger.info(f"\n📱 Публикация в Telegram: {len(telegram_posts)} постов\n")
            for page in telegram_posts:
                try:
                    props = self.notion.get_page_properties(page)
                    page_id = props["id"]
                    title = props.get("title", "Без названия")
                    
                    logger.info(f"Обработка Telegram: {title}")
                    
                    blocks = self.notion.get_page_content(page_id)
                    text = self.notion.extract_text_from_blocks(blocks)
                    images = self.notion.extract_images(blocks)
                    
                    logger.info(f"  Длина текста: {len(text)} символов")
                    logger.info(f"  Картинок: {len(images)}")
                    
                    if len(text) > 4096:
                        logger.warning(f"  ⚠️ Текст слишком длинный ({len(text)} символов)")
                        self.telegram.send_error_to_admin(title, len(text))
                        stats['errors'] += 1
                        continue
                    
                    result = self.telegram.publish(title=title, text=text, images=images)
                    
                    if result:
                        self.notion.update_post_status(page_id, "Опубликовано")
                        logger.info(f"  ✅ Опубликовано в Telegram\n")
                        stats['published'] += 1
                    else:
                        logger.error(f"  ❌ Ошибка публикации в Telegram\n")
                        stats['errors'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке Telegram поста: {e}\n")
                    stats['errors'] += 1
                    continue
        
        # 4. Обрабатываем VK
        if vk_posts:
            logger.info(f"\n🔵 Публикация в VK: {len(vk_posts)} постов\n")
            for page in vk_posts:
                try:
                    props = self.notion.get_page_properties(page)
                    page_id = props["id"]
                    title = props.get("title", "Без названия")
                    
                    logger.info(f"Обработка VK: {title}")
                    
                    blocks = self.notion.get_page_content(page_id)
                    text = self.notion.extract_text_from_blocks(blocks)
                    images = self.notion.extract_images(blocks)
                    
                    logger.info(f"  Длина текста: {len(text)} символов")
                    logger.info(f"  Картинок: {len(images)}")
                    
                    if len(text) > 4096:
                        logger.warning(f"  ⚠️ Текст слишком длинный ({len(text)} символов)")
                        stats['errors'] += 1
                        continue
                    
                    result = self.vk.publish(title=title, text=text, images=images)
                    
                    if result:
                        self.notion.update_post_status(page_id, "Опубликовано")
                        logger.info(f"  ✅ Опубликовано в VK\n")
                        stats['published'] += 1
                    else:
                        logger.error(f"  ❌ Ошибка публикации в VK\n")
                        stats['errors'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке VK поста: {e}\n")
                    stats['errors'] += 1
                    continue
        
        return stats
    
    def run(self):
        """Запустить агента один раз."""
        logger.info("\n" + "="*60)
        logger.info("🚀 Агент Публикатор запущен")
        logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60 + "\n")
        
        try:
            stats = self.process_posts()
            
            # Отправляем итоговое уведомление
            if stats:
                message = (
                    f"📊 Отчет о работе\n\n"
                    f"Постов со статусом 'Готово': {stats['total_ready']}\n"
                    f"📱 Для Telegram: {stats['telegram_posts']}\n"
                    f"🔵 Для VK: {stats['vk_posts']}\n"
                    f"✅ Опубликовано: {stats['published']}\n"
                    f"❌ Ошибок: {stats['errors']}\n\n"
                )
                
                if stats['published'] > 0:
                    message += "Работа завершена успешно!"
                elif stats['errors'] > 0:
                    message += "Возникли ошибки при публикации."
                else:
                    message += "Нет постов для публикации."
                
                self.telegram.send_notification_to_admin(message)
                
        except Exception as e:
            logger.error(f"Ошибка в главном цикле: {e}")
            self.telegram.send_notification_to_admin(
                f"❌ Ошибка работы агента:\n\n{e}"
            )
        
        logger.info("\n" + "="*60)
        logger.info("🏁 Работа завершена")
        logger.info("="*60 + "\n")

def main():
    """Точка входа."""
    agent = PublisherAgent()
    agent.run()

if __name__ == "__main__":
    main()
