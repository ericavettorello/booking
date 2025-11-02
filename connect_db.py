"""
Скрипт для подключения и работы с базой данных booking.
Можно использовать для проверки подключения и просмотра данных.
"""
from pg_driver import PostgreSQLDriver
from models.user import UserModel
from models.table import TableModel
from models.booking import BookingModel

def show_database_info():
    """Показывает информацию о базе данных и таблицах."""
    try:
        with PostgreSQLDriver() as db:
            print("=" * 60)
            print("Информация о базе данных")
            print("=" * 60)
            
            # Параметры подключения
            print(f"\nПараметры подключения:")
            print(f"  Host: {db._connection_params['host']}")
            print(f"  Port: {db._connection_params['port']}")
            print(f"  Database: {db._connection_params['database']}")
            print(f"  User: {db._connection_params['user']}")
            
            # Список таблиц
            tables = db.execute_raw(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name",
                params=None
            )
            
            print(f"\nТаблицы в базе данных ({len(tables)}):")
            for table in tables:
                table_name = table.get('table_name', '')
                count = db.count(table_name=table_name)
                print(f"  • {table_name} - записей: {count}")
            
            print("\n" + "=" * 60)
            print("Подключение успешно!")
            print("=" * 60)
            
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        print("\nПроверьте:")
        print("  1. Существует ли файл .env с правильными настройками")
        print("  2. Запущен ли сервер PostgreSQL")
        print("  3. Правильность пароля в .env")

if __name__ == "__main__":
    show_database_info()

