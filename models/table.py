"""
Модель стола для системы бронирования в ресторане.
Предоставляет интерфейс для работы с таблицей tables.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pg_driver import PostgreSQLDriver


class TableModel:
    """
    Модель стола для системы бронирования в ресторане.
    
    Поля таблицы:
    - id: INTEGER PRIMARY KEY (автоматически)
    - table_number: INTEGER UNIQUE NOT NULL - номер столика
    - seats: INTEGER NOT NULL - количество мест
    - status: TEXT DEFAULT 'available' - статус столика (available, unavailable)
    """
    
    def __init__(self, db: Optional[PostgreSQLDriver] = None):
        """
        Инициализация модели стола.
        
        Args:
            db: Экземпляр PostgreSQLDriver. Если None, создается новый.
        """
        self.db = db or PostgreSQLDriver()
        self.table_name = "tables"
        
        # Определение колонок таблицы
        self.columns = """
            table_number INTEGER UNIQUE NOT NULL,
            seats INTEGER NOT NULL CHECK (seats > 0),
            status TEXT DEFAULT 'available' CHECK (status IN ('available', 'unavailable'))
        """
    
    def create_table(self) -> bool:
        """
        Создает таблицу tables в базе данных.
        
        Returns:
            True если таблица создана успешно, False в противном случае.
        """
        return self.db.create_table(
            table_name=self.table_name,
            columns=self.columns,
            if_not_exists=True,
            auto_id=True
        )
    
    def create_table_item(
        self,
        table_number: int,
        seats: int,
        status: str = "available"
    ) -> Optional[int]:
        """
        Создает новый стол в базе данных.
        
        Args:
            table_number: Номер столика (должен быть уникальным)
            seats: Количество мест (должно быть больше 0)
            status: Статус столика (available, unavailable)
            
        Returns:
            ID созданного стола или None в случае ошибки.
        """
        if seats <= 0:
            print("Ошибка: количество мест должно быть больше 0")
            return None
        
        valid_statuses = ['available', 'unavailable']
        if status not in valid_statuses:
            print(f"Ошибка: статус должен быть одним из: {valid_statuses}")
            return None
        
        data = {
            "table_number": table_number,
            "seats": seats,
            "status": status
        }
        
        try:
            return self.db.insert(table_name=self.table_name, data=data)
        except Exception as e:
            print(f"Ошибка при создании стола: {e}")
            return None
    
    def get_table_by_id(self, table_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает стол по ID.
        
        Args:
            table_id: ID стола
            
        Returns:
            Словарь с данными стола или None.
        """
        return self.db.select_one(
            table_name=self.table_name,
            where={"id": table_id}
        )
    
    def get_table_by_number(self, table_number: int) -> Optional[Dict[str, Any]]:
        """
        Получает стол по номеру.
        
        Args:
            table_number: Номер столика
            
        Returns:
            Словарь с данными стола или None.
        """
        return self.db.select_one(
            table_name=self.table_name,
            where={"table_number": table_number}
        )
    
    def get_all_tables(
        self,
        status: Optional[str] = None,
        min_seats: Optional[int] = None,
        max_seats: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: str = "table_number ASC"
    ) -> List[Dict[str, Any]]:
        """
        Получает список всех столов с опциональными фильтрами.
        
        Args:
            status: Фильтр по статусу (available, unavailable)
            min_seats: Минимальное количество мест
            max_seats: Максимальное количество мест
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки
            
        Returns:
            Список столов.
        """
        # Для более сложных фильтров используем raw SQL
        where = {}
        
        if status:
            where["status"] = status
        
        tables = self.db.select(
            table_name=self.table_name,
            where=where if where else None,
            order_by=order_by,
            limit=limit
        )
        
        # Фильтруем по количеству мест, если указано
        if min_seats is not None or max_seats is not None:
            filtered_tables = []
            for table in tables:
                seats = table.get("seats", 0)
                if min_seats is not None and seats < min_seats:
                    continue
                if max_seats is not None and seats > max_seats:
                    continue
                filtered_tables.append(table)
            return filtered_tables
        
        return tables
    
    def get_available_tables(
        self,
        min_seats: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает список доступных столов.
        
        Args:
            min_seats: Минимальное количество мест
            limit: Максимальное количество записей
            
        Returns:
            Список доступных столов.
        """
        return self.get_all_tables(
            status="available",
            min_seats=min_seats,
            limit=limit,
            order_by="table_number ASC"
        )
    
    def update_table(
        self,
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
        data = {}
        
        if table_number is not None:
            data["table_number"] = table_number
        if seats is not None:
            if seats <= 0:
                print("Ошибка: количество мест должно быть больше 0")
                return False
            data["seats"] = seats
        if status is not None:
            valid_statuses = ['available', 'unavailable']
            if status not in valid_statuses:
                print(f"Ошибка: статус должен быть одним из: {valid_statuses}")
                return False
            data["status"] = status
        
        if not data:
            return False
        
        try:
            updated = self.db.update(
                table_name=self.table_name,
                data=data,
                where={"id": table_id}
            )
            return updated > 0
        except Exception as e:
            print(f"Ошибка при обновлении стола: {e}")
            return False
    
    def delete_table(self, table_id: int) -> bool:
        """
        Удаляет стол из базы данных.
        
        Args:
            table_id: ID стола
            
        Returns:
            True если удаление успешно, False в противном случае.
        """
        try:
            deleted = self.db.delete(
                table_name=self.table_name,
                where={"id": table_id}
            )
            return deleted > 0
        except Exception as e:
            print(f"Ошибка при удалении стола: {e}")
            return False
    
    def count_tables(
        self,
        status: Optional[str] = None
    ) -> int:
        """
        Подсчитывает количество столов.
        
        Args:
            status: Фильтр по статусу
            
        Returns:
            Количество столов.
        """
        where = {}
        
        if status:
            where["status"] = status
        
        if where:
            return self.db.count(table_name=self.table_name, where=where)
        else:
            return self.db.count(table_name=self.table_name)
    
    def table_exists(self, table_number: int) -> bool:
        """
        Проверяет, существует ли стол с данным номером.
        
        Args:
            table_number: Номер столика для проверки
            
        Returns:
            True если стол существует, False в противном случае.
        """
        table = self.get_table_by_number(table_number)
        return table is not None
    
    def set_status(self, table_id: int, status: str) -> bool:
        """
        Устанавливает статус стола.
        
        Args:
            table_id: ID стола
            status: Новый статус (available, unavailable)
            
        Returns:
            True если статус успешно изменен, False в противном случае.
        """
        return self.update_table(table_id, status=status)

