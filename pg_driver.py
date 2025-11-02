"""
PostgreSQL Driver Module
Модуль-драйвер для работы с PostgreSQL в внешних проектах.

Использование:
    from pg_driver import PostgreSQLDriver
    
    db = PostgreSQLDriver()
    
    # CREATE
    db.create_table('users', 'name TEXT NOT NULL, email TEXT UNIQUE')
    
    # INSERT
    db.insert('users', {'name': 'Иван', 'email': 'ivan@example.com'})
    
    # READ
    users = db.select('users', where={'name': 'Иван'})
    
    # UPDATE
    db.update('users', {'name': 'Петр'}, where={'id': 1})
    
    # DELETE
    db.delete('users', where={'id': 1})
"""

import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import psycopg2
from psycopg2.extensions import connection as PsycopgConnection
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


class PostgreSQLDriver:
    """
    Драйвер для работы с PostgreSQL.
    Использует переменные окружения из .env файла для подключения.
    """
    
    def __init__(self, env_path: Optional[Path] = None):
        """
        Инициализация драйвера.
        
        Args:
            env_path: Путь к .env файлу. Если None, используется .env в директории модуля.
        """
        if env_path is None:
            env_path = Path(__file__).parent / ".env"
        
        load_dotenv(dotenv_path=env_path)
        
        self._connection_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "postgres"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
        }
    
    def _get_connection(self) -> PsycopgConnection:
        """Создает и возвращает подключение к БД."""
        return psycopg2.connect(**self._connection_params)
    
    @contextmanager
    def _get_cursor(self, connection: Optional[PsycopgConnection] = None):
        """Контекстный менеджер для курсора."""
        own_connection = connection is None
        if own_connection:
            connection = self._get_connection()
        
        try:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor, connection
        finally:
            if own_connection:
                connection.close()
    
    # ==================== CREATE OPERATIONS ====================
    
    def create_table(
        self,
        table_name: str,
        columns: str,
        schema: str = "public",
        if_not_exists: bool = True,
        auto_id: bool = True
    ) -> bool:
        """
        Создает таблицу в базе данных.
        
        Args:
            table_name: Имя таблицы
            columns: Определение столбцов (например: 'name TEXT NOT NULL, email TEXT UNIQUE')
            schema: Схема БД (по умолчанию 'public')
            if_not_exists: Если True, добавляет IF NOT EXISTS
            auto_id: Если True, автоматически добавляет id, если его нет в columns
        
        Returns:
            True если успешно, False при ошибке
        """
        # Проверяем, есть ли уже id в columns
        import re
        has_id = re.search(r"\bid\b", columns, flags=re.IGNORECASE) is not None
        
        if auto_id and not has_id:
            columns = "id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, " + columns
        
        if_not_exists_clause = "IF NOT EXISTS" if if_not_exists else ""
        
        query = sql.SQL("CREATE TABLE {if_not_exists} {schema}.{table} ({columns})").format(
            if_not_exists=sql.SQL(if_not_exists_clause) if if_not_exists_clause else sql.SQL(""),
            schema=sql.Identifier(schema),
            table=sql.Identifier(table_name),
            columns=sql.SQL(columns)
        )
        
        try:
            with self._get_cursor() as (cursor, conn):
                cursor.execute(query)
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка создания таблицы: {e}")
            return False
    
    def create_table_from_model(
        self,
        model,
        schema: str = "public",
        if_not_exists: bool = True,
        auto_id: bool = True
    ) -> bool:
        """
        Создает таблицу на основе модели (объекта с атрибутами table_name и columns).
        
        Args:
            model: Объект модели (например, UserModel, TableModel, BookingModel),
                   который должен иметь атрибуты:
                   - table_name: str - имя таблицы
                   - columns: str - определение колонок SQL
            schema: Схема БД (по умолчанию 'public')
            if_not_exists: Если True, добавляет IF NOT EXISTS
            auto_id: Если True, автоматически добавляет id, если его нет в columns
        
        Returns:
            True если успешно, False при ошибке
            
        Example:
            from models.user import UserModel
            
            db = PostgreSQLDriver()
            user_model = UserModel(db)
            db.create_table_from_model(user_model)
        """
        # Проверяем наличие необходимых атрибутов
        if not hasattr(model, 'table_name'):
            print("Ошибка: модель должна иметь атрибут 'table_name'")
            return False
        
        if not hasattr(model, 'columns'):
            print("Ошибка: модель должна иметь атрибут 'columns'")
            return False
        
        table_name = model.table_name
        columns = model.columns
        
        # Используем существующий метод create_table
        return self.create_table(
            table_name=table_name,
            columns=columns,
            schema=schema,
            if_not_exists=if_not_exists,
            auto_id=auto_id
        )
    
    def insert(
        self,
        table_name: str,
        data: Dict[str, Any],
        schema: str = "public",
        commit: bool = True
    ) -> Optional[int]:
        """
        Вставляет строку в таблицу.
        
        Args:
            table_name: Имя таблицы
            data: Словарь с данными {column: value}
            schema: Схема БД (по умолчанию 'public')
            commit: Автоматически коммитить транзакцию
        
        Returns:
            ID вставленной строки (если есть) или None
        """
        if not data:
            return None
        
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        
        query = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({placeholders}) RETURNING id").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table_name),
            columns=sql.SQL(", ").join([sql.Identifier(col) for col in columns]),
            placeholders=sql.SQL(placeholders)
        )
        
        try:
            with self._get_cursor() as (cursor, conn):
                cursor.execute(query, values)
                if commit:
                    conn.commit()
                
                # Пытаемся получить id
                try:
                    result = cursor.fetchone()
                    return result["id"] if result and "id" in result else None
                except psycopg2.ProgrammingError:
                    # Если нет RETURNING или нет id
                    return None
        except Exception as e:
            print(f"Ошибка вставки: {e}")
            return None
    
    def insert_many(
        self,
        table_name: str,
        data_list: List[Dict[str, Any]],
        schema: str = "public",
        commit: bool = True
    ) -> int:
        """
        Вставляет несколько строк в таблицу.
        
        Args:
            table_name: Имя таблицы
            data_list: Список словарей с данными
            schema: Схема БД (по умолчанию 'public')
            commit: Автоматически коммитить транзакцию
        
        Returns:
            Количество вставленных строк
        """
        if not data_list:
            return 0
        
        # Берем столбцы из первого элемента
        columns = list(data_list[0].keys())
        
        query = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES %s").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table_name),
            columns=sql.SQL(", ").join([sql.Identifier(col) for col in columns])
        )
        
        # Подготавливаем данные для batch insert
        values_list = [[row.get(col) for col in columns] for row in data_list]
        
        try:
            with self._get_cursor() as (cursor, conn):
                from psycopg2.extras import execute_values
                execute_values(cursor, query, values_list)
                if commit:
                    conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Ошибка массовой вставки: {e}")
            return 0
    
    # ==================== READ OPERATIONS ====================
    
    def select(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        schema: str = "public"
    ) -> List[Dict[str, Any]]:
        """
        Выполняет SELECT запрос.
        
        Args:
            table_name: Имя таблицы
            columns: Список столбцов для выборки (None = все)
            where: Условия WHERE в виде словаря {column: value}
            order_by: ORDER BY выражение (например: 'id DESC')
            limit: LIMIT количество строк
            schema: Схема БД (по умолчанию 'public')
        
        Returns:
            Список словарей с результатами
        """
        # Формируем SELECT часть
        if columns:
            select_cols = sql.SQL(", ").join([sql.Identifier(col) for col in columns])
        else:
            select_cols = sql.SQL("*")
        
        query_parts = [sql.SQL("SELECT {columns} FROM {schema}.{table}").format(
            columns=select_cols,
            schema=sql.Identifier(schema),
            table=sql.Identifier(table_name)
        )]
        
        params = []
        
        # Добавляем WHERE
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(sql.SQL("{column} = %s").format(column=sql.Identifier(key)))
                params.append(value)
            query_parts.append(sql.SQL("WHERE {conditions}").format(
                conditions=sql.SQL(" AND ").join(conditions)
            ))
        
        # Добавляем ORDER BY
        if order_by:
            query_parts.append(sql.SQL("ORDER BY {order}").format(
                order=sql.SQL(order_by)
            ))
        
        # Добавляем LIMIT
        if limit:
            query_parts.append(sql.SQL("LIMIT {limit}").format(
                limit=sql.Literal(limit)
            ))
        
        query = sql.SQL(" ").join(query_parts)
        
        try:
            with self._get_cursor() as (cursor, conn):
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка выборки: {e}")
            return []
    
    def select_one(
        self,
        table_name: str,
        where: Dict[str, Any],
        columns: Optional[List[str]] = None,
        schema: str = "public"
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет SELECT запрос и возвращает одну строку.
        
        Args:
            table_name: Имя таблицы
            where: Условия WHERE в виде словаря {column: value}
            columns: Список столбцов для выборки (None = все)
            schema: Схема БД (по умолчанию 'public')
        
        Returns:
            Словарь с результатом или None
        """
        results = self.select(table_name, columns, where, limit=1, schema=schema)
        return results[0] if results else None
    
    def count(
        self,
        table_name: str,
        where: Optional[Dict[str, Any]] = None,
        schema: str = "public"
    ) -> int:
        """
        Подсчитывает количество строк в таблице.
        
        Args:
            table_name: Имя таблицы
            where: Условия WHERE в виде словаря {column: value}
            schema: Схема БД (по умолчанию 'public')
        
        Returns:
            Количество строк
        """
        query_parts = [sql.SQL("SELECT COUNT(*) as count FROM {schema}.{table}").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table_name)
        )]
        
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(sql.SQL("{column} = %s").format(column=sql.Identifier(key)))
                params.append(value)
            query_parts.append(sql.SQL("WHERE {conditions}").format(
                conditions=sql.SQL(" AND ").join(conditions)
            ))
        
        query = sql.SQL(" ").join(query_parts)
        
        try:
            with self._get_cursor() as (cursor, conn):
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result["count"] if result else 0
        except Exception as e:
            print(f"Ошибка подсчета: {e}")
            return 0
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update(
        self,
        table_name: str,
        data: Dict[str, Any],
        where: Dict[str, Any],
        schema: str = "public",
        commit: bool = True
    ) -> int:
        """
        Обновляет строки в таблице.
        
        Args:
            table_name: Имя таблицы
            data: Словарь с данными для обновления {column: value}
            where: Условия WHERE в виде словаря {column: value}
            schema: Схема БД (по умолчанию 'public')
            commit: Автоматически коммитить транзакцию
        
        Returns:
            Количество обновленных строк
        """
        if not data or not where:
            return 0
        
        # Формируем SET часть
        set_parts = []
        set_params = []
        for key, value in data.items():
            set_parts.append(sql.SQL("{column} = %s").format(column=sql.Identifier(key)))
            set_params.append(value)
        
        # Формируем WHERE часть
        where_parts = []
        where_params = []
        for key, value in where.items():
            where_parts.append(sql.SQL("{column} = %s").format(column=sql.Identifier(key)))
            where_params.append(value)
        
        query = sql.SQL("UPDATE {schema}.{table} SET {set_clause} WHERE {where_clause}").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table_name),
            set_clause=sql.SQL(", ").join(set_parts),
            where_clause=sql.SQL(" AND ").join(where_parts)
        )
        
        params = set_params + where_params
        
        try:
            with self._get_cursor() as (cursor, conn):
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Ошибка обновления: {e}")
            return 0
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete(
        self,
        table_name: str,
        where: Dict[str, Any],
        schema: str = "public",
        commit: bool = True
    ) -> int:
        """
        Удаляет строки из таблицы.
        
        Args:
            table_name: Имя таблицы
            where: Условия WHERE в виде словаря {column: value}
            schema: Схема БД (по умолчанию 'public')
            commit: Автоматически коммитить транзакцию
        
        Returns:
            Количество удаленных строк
        """
        if not where:
            # Защита от случайного удаления всех строк
            raise ValueError("WHERE условия обязательны для DELETE")
        
        # Формируем WHERE часть
        where_parts = []
        where_params = []
        for key, value in where.items():
            where_parts.append(sql.SQL("{column} = %s").format(column=sql.Identifier(key)))
            where_params.append(value)
        
        query = sql.SQL("DELETE FROM {schema}.{table} WHERE {where_clause}").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table_name),
            where_clause=sql.SQL(" AND ").join(where_parts)
        )
        
        try:
            with self._get_cursor() as (cursor, conn):
                cursor.execute(query, where_params)
                if commit:
                    conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return 0
    
    # ==================== UTILITY METHODS ====================
    
    def execute_raw(self, query: str, params: Optional[Tuple] = None, commit: bool = True) -> List[Dict[str, Any]]:
        """
        Выполняет произвольный SQL запрос.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            commit: Автоматически коммитить транзакцию
        
        Returns:
            Список результатов (для SELECT) или пустой список
        """
        try:
            with self._get_cursor() as (cursor, conn):
                cursor.execute(query, params)
                
                if commit:
                    conn.commit()
                
                # Пытаемся получить результаты
                try:
                    return [dict(row) for row in cursor.fetchall()]
                except psycopg2.ProgrammingError:
                    # Если нет результатов (INSERT, UPDATE, DELETE без RETURNING)
                    return []
        except Exception as e:
            print(f"Ошибка выполнения SQL: {e}")
            return []
    
    def begin_transaction(self):
        """Начинает транзакцию. Возвращает объект подключения для использования с commit/rollback."""
        return self._get_connection()
    
    def commit(self, connection: PsycopgConnection):
        """Коммитит транзакцию."""
        connection.commit()
        connection.close()
    
    def rollback(self, connection: PsycopgConnection):
        """Откатывает транзакцию."""
        connection.rollback()
        connection.close()
    
    def __enter__(self):
        """Контекстный менеджер: вход."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход."""
        # Соединения закрываются автоматически при каждом использовании _get_cursor
        # Здесь ничего не нужно закрывать
        return False

