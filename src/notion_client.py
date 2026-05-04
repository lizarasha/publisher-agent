"""Клиент для работы с Notion API."""

import logging
from notion_client import Client
from config.settings import NOTION_TOKEN, NOTION_DATABASE_ID

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self):
        self.client = Client(auth=NOTION_TOKEN)
        self.database_id = NOTION_DATABASE_ID
    
    def get_ready_posts(self):
        """Получить посты со статусом 'Готово к публикации'."""
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Статус",
                    "select": {
                        "equals": "Готово к публикации"
                    }
                }
            )
            return response["results"]
        except Exception as e:
            logger.error(f"Ошибка при получении постов из Notion: {e}")
            return []
    
    def update_post_status(self, page_id, status="Опубликовано"):
        """Обновить статус поста."""
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Статус": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            logger.info(f"Статус поста {page_id} обновлен на '{status}'")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса: {e}")
            return False
    
    def get_page_content(self, page_id):
        """Получить контент страницы (блоки)."""
        try:
            blocks = self.client.blocks.children.list(block_id=page_id)
            return blocks["results"]
        except Exception as e:
            logger.error(f"Ошибка при получении контента страницы: {e}")
            return []
    
    def extract_text_from_blocks(self, blocks):
        """Извлечь текст из блоков Notion в формате для публикации."""
        text_parts = []
        
        for block in blocks:
            block_type = block["type"]
            
            if block_type == "paragraph":
                text = self._extract_rich_text(block["paragraph"]["rich_text"])
                if text:
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
        return "".join([text["plain_text"] for text in rich_text_array])
    
    def get_page_properties(self, page):
        """Получить свойства страницы."""
        properties = page.get("properties", {})
        
        result = {
            "id": page["id"],
            "url": page["url"],
        }
        
        # Название
        if "Название" in properties:
            title = properties["Название"]["title"]
            result["title"] = "".join([t["plain_text"] for t in title]) if title else ""
        
        # Каналы
        if "Каналы" in properties:
            multi_select = properties["Каналы"]["multi_select"]
            result["channels"] = [item["name"] for item in multi_select]
        else:
            result["channels"] = []
        
        return result
