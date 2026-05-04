"""Тестовый скрипт для проверки чтения из Notion."""

import sys
sys.path.insert(0, '/tmp/publisher-agent')

from src.notion_client import NotionClient

def test_notion_reading():
    print("=== Тестирование чтения из Notion ===\n")
    
    client = NotionClient()
    
    # 1. Получаем все страницы из базы
    print("1. Получаем список страниц из базы...")
    try:
        response = client.client.databases.query(
            database_id=client.database_id
        )
        pages = response["results"]
        print(f"   ✅ Найдено страниц: {len(pages)}\n")
        
        if not pages:
            print("   ⚠️ База пуста!")
            return
        
        # Показываем первые 3 страницы
        print("   Первые страницы:")
        for i, page in enumerate(pages[:3], 1):
            props = client.get_page_properties(page)
            print(f"   {i}. {props.get('title', 'Без названия')} (ID: {props['id'][:8]}...)")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return
    
    # 2. Ищем страницы со статусом "Готово"
    print("\n2. Ищем страницы со статусом 'Готово'...")
    try:
        ready_pages = client.get_ready_posts()
        print(f"   ✅ Найдено страниц со статусом 'Готово': {len(ready_pages)}\n")
        
        if not ready_pages:
            print("   ⚠️ Нет страниц со статусом 'Готово к публикации'")
            print("   Статусы в базе:")
            # Показываем какие статусы есть
            statuses = set()
            for page in pages[:10]:
                if "Статус" in page["properties"]:
                    status = page["properties"]["Статус"]
                    if "select" in status and status["select"]:
                        statuses.add(status["select"]["name"])
            for status in statuses:
                print(f"   - {status}")
            return
        
        # Берем первую страницу для теста
        test_page = ready_pages[0]
        props = client.get_page_properties(test_page)
        
        print(f"   Тестируем страницу: {props.get('title', 'Без названия')}")
        print(f"   Каналы: {', '.join(props.get('channels', []))}")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return
    
    # 3. Читаем контент страницы
    print("\n3. Читаем контент страницы...")
    try:
        blocks = client.get_page_content(test_page["id"])
        print(f"   ✅ Найдено блоков: {len(blocks)}")
        
        if blocks:
            print("\n   Типы блоков:")
            for i, block in enumerate(blocks[:5], 1):
                print(f"   {i}. {block['type']}")
            
            # Извлекаем текст
            print("\n   Извлеченный текст (первые 500 символов):")
            text = client.extract_text_from_blocks(blocks)
            print(f"   {text[:500]}...")
            
            # Извлекаем картинки
            images = client.extract_images(blocks)
            print(f"\n   Найдено картинок: {len(images)}")
            for img in images[:3]:
                print(f"   - {img[:60]}...")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return
    
    print("\n=== Тест завершен успешно! ===")

if __name__ == "__main__":
    test_notion_reading()
