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
        self.base_url = "https://api.vk.com/method"
    
    def _api_request(self, method, params=None):
        """Выполнить запрос к VK API."""
        url = f"{self.base_url}/{method}"
        if params is None:
            params = {}
        params['access_token'] = self.access_token
        params['v'] = self.api_version
        
        try:
            response = requests.post(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                error_msg = data['error'].get('error_msg', 'Unknown error')
                error_code = data['error'].get('error_code', 0)
                logger.error(f"VK API Error {error_code}: {error_msg}")
                return None
            
            return data.get('response')
        except Exception as e:
            logger.error(f"Ошибка запроса к VK API: {e}")
            return None
    
    def _upload_photo(self, image_url):
        """Загрузить фото на сервер VK и получить ID."""
        try:
            # 1. Получаем URL сервера для загрузки
            upload_data = self._api_request('photos.getWallUploadServer', {
                'group_id': self.group_id
            })
            
            if not upload_data:
                logger.error("Не удалось получить upload_url")
                return None
            
            upload_url = upload_data['upload_url']
            
            # 2. Скачиваем картинку
            img_response = requests.get(image_url, timeout=10)
            img_response.raise_for_status()
            
            # 3. Загружаем на сервер VK
            files = {'photo': ('image.jpg', img_response.content)}
            upload_response = requests.post(upload_url, files=files, timeout=30)
            upload_response.raise_for_status()
            upload_result = upload_response.json()
            
            # 4. Сохраняем фото
            save_data = self._api_request('photos.saveWallPhoto', {
                'group_id': self.group_id,
                'photo': upload_result.get('photo'),
                'server': upload_result.get('server'),
                'hash': upload_result.get('hash')
            })
            
            if save_data and len(save_data) > 0:
                photo = save_data[0]
                return f"photo{photo['owner_id']}_{photo['id']}"
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка загрузки фото: {e}")
            return None
    
    def publish(self, title, text, images=None):
        """Опубликовать пост на стену VK группы.
        
        Args:
            title: Заголовок поста (для логов, НЕ публикуется)
            text: Текст поста
            images: Список URL картинок (опционально)
        
        Returns:
            bool: Успешность публикации
        """
        try:
            # Проверяем длину текста
            if len(text) > 4096:
                logger.error(f"Текст слишком длинный: {len(text)} символов (макс. 4096)")
                return False
            
            # Формируем параметры публикации
            params = {
                'owner_id': f'-{self.group_id}',
                'from_group': 1,
                'message': text
            }
            
            # Загружаем картинки если есть
            attachments = []
            if images:
                for img_url in images[:10]:  # Лимит 10 картинок
                    photo_id = self._upload_photo(img_url)
                    if photo_id:
                        attachments.append(photo_id)
                
                if attachments:
                    params['attachments'] = ','.join(attachments)
            
            # Публикуем пост
            result = self._api_request('wall.post', params)
            
            if result and 'post_id' in result:
                post_id = result['post_id']
                logger.info(f"✅ Пост опубликован в VK: {title} (ID: {post_id})")
                return True
            else:
                logger.error(f"❌ Ошибка публикации в VK: {result}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при публикации в VK: {e}")
            return False
