"""
Backend модуль для системы бронирования.
Содержит логику инициализации и управления базой данных.
"""

from typing import Optional, List, Dict, Any
from datetime import date, time

from pg_driver import PostgreSQLDriver
from models.user import UserModel
from models.table import TableModel
from models.booking import BookingModel


def create_tables():
    """
    Создает все таблицы в базе данных на основе моделей.
    Вызывает create_table_from_model для каждой модели (User, Table, Booking).
    """
    with PostgreSQLDriver() as db:
        # Создаем модель пользователя
        user_model = UserModel(db)
        print("Создание таблицы users...")
        if db.create_table_from_model(user_model):
            print("✓ Таблица users создана успешно")
        else:
            print("✗ Ошибка при создании таблицы users")
        
        # Создаем модель столов
        table_model = TableModel(db)
        print("Создание таблицы tables...")
        if db.create_table_from_model(table_model):
            # Обновляем CHECK ограничение для статуса
            try:
                db.execute_raw(
                    """
                    DO $$ 
                    BEGIN
                        -- Удаляем старое ограничение, если оно существует
                        IF EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'tables_status_check'
                        ) THEN
                            ALTER TABLE tables DROP CONSTRAINT tables_status_check;
                        END IF;
                        
                        -- Добавляем новое ограничение
                        ALTER TABLE tables 
                        ADD CONSTRAINT tables_status_check 
                        CHECK (status IN ('available', 'unavailable'));
                    END $$;
                    """
                )
                print("✓ Таблица tables создана успешно (с обновленным CHECK)")
            except Exception as e:
                print(f"⚠ Таблица tables создана, но возникла ошибка при обновлении CHECK ограничения: {e}")
        else:
            print("✗ Ошибка при создании таблицы tables")
        
        # Создаем модель бронирований
        booking_model = BookingModel(db)
        print("Создание таблицы bookings...")
        if db.create_table_from_model(booking_model):
            # Добавляем внешние ключи для bookings
            try:
                db.execute_raw(
                    """
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'fk_bookings_user_id'
                        ) THEN
                            ALTER TABLE bookings 
                            ADD CONSTRAINT fk_bookings_user_id 
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                        END IF;
                    END $$;
                    """
                )
                db.execute_raw(
                    """
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'fk_bookings_table_id'
                        ) THEN
                            ALTER TABLE bookings 
                            ADD CONSTRAINT fk_bookings_table_id 
                            FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE;
                        END IF;
                    END $$;
                    """
                )
                # Обновляем CHECK ограничение для статуса
                try:
                    db.execute_raw(
                        """
                        DO $$ 
                        BEGIN
                            -- Удаляем старое ограничение, если оно существует
                            IF EXISTS (
                                SELECT 1 FROM pg_constraint 
                                WHERE conname = 'bookings_status_check'
                            ) THEN
                                ALTER TABLE bookings DROP CONSTRAINT bookings_status_check;
                            END IF;
                            
                            -- Добавляем новое ограничение
                            ALTER TABLE bookings 
                            ADD CONSTRAINT bookings_status_check 
                            CHECK (status IN ('reserved', 'cancelled', 'pending'));
                        END $$;
                        """
                    )
                    print("✓ Таблица bookings создана успешно (с внешними ключами и обновленным CHECK)")
                except Exception as e:
                    print(f"⚠ Таблица bookings создана, но возникла ошибка при обновлении CHECK ограничения: {e}")
            except Exception as e:
                print(f"⚠ Таблица bookings создана, но возникла ошибка при добавлении внешних ключей: {e}")
        else:
            print("✗ Ошибка при создании таблицы bookings")
        
        print("\nВсе таблицы созданы!")


# ==================== CRUD OPERATIONS FOR USERS ====================

def create_user(
    name: str,
    email: str,
    password: str,
    phone: Optional[str] = None,
    role: str = "client",
    is_active: bool = True
) -> Optional[int]:
    """
    Создает нового пользователя.
    
    Args:
        name: Имя пользователя
        email: Email адрес (должен быть уникальным)
        password: Пароль в открытом виде (будет автоматически хэширован)
        phone: Номер телефона (опционально)
        role: Роль пользователя
        is_active: Активен ли пользователь
        
    Returns:
        ID созданного пользователя или None в случае ошибки.
    """
    with PostgreSQLDriver() as db:
        user_model = UserModel(db)
        return user_model.create_user(name, email, password, phone, role, is_active)


