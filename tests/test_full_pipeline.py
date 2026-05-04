"""Тестирование полной цепочки чтения из Notion."""

import sys
sys.path.insert(0, '/tmp/publisher-agent')

from src.notion_client import NotionClient

def test_full_pipeline():
    print("=== Тестирование чтения из Notion ===\n")
    
    client = NotionClient()
    
    # 1. Получаем страницы со статусом "Готово"
    print("1. Получаем страницы со статусом 'Готово'...")
    ready_pages = client.get_ready_posts()
    print(f"   ✅ Найдено: {len(ready_pages)}\n")
    
    if not ready_pages:
        print("   ⚠️ Нет страниц для публикации")
        return
    
    # 2. Обрабатываем первую страницу
    page = ready_pages[0]
    props = client.get_page_properties(page)
    
    print("2. Свойства страницы:")
    print(f"   Название: {props['title']}")
    print(f"   ID: {props['id']}")
    print(f"   Каналы: {', '.join(props['channels']) if props['channels'] else 'Не указаны'}")
    print(f"   Тип: {props.get('content_type', 'Не указан')}\n")
    
    # 3. Читаем контент
    print("3. Читаем контент страницы...")
    blocks = client.get_page_content(props['id'])
    print(f"   ✅ Блоков: {len(blocks)}\n")
    
    # 4. Извлекаем текст
    print("4. Извлеченный текст (первые 800 символов):")
    print("-" * 50)
    text = client.extract_text_from_blocks(blocks)
    print(text[:800])
    print("-" * 50)
    
    # 5. Проверяем картинки
    print("\n5. Картинки:")
    images = client.extract_images(blocks)
    print(f"   Найдено: {len(images)}")
    for img in images[:3]:
        print(f"   - {img[:60]}...")
    
    print("\n=== Тест пройден успешно! ===")
    print("Агент может читать контент из Notion.")

if __name__ == "__main__":
    test_full_pipeline()
