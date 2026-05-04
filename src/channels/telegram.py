"""Публикация в Telegram канал."""

import logging
import requests
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

logger = logging.getLogger(__name__)

class TelegramPublisher:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def _send_message(self, chat_id, text, parse_mode="Markdown"):
        """Отправить текстовое сообщение."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _send_photo(self, chat_id, photo_url, caption=None, parse_mode="Markdown"):
        """Отправить фото с подписью."""
        url = f"{self.base_url}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "parse_mode": parse_mode
        }
        if caption:
            payload["caption"] = caption[:1024]  # Лимит caption
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _send_media_group(self, chat_id, media):
        """Отправить альбом фото."""
        url = f"{self.base_url}/sendMediaGroup"
        payload = {
            "chat_id": chat_id,
            "media": media
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def send_error_to_admin(self, title, text_length):
        """Отправить ошибку админу о длинном тексте."""
        try:
            # Отправляем сообщение в канал (или можно в ЛС бота)
            error_msg = f"⚠️ ОШИБКА: Пост «{title}» слишком длинный ({text_length} символов). Максимум 4096."
            self._send_message(self.channel_id, error_msg)
            logger.warning(f"Отправлена ошибка о длинном посте: {title}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")
            return False
    
    def publish(self, title, text, images=None):
        """Опубликовать пост в Telegram канал.
        
        Args:
            title: Заголовок поста (для логов и ошибок, НЕ публикуется)
            text: Текст поста (без заголовка)
            images: Список URL картинок (опционально)
        
        Returns:
            bool: Успешность публикации
        """
        try:
            # Проверяем длину текста
            if len(text) > 4096:
                logger.error(f"Текст слишком длинный: {len(text)} символов (макс. 4096)")
                self.send_error_to_admin(title, len(text))
                return False
            
            # Отправляем картинки если есть
            if images:
                if len(images) == 1:
                    # Одна картинка - отправляем с текстом
                    self._send_photo(
                        chat_id=self.channel_id,
                        photo_url=images[0],
                        caption=text
                    )
                else:
                    # Несколько картинок - отправляем альбом
                    media = []
                    for i, img in enumerate(images[:10]):  # Лимит 10 картинок
                        if i == 0:
                            media.append({
                                "type": "photo",
                                "media": img,
                                "caption": text[:1024] if len(text) <= 1024 else "",
                                "parse_mode": "Markdown"
                            })
                        else:
                            media.append({"type": "photo", "media": img})
                    
                    self._send_media_group(
                        chat_id=self.channel_id,
                        media=media
                    )
                    
                    # Если текст длинный (но <= 4096), отправляем отдельно
                    if len(text) > 1024:
                        self._send_message(
                            chat_id=self.channel_id,
                            text=text
                        )
            else:
                # Только текст
                self._send_message(
                    chat_id=self.channel_id,
                    text=text
                )
            
            logger.info(f"✅ Пост опубликован в Telegram: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при публикации в Telegram: {e}")
            return False