def get_user(user_id: Optional[int] = None, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Получает пользователя по ID или email.
    
    Args:
        user_id: ID пользователя
        email: Email адрес
        
    Returns:
        Словарь с данными пользователя или None.
    """
    with PostgreSQLDriver() as db:
        user_model = UserModel(db)
        if user_id:
            return user_model.get_user_by_id(user_id)
        elif email:
            return user_model.get_user_by_email(email)
        return None


def get_all_users(
    active_only: bool = False,
    role: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Получает список всех пользователей.
    
    Args:
        active_only: Если True, возвращает только активных пользователей
        role: Фильтр по роли
        limit: Максимальное количество записей
        
    Returns:
        Список пользователей.
    """
    with PostgreSQLDriver() as db:
        user_model = UserModel(db)
        return user_model.get_all_users(active_only=active_only, role=role, limit=limit)


def update_user(
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None
) -> bool:
    """
    Обновляет данные пользователя.
    
    Args:
        user_id: ID пользователя
        name: Новое имя (опционально)
        email: Новый email (опционально)
        phone: Новый телефон (опционально)
        password: Новый пароль (опционально)
        role: Новая роль (опционально)
        is_active: Новый статус активности (опционально)
        
    Returns:
        True если обновление успешно, False в противном случае.
    """
    with PostgreSQLDriver() as db:
        user_model = UserModel(db)
        return user_model.update_user(user_id, name, email, phone, password, role, is_active)


def delete_user(user_id: int, hard_delete: bool = False) -> bool:
    """
    Удаляет пользователя.
    
    Args:
        user_id: ID пользователя
        hard_delete: Если True, физически удаляет запись.
                    Если False, деактивирует пользователя.
        
    Returns:
        True если удаление успешно, False в противном случае.
    """
    with PostgreSQLDriver() as db:
        user_model = UserModel(db)
        return user_model.delete_user(user_id, hard_delete)


# ==================== CRUD OPERATIONS FOR TABLES ====================

def create_table(
    table_number: int,
    seats: int,
    status: str = "available"
) -> Optional[int]:
    """
    Создает новый стол.
    
    Args:
        table_number: Номер столика (должен быть уникальным)
        seats: Количество мест (должно быть больше 0)
        status: Статус столика (available, unavailable)
        
    Returns:
        ID созданного стола или None в случае ошибки.
    """
    with PostgreSQLDriver() as db:
        table_model = TableModel(db)
        return table_model.create_table_item(table_number, seats, status)


def get_table(table_id: Optional[int] = None, table_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Получает стол по ID или номеру.
    
    Args:
        table_id: ID стола
        table_number: Номер столика
        
    Returns:
        Словарь с данными стола или None.
    """
    with PostgreSQLDriver() as db:
        table_model = TableModel(db)
        if table_id:
            return table_model.get_table_by_id(table_id)
        elif table_number is not None:
            return table_model.get_table_by_number(table_number)
        return None


def get_all_tables(
    status: Optional[str] = None,
    min_seats: Optional[int] = None,
    max_seats: Optional[int] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Получает список всех столов.
    
    Args:
        status: Фильтр по статусу
        min_seats: Минимальное количество мест
        max_seats: Максимальное количество мест
        limit: Максимальное количество записей
        
    Returns:
        Список столов.
    """
    with PostgreSQLDriver() as db:
        table_model = TableModel(db)
        return table_model.get_all_tables(status=status, min_seats=min_seats, 
                                         max_seats=max_seats, limit=limit)


def get_available_tables(min_seats: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Получает список доступных столов.
    
    Args:
        min_seats: Минимальное количество мест
        limit: Максимальное количество записей
        
    Returns:
        Список доступных столов.
    """
    with PostgreSQLDriver() as db:
        table_model = TableModel(db)
        return table_model.get_available_tables(min_seats=min_seats, limit=limit)


def update_table(
    table_id: int,
    table_number: Optional[int] = None,
    seats: Optional[int] = None,
    status: Optional[str] = None
) -> bool:
    """
    Обновляет данные стола.
    
    Args:
        table_id: ID стола
        table_number: Новый номер столика (опционально)
        seats: Новое количество мест (опционально)
        status: Новый статус (опционально)
        
    Returns:
        True если обновление успешно, False в противном случае.
    """
    with PostgreSQLDriver() as db:
        table_model = TableModel(db)
        return table_model.update_table(table_id, table_number, seats, status)


def delete_table(table_id: int) -> bool:
    """
    Удаляет стол из базы данных.
    
    Args:
        table_id: ID стола
        
    Returns:
        True если удаление успешно, False в противном случае.
    """
    with PostgreSQLDriver() as db:
        table_model = TableModel(db)
        return table_model.delete_table(table_id)


# ==================== CRUD OPERATIONS FOR BOOKINGS ====================

def create_booking(
    user_id: int,
    table_id: int,
    booking_date: date,
    booking_time: time,
    status: str = "pending"
) -> Optional[int]:
    """
    Создает новое бронирование.
    
    Args:
        user_id: ID пользователя
        table_id: ID стола
        booking_date: Дата бронирования
        booking_time: Время бронирования
        status: Статус бронирования (reserved, cancelled, pending)
        
    Returns:
        ID созданного бронирования или None в случае ошибки.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.create_booking(user_id, table_id, booking_date, booking_time, status)


def get_booking(booking_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает бронирование по ID.
    
    Args:
        booking_id: ID бронирования
        
    Returns:
        Словарь с данными бронирования или None.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.get_booking_by_id(booking_id)


def get_bookings_by_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Получает все бронирования пользователя.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Список бронирований пользователя.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.get_bookings_by_user(user_id)


def get_bookings_by_table(table_id: int) -> List[Dict[str, Any]]:
    """
    Получает все бронирования для стола.
    
    Args:
        table_id: ID стола
        
    Returns:
        Список бронирований стола.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.get_bookings_by_table(table_id)


def get_all_bookings(
    status: Optional[str] = None,
    booking_date: Optional[date] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Получает список всех бронирований.
    
    Args:
        status: Фильтр по статусу
        booking_date: Фильтр по дате бронирования
        limit: Максимальное количество записей
        
    Returns:
        Список бронирований.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.get_all_bookings(status=status, booking_date=booking_date, limit=limit)


def update_booking(
    booking_id: int,
    user_id: Optional[int] = None,
    table_id: Optional[int] = None,
    booking_date: Optional[date] = None,
    booking_time: Optional[time] = None,
    status: Optional[str] = None
) -> bool:
    """
    Обновляет данные бронирования.
    
    Args:
        booking_id: ID бронирования
        user_id: Новый ID пользователя (опционально)
        table_id: Новый ID стола (опционально)
        booking_date: Новая дата бронирования (опционально)
        booking_time: Новое время бронирования (опционально)
        status: Новый статус (опционально)
        
    Returns:
        True если обновление успешно, False в противном случае.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.update_booking(booking_id, user_id, table_id, booking_date, booking_time, status)


def delete_booking(booking_id: int) -> bool:
    """
    Удаляет бронирование из базы данных.
    
    Args:
        booking_id: ID бронирования
        
    Returns:
        True если удаление успешно, False в противном случае.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.delete_booking(booking_id)


def check_table_availability(
    table_id: int,
    booking_date: date,
    booking_time: time
) -> bool:
    """
    Проверяет, доступен ли стол для бронирования на указанные дату и время.
    
    Args:
        table_id: ID стола
        booking_date: Дата бронирования
        booking_time: Время бронирования
        
    Returns:
        True если стол доступен, False в противном случае.
    """
    with PostgreSQLDriver() as db:
        booking_model = BookingModel(db)
        return booking_model.check_table_availability(table_id, booking_date, booking_time)


if __name__ == "__main__":
    print("Инициализация базы данных...")
    print("=" * 50)
    create_tables()

