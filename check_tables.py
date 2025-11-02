"""
Скрипт для проверки таблиц в базе данных.
"""
from pg_driver import PostgreSQLDriver

def check_tables():
    """Проверяет наличие таблиц в базе данных."""
    try:
        with PostgreSQLDriver() as db:
            # Получаем список всех таблиц в схеме public
            tables = db.execute_raw(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name",
                params=None
            )
            
            print("=" * 50)
            print("Проверка таблиц в базе данных:")
            print("=" * 50)
            
            if tables:
                print(f"\nНайдено таблиц: {len(tables)}\n")
                for table in tables:
                    table_name = table.get('table_name', '')
                    print(f"  ✓ {table_name}")
                    
                    # Получаем количество строк в таблице
                    count = db.count(table_name=table_name)
                    print(f"    Количество записей: {count}")
            else:
                print("\n✗ Таблицы не найдены в базе данных!")
                
            print("\n" + "=" * 50)
            
    except Exception as e:
        print(f"Ошибка при проверке: {e}")

if __name__ == "__main__":
    check_tables()

