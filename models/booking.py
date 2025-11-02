"""
Модель бронирования для системы бронирования в ресторане.
Связывает пользователей (User) и столики (Table).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from pg_driver import PostgreSQLDriver


class BookingModel:
    """
    Модель бронирования для системы бронирования в ресторане.
    
    Поля таблицы:
    - id: INTEGER PRIMARY KEY (автоматически)
    - user_id: INTEGER NOT NULL - внешний ключ на таблицу users (ID пользователя)
    - table_id: INTEGER NOT NULL - внешний ключ на таблицу tables (ID стола)
    - booking_date: DATE NOT NULL - дата бронирования
    - booking_time: TIME NOT NULL - время бронирования
    - status: TEXT DEFAULT 'pending' - статус бронирования (reserved, cancelled, pending)
    - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - дата создания записи
    - updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - дата обновления записи
    """
    
    def __init__(self, db: Optional[PostgreSQLDriver] = None):
        """
        Инициализация модели бронирования.
        
        Args:
            db: Экземпляр PostgreSQLDriver. Если None, создается новый.
        """
        self.db = db or PostgreSQLDriver()
        self.table_name = "bookings"
        
        # Определение колонок таблицы
        # Примечание: В PostgreSQL внешние ключи добавляются отдельно после создания таблицы
        self.columns = """
            user_id INTEGER NOT NULL,
            table_id INTEGER NOT NULL,
            booking_date DATE NOT NULL,
            booking_time TIME NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('reserved', 'cancelled', 'pending')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
    
    def create_table(self) -> bool:
        """
        Создает таблицу bookings в базе данных.
        
        Returns:
            True если таблица создана успешно, False в противном случае.
        """
        result = self.db.create_table(
            table_name=self.table_name,
            columns=self.columns,
            if_not_exists=True,
            auto_id=True
        )
        
        # Добавляем внешние ключи после создания таблицы
        if result:
            try:
                # Добавляем внешний ключ на users
                self.db.execute_raw(
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
                
                # Добавляем внешний ключ на tables
                self.db.execute_raw(
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
                
                return True
            except Exception as e:
                print(f"Предупреждение: не удалось добавить внешние ключи: {e}")
                return result
        
        return result
    
    def create_booking(
        self,
        user_id: int,
        table_id: int,
        booking_date: date,
        booking_time: time,
        status: str = "pending"
    ) -> Optional[int]:
        """
        Создает новое бронирование.
        
        Args:
            user_id: ID пользователя (должен существовать в таблице users)
            table_id: ID стола (должен существовать в таблице tables)
            booking_date: Дата бронирования
            booking_time: Время бронирования
            status: Статус бронирования (reserved, cancelled, pending)
            
        Returns:
            ID созданного бронирования или None в случае ошибки.
        """
        valid_statuses = ['reserved', 'cancelled', 'pending']
        if status not in valid_statuses:
            print(f"Ошибка: статус должен быть одним из: {valid_statuses}")
            return None
        
        # Проверяем, что дата не в прошлом
        if isinstance(booking_date, str):
            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        
        today = date.today()
        if booking_date < today:
            print("Ошибка: нельзя забронировать стол на прошедшую дату")
            return None
        
        data = {
            "user_id": user_id,
            "table_id": table_id,
            "booking_date": booking_date,
            "booking_time": booking_time,
            "status": status,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        try:
            booking_id = self.db.insert(table_name=self.table_name, data=data)
            
            # При создании бронирования статус стола не меняется
            # Статус стола (available/unavailable) управляется отдельно
            
            return booking_id
        except Exception as e:
            print(f"Ошибка при создании бронирования: {e}")
            return None
    
    def get_booking_by_id(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает бронирование по ID.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            Словарь с данными бронирования или None.
        """
        return self.db.select_one(
            table_name=self.table_name,
            where={"id": booking_id}
        )
    
    def get_bookings_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получает все бронирования пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список бронирований пользователя.
        """
        return self.db.select(
            table_name=self.table_name,
            where={"user_id": user_id},
            order_by="booking_date DESC, booking_time DESC"
        )
    
    def get_bookings_by_table(self, table_id: int) -> List[Dict[str, Any]]:
        """
        Получает все бронирования для стола.
        
        Args:
            table_id: ID стола
            
        Returns:
            Список бронирований стола.
        """
        return self.db.select(
            table_name=self.table_name,
            where={"table_id": table_id},
            order_by="booking_date DESC, booking_time DESC"
        )
    
    def get_all_bookings(
        self,
        status: Optional[str] = None,
        booking_date: Optional[date] = None,
        limit: Optional[int] = None,
        order_by: str = "booking_date DESC, booking_time DESC"
    ) -> List[Dict[str, Any]]:
        """
        Получает список всех бронирований с опциональными фильтрами.
        
        Args:
            status: Фильтр по статусу (reserved, cancelled, pending)
            booking_date: Фильтр по дате бронирования
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки
            
        Returns:
            Список бронирований.
        """
        where = {}
        
        if status:
            where["status"] = status
        
        if booking_date:
            where["booking_date"] = booking_date
        
        if where:
            return self.db.select(
                table_name=self.table_name,
                where=where,
                order_by=order_by,
                limit=limit
            )
        else:
            return self.db.select(
                table_name=self.table_name,
                order_by=order_by,
                limit=limit
            )
    
    def get_upcoming_bookings(
        self,
        user_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает предстоящие бронирования (на сегодня и в будущем).
        
        Args:
            user_id: Если указан, фильтрует по пользователю
            limit: Максимальное количество записей
            
        Returns:
            Список предстоящих бронирований.
        """
        today = date.today()
        
        # Используем raw SQL для фильтрации по дате
        query = """
            SELECT * FROM bookings 
            WHERE booking_date >= %s 
            AND status IN ('reserved', 'pending')
        """
        
        params = [today]
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        query += " ORDER BY booking_date ASC, booking_time ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return list(self.db.execute_raw(query, params=tuple(params)))
    
    def check_table_availability(
        self,
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
        # Сначала проверяем статус стола
        from models.table import TableModel
        table_model = TableModel(self.db)
        table = table_model.get_table_by_id(table_id)
        
        if not table:
            return False
        
        # Если стол имеет статус unavailable, он недоступен для бронирования
        if table.get('status') == 'unavailable':
            return False
        
        # Проверяем существующие бронирования на эту дату (только активные)
        query = """
            SELECT * FROM bookings 
            WHERE table_id = %s 
            AND booking_date = %s 
            AND status IN ('reserved', 'pending')
        """
        
        bookings = list(self.db.execute_raw(
            query,
            params=(table_id, booking_date)
        ))
        
        # Если есть активные бронирования на это время, стол недоступен
        for booking in bookings:
            booking_time_obj = booking.get("booking_time")
            if isinstance(booking_time_obj, str):
                booking_time_obj = datetime.strptime(booking_time_obj, "%H:%M:%S").time()
            
            # Считаем, что стол занят, если время совпадает или разница менее часа
            time_diff = abs(
                (datetime.combine(date.today(), booking_time) - 
                 datetime.combine(date.today(), booking_time_obj)).total_seconds()
            )
            
            if time_diff < 3600:  # 1 час
                return False
        
        return True
    
    def update_booking(
        self,
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
        data = {
            "updated_at": datetime.now()
        }
        
        if user_id is not None:
            data["user_id"] = user_id
        if table_id is not None:
            data["table_id"] = table_id
        if booking_date is not None:
            if isinstance(booking_date, str):
                booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
            if booking_date < date.today():
                print("Ошибка: нельзя изменить дату на прошедшую")
                return False
            data["booking_date"] = booking_date
        if booking_time is not None:
            data["booking_time"] = booking_time
        if status is not None:
            valid_statuses = ['reserved', 'cancelled', 'pending']
            if status not in valid_statuses:
                print(f"Ошибка: статус должен быть одним из: {valid_statuses}")
                return False
            data["status"] = status
            
            # При обновлении бронирования статус стола не меняется
            # Статус стола (available/unavailable) управляется отдельно
        
        if not data or len(data) == 1:  # Только updated_at
            return False
        
        try:
            updated = self.db.update(
                table_name=self.table_name,
                data=data,
                where={"id": booking_id}
            )
            return updated > 0
        except Exception as e:
            print(f"Ошибка при обновлении бронирования: {e}")
            return False
    
    def delete_booking(self, booking_id: int) -> bool:
        """
        Удаляет бронирование из базы данных.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            True если удаление успешно, False в противном случае.
        """
        # Получаем данные бронирования перед удалением
        booking = self.get_booking_by_id(booking_id)
        
        try:
            deleted = self.db.delete(
                table_name=self.table_name,
                where={"id": booking_id}
            )
            
            # При удалении бронирования статус стола не меняется
            # Статус стола (available/unavailable) управляется отдельно
            
            return deleted > 0
        except Exception as e:
            print(f"Ошибка при удалении бронирования: {e}")
            return False
    
    def count_bookings(
        self,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        table_id: Optional[int] = None
    ) -> int:
        """
        Подсчитывает количество бронирований.
        
        Args:
            status: Фильтр по статусу
            user_id: Фильтр по пользователю
            table_id: Фильтр по столу
            
        Returns:
            Количество бронирований.
        """
        where = {}
        
        if status:
            where["status"] = status
        if user_id:
            where["user_id"] = user_id
        if table_id:
            where["table_id"] = table_id
        
        if where:
            return self.db.count(table_name=self.table_name, where=where)
        else:
            return self.db.count(table_name=self.table_name)
    
    def set_status(self, booking_id: int, status: str) -> bool:
        """
        Устанавливает статус бронирования.
        
        Args:
            booking_id: ID бронирования
            status: Новый статус (reserved, cancelled, pending)
            
        Returns:
            True если статус успешно изменен, False в противном случае.
        """
        return self.update_booking(booking_id, status=status)

