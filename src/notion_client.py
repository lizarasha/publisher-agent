"""Клиент для работы с Notion API."""

import logging
import requests
from config.settings import NOTION_TOKEN, NOTION_DATABASE_ID

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self):
        self.token = NOTION_TOKEN
        self.database_id = NOTION_DATABASE_ID
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method, endpoint, data=None):
        """Выполнить запрос к Notion API."""
        url = f'https://api.notion.com/v1/{endpoint}'
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_ready_posts(self):
        """Получить посты со статусом 'Готово'."""
        try:
            data = self._request('POST', f'databases/{self.database_id}/query', {
                'filter': {
                    'property': 'Статус',
                    'select': {
                        'equals': 'Готово'
                    }
                }
            })
            return data.get('results', [])
        except Exception as e:
            logger.error(f"Ошибка при получении постов из Notion: {e}")
            return []
    
    def update_post_status(self, page_id, status="Опубликовано"):
        """Обновить статус поста."""
        try:
            self._request('PATCH', f'pages/{page_id}', {
                'properties': {
                    'Статус': {
                        'select': {
                            'name': status
                        }
                    }
                }
            })
            logger.info(f"Статус поста {page_id} обновлен на '{status}'")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса: {e}")
            return False
    
    def get_page_content(self, page_id):
        """Получить контент страницы (блоки)."""
        try:
            data = self._request('GET', f'blocks/{page_id}/children')
            return data.get('results', [])
        except Exception as e:
            logger.error(f"Ошибка при получении контента страницы: {e}")
            return []
    
    def extract_text_from_blocks(self, blocks):
        """Извлечь текст из блоков Notion в формате для публикации."""
        text_parts = []
        first_paragraph = True
        
        for block in blocks:
            block_type = block["type"]
            
            if block_type == "paragraph":
                text = self._extract_rich_text(block["paragraph"]["rich_text"])
                if text:
                    # Первый абзац делаем жирным
                    if first_paragraph:
                        text_parts.append(f"*{text}*")
                        first_paragraph = False
                    else:
                        text_parts.append(text)
            
            elif block_type == "heading_1":
                text = self._extract_rich_text(block["heading_1"]["rich_text"])
                if text:
                    text_parts.append(f"*{text}*")  # Жирный для Telegram
            
            elif block_type == "heading_2":
                text = self._extract_rich_text(block["heading_2"]["rich_text"])
                if text:
                    text_parts.append(f"*{text}*")
            
            elif block_type == "heading_3":
                text = self._extract_rich_text(block["heading_3"]["rich_text"])
                if text:
                    text_parts.append(f"_{text}_")  # Курсив
            
            elif block_type == "bulleted_list_item":
                text = self._extract_rich_text(block["bulleted_list_item"]["rich_text"])
                if text:
                    text_parts.append(f"• {text}")
            
            elif block_type == "numbered_list_item":
                text = self._extract_rich_text(block["numbered_list_item"]["rich_text"])
                if text:
                    text_parts.append(f"1. {text}")
            
            elif block_type == "quote":
                text = self._extract_rich_text(block["quote"]["rich_text"])
                if text:
                    text_parts.append(f"> {text}")
            
            elif block_type == "divider":
                text_parts.append("---")
            
            elif block_type == "image":
                url = self._get_image_url(block)
                if url:
                    text_parts.append(f"[IMAGE:{url}]")
        
        return "\n\n".join(text_parts)
    
    def extract_images(self, blocks):
        """Извлечь URL картинок из блоков."""
        images = []
        for block in blocks:
            if block["type"] == "image":
                url = self._get_image_url(block)
                if url:
                    images.append(url)
        return images
    
    def _get_image_url(self, block):
        """Получить URL картинки из блока."""
        if "file" in block["image"]:
            return block["image"]["file"]["url"]
        elif "external" in block["image"]:
            return block["image"]["external"]["url"]
        return None
    
    def _extract_rich_text(self, rich_text_array):
        """Извлечь текст из rich_text массива."""
        if not rich_text_array:
            return ""
        return "".join([text.get("plain_text", "") for text in rich_text_array])
    
    def get_page_properties(self, page):
        """Получить свойства страницы."""
        properties = page.get("properties", {})
        
        result = {
            "id": page["id"],
            "url": page["url"],
        }
        
        # Название (Name или Название)
        title = ""
        if "Name" in properties and properties["Name"]["title"]:
            title = "".join([t.get("plain_text", "") for t in properties["Name"]["title"]])
        elif "Название" in properties and properties["Название"]["title"]:
            title = "".join([t.get("plain_text", "") for t in properties["Название"]["title"]])
        result["title"] = title
        
        # Каналы (Platform в твоей базе)
        if "Платформа" in properties:
            multi_select = properties["Платформа"]["multi_select"]
            result["channels"] = [item["name"] for item in multi_select]
        else:
            result["channels"] = []
        
        # Тип контента
        if "Тип контента" in properties:
            select = properties["Тип контента"]["select"]
            result["content_type"] = select["name"] if select else ""
        else:
            result["content_type"] = ""
        
        return result
