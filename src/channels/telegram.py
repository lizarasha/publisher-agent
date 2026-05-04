"""Публикация в Telegram канал."""

import logging
from telegram import Bot
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

logger = logging.getLogger(__name__)

class TelegramPublisher:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.channel_id = TELEGRAM_CHANNEL_ID
    
    async def publish(self, title, text, images=None):
        """Опубликовать пост в Telegram канал.
        
        Args:
            title: Заголовок поста
            text: Текст поста
            images: Список URL картинок (опционально)
        
        Returns:
            bool: Успешность публикации
        """
        try:
            # Формируем сообщение
            message = f"*{title}*\n\n{text}" if title else text
            
            # Отправляем картинки если есть
            if images:
                if len(images) == 1:
                    # Одна картинка - отправляем с текстом
                    await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=images[0],
                        caption=message[:1024],  # Лимит caption в Telegram
                        parse_mode="Markdown"
                    )
                    # Если текст длинный, отправляем остаток отдельно
                    if len(message) > 1024:
                        await self.bot.send_message(
                            chat_id=self.channel_id,
                            text=message[1024:4096],  # Лимит сообщения
                            parse_mode="Markdown"
                        )
                else:
                    # Несколько картинок - отправляем альбом
                    media = []
                    for i, img in enumerate(images[:10]):  # Лимит 10 картинок
                        if i == 0:
                            media.append({
                                "type": "photo",
                                "media": img,
                                "caption": message[:1024] if len(message) <= 1024 else title[:1024],
                                "parse_mode": "Markdown"
                            })
                        else:
                            media.append({"type": "photo", "media": img})
                    
                    await self.bot.send_media_group(
                        chat_id=self.channel_id,
                        media=media
                    )
                    
                    # Если текст длинный, отправляем остаток
                    if len(message) > 1024:
                        await self.bot.send_message(
                            chat_id=self.channel_id,
                            text=message[1024:4096],
                            parse_mode="Markdown"
                        )
            else:
                # Только текст
                # Разбиваем на части если длиннее 4096 символов
                parts = [message[i:i+4096] for i in range(0, len(message), 4096)]
                for part in parts:
                    await self.bot.send_message(
                        chat_id=self.channel_id,
                        text=part,
                        parse_mode="Markdown"
                    )
            
            logger.info(f"Пост опубликован в Telegram: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при публикации в Telegram: {e}")
            return False
