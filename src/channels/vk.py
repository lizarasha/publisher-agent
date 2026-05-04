"""Публикация в VK группу."""

import logging
import requests
from config.settings import VK_ACCESS_TOKEN, VK_GROUP_ID, VK_API_VERSION

logger = logging.getLogger(__name__)

class VKPublisher:
    def __init__(self):
        self.access_token = VK_ACCESS_TOKEN
        self.group_id = VK_GROUP_ID
        self.api_version = VK_API_VERSION
    
    def publish(self, title, text, images=None):
        """Опубликовать пост на стену VK группы.
        
        Args:
            title: Заголовок поста
            text: Текст поста
            images: Список URL картинок (опционально)
        
        Returns:
            bool: Успешность публикации
        """
        try:
            # Формируем сообщение
            message = f"{title}\n\n{text}" if title else text
            
            # Если есть картинки, загружаем их на сервер VK
            attachments = []
            if images:
                photo_ids = self._upload_photos(images)
                attachments = [f"photo{pid}" for pid in photo_ids]
            
            # Публикуем пост
            params = {
                "access_token": self.access_token,
                "v": self.api_version,
                "owner_id": f"-{self.group_id}",  # Отрицательный ID для группы
                "from_group": 1,  # От имени группы
                "message": message,
                "attachments": ",".join(attachments) if attachments else None
            }
            
            response = requests.post(
                "https://api.vk.com/method/wall.post",
                params={k: v for k, v in params.items() if v is not None}
            )
            
            data = response.json()
            
            if "error" in data:
                logger.error(f"Ошибка VK API: {data['error']}")
                return False
            
            logger.info(f"Пост опубликован в VK: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при публикации в VK: {e}")
            return False
    
    def _upload_photos(self, image_urls):
        """Загрузить картинки на сервер VK и получить ID.
        
        Returns:
            list: Список ID фотографий в формате owner_id_photo_id
        """
        photo_ids = []
        
        for url in image_urls[:10]:  # Лимит 10 картинок
            try:
                # 1. Получаем URL сервера для загрузки
                upload_url_response = requests.get(
                    "https://api.vk.com/method/photos.getWallUploadServer",
                    params={
                        "access_token": self.access_token,
                        "v": self.api_version,
                        "group_id": self.group_id
                    }
                ).json()
                
                if "error" in upload_url_response:
                    logger.error(f"Ошибка получения upload_url: {upload_url_response['error']}")
                    continue
                
                upload_url = upload_url_response["response"]["upload_url"]
                
                # 2. Скачиваем картинку
                img_response = requests.get(url)
                
                # 3. Загружаем на сервер VK
                upload_response = requests.post(
                    upload_url,
                    files={"photo": ("image.jpg", img_response.content)}
                ).json()
                
                # 4. Сохраняем фото
                save_response = requests.get(
                    "https://api.vk.com/method/photos.saveWallPhoto",
                    params={
                        "access_token": self.access_token,
                        "v": self.api_version,
                        "group_id": self.group_id,
                        "photo": upload_response["photo"],
                        "server": upload_response["server"],
                        "hash": upload_response["hash"]
                    }
                ).json()
                
                if "error" in save_response:
                    logger.error(f"Ошибка сохранения фото: {save_response['error']}")
                    continue
                
                photo = save_response["response"][0]
                photo_ids.append(f"{photo['owner_id']}_{photo['id']}")
                
            except Exception as e:
                logger.error(f"Ошибка загрузки картинки {url}: {e}")
                continue
        
        return photo_ids
