"""
Пример использования PostgreSQLDriver во внешних проектах.
"""

from pg_driver import PostgreSQLDriver

# Инициализация драйвера
# Автоматически использует .env из директории модуля
db = PostgreSQLDriver()

# Или можно указать свой путь к .env
# db = PostgreSQLDriver(env_path=Path("/path/to/your/.env"))


def example_create():
    """Пример создания таблицы"""
    print("=== CREATE TABLE ===")
    db.create_table(
        table_name="users",
        columns="name TEXT NOT NULL, email TEXT UNIQUE, age INTEGER",
        # id добавится автоматически
    )
    print("Таблица users создана (с автоматическим id)")


def example_insert():
    """Пример вставки данных"""
    print("\n=== INSERT ===")
    user_id = db.insert(
        table_name="users",
        data={
            "name": "Иван Иванов",
            "email": "ivan@example.com",
            "age": 30
        }
    )
    print(f"Пользователь добавлен с id: {user_id}")
    
    # Массовая вставка
    users_data = [
        {"name": "Петр Петров", "email": "petr@example.com", "age": 25},
        {"name": "Мария Сидорова", "email": "maria@example.com", "age": 28},
    ]
    count = db.insert_many("users", users_data)
    print(f"Добавлено пользователей: {count}")


def example_select():
    """Пример выборки данных"""
    print("\n=== SELECT ===")
    
    # Выбрать всех
    all_users = db.select("users")
    print(f"Всего пользователей: {len(all_users)}")
    for user in all_users:
        print(f"  {user}")
    
    # Выбрать с условием
    ivan = db.select_one("users", where={"name": "Иван Иванов"})
    print(f"\nНайден: {ivan}")
    
    # Выбрать с несколькими условиями
    young_users = db.select(
        "users",
        where={"age": 25},  # Можно использовать операторы в будущем
        order_by="name ASC",
        limit=10
    )
    print(f"\nМолодые пользователи: {young_users}")
    
    # Подсчет
    total = db.count("users")
    print(f"\nВсего записей в таблице: {total}")


def example_update():
    """Пример обновления данных"""
    print("\n=== UPDATE ===")
    
    updated = db.update(
        table_name="users",
        data={"age": 31},
        where={"name": "Иван Иванов"}
    )
    print(f"Обновлено записей: {updated}")
    
    # Проверяем
    ivan = db.select_one("users", where={"name": "Иван Иванов"})
    print(f"Обновленный пользователь: {ivan}")


def example_delete():
    """Пример удаления данных"""
    print("\n=== DELETE ===")
    
    deleted = db.delete(
        table_name="users",
        where={"email": "petr@example.com"}
    )
    print(f"Удалено записей: {deleted}")
    
    # Проверяем
    remaining = db.count("users")
    print(f"Осталось пользователей: {remaining}")


def example_raw_sql():
    """Пример выполнения произвольного SQL"""
    print("\n=== RAW SQL ===")
    
    results = db.execute_raw(
        "SELECT name, email FROM users WHERE age > %s ORDER BY name",
        params=(25,)
    )
    print("Результаты произвольного запроса:")
    for row in results:
        print(f"  {row}")


def example_transaction():
    """Пример работы с транзакциями"""
    print("\n=== TRANSACTION ===")
    
    conn = db.begin_transaction()
    try:
        # Выполняем несколько операций в одной транзакции
        db.insert("users", {"name": "Тест", "email": "test@test.com", "age": 20}, 
                  commit=False)
        # Можно использовать execute_raw с существующим соединением
        # ...
        db.commit(conn)
        print("Транзакция успешно завершена")
    except Exception as e:
        db.rollback(conn)
        print(f"Транзакция откачена: {e}")


if __name__ == "__main__":
    # Раскомментируйте нужные примеры
    # example_create()
    # example_insert()
    # example_select()
    # example_update()
    # example_delete()
    # example_raw_sql()
    # example_transaction()
    
    print("Примеры готовы к использованию!")
    print("Раскомментируйте нужные функции в __main__ для запуска.")

