"""
Модель пользователя для системы бронирования.
Предоставляет интерфейс для работы с таблицей users.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import bcrypt
from pg_driver import PostgreSQLDriver


class UserModel:
    """
    Модель пользователя для системы бронирования.
    
    Поля таблицы:
    - id: INTEGER PRIMARY KEY (автоматически)
    - name: TEXT NOT NULL - имя пользователя
    - email: TEXT UNIQUE NOT NULL - email адрес
    - phone: TEXT - номер телефона
    - password_hash: TEXT NOT NULL - хэш пароля
    - role: TEXT DEFAULT 'client' - роль (client, admin, manager)
    - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - дата создания
    - updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - дата обновления
    - is_active: BOOLEAN DEFAULT TRUE - активен ли пользователь
    """
    
    def __init__(self, db: Optional[PostgreSQLDriver] = None):
        """
        Инициализация модели пользователя.
        
        Args:
            db: Экземпляр PostgreSQLDriver. Если None, создается новый.
        """
        self.db = db or PostgreSQLDriver()
        self.table_name = "users"
        
        # Определение колонок таблицы
        self.columns = """
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        """
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Хэширует пароль с использованием bcrypt.
        
        Args:
            password: Пароль в открытом виде
            
        Returns:
            Хэшированный пароль (строка в формате bcrypt).
        """
        # Генерируем соль и хэшируем пароль
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """
        Проверяет соответствие пароля хэшу.
        
        Args:
            password: Пароль в открытом виде
            password_hash: Хэш пароля из базы данных
            
        Returns:
            True если пароль совпадает, False в противном случае.
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    def create_table(self) -> bool:
        """
        Создает таблицу users в базе данных.
        
        Returns:
            True если таблица создана успешно, False в противном случае.
        """
        return self.db.create_table(
            table_name=self.table_name,
            columns=self.columns,
            if_not_exists=True,
            auto_id=True
        )
    
    def create_user(
        self,
        name: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        role: str = "client",
        is_active: bool = True
    ) -> Optional[int]:
        """
        Создает нового пользователя.
        Пароль автоматически хэшируется перед сохранением.
        
        Args:
            name: Имя пользователя
            email: Email адрес (должен быть уникальным)
            password: Пароль в открытом виде (будет автоматически хэширован)
            phone: Номер телефона (опционально)
            role: Роль пользователя (client, admin, manager)
            is_active: Активен ли пользователь
            
        Returns:
            ID созданного пользователя или None в случае ошибки.
        """
        # Хэшируем пароль перед сохранением
        password_hash = self._hash_password(password)
        
        data = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "is_active": is_active,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        if phone:
            data["phone"] = phone
        
        try:
            return self.db.insert(table_name=self.table_name, data=data)
        except Exception as e:
            print(f"Ошибка при создании пользователя: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь с данными пользователя или None.
        """
        return self.db.select_one(
            table_name=self.table_name,
            where={"id": user_id}
        )
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по email.
        
        Args:
            email: Email адрес
            
        Returns:
            Словарь с данными пользователя или None.
        """
        return self.db.select_one(
            table_name=self.table_name,
            where={"email": email}
        )
    
    def get_all_users(
        self,
        active_only: bool = False,
        role: Optional[str] = None,
        limit: Optional[int] = None,
        order_by: str = "created_at DESC"
    ) -> List[Dict[str, Any]]:
        """
        Получает список всех пользователей с опциональными фильтрами.
        
        Args:
            active_only: Если True, возвращает только активных пользователей
            role: Фильтр по роли (client, admin, manager)
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки
            
        Returns:
            Список пользователей.
        """
        where = {}
        
        if active_only:
            where["is_active"] = True
        
        if role:
            where["role"] = role
        
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
    
    def update_user(
        self,
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
        Пароль автоматически хэшируется перед сохранением.
        
        Args:
            user_id: ID пользователя
            name: Новое имя (опционально)
            email: Новый email (опционально)
            phone: Новый телефон (опционально)
            password: Новый пароль в открытом виде (будет автоматически хэширован)
            role: Новая роль (опционально)
            is_active: Новый статус активности (опционально)
            
        Returns:
            True если обновление успешно, False в противном случае.
        """
        data = {
            "updated_at": datetime.now()
        }
        
        if name is not None:
            data["name"] = name
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if password is not None:
            # Хэшируем пароль перед сохранением
            data["password_hash"] = self._hash_password(password)
        if role is not None:
            data["role"] = role
        if is_active is not None:
            data["is_active"] = is_active
        
        try:
            updated = self.db.update(
                table_name=self.table_name,
                data=data,
                where={"id": user_id}
            )
            return updated > 0
        except Exception as e:
            print(f"Ошибка при обновлении пользователя: {e}")
            return False
    
    def delete_user(self, user_id: int, hard_delete: bool = False) -> bool:
        """
        Удаляет пользователя.
        
        Args:
            user_id: ID пользователя
            hard_delete: Если True, физически удаляет запись.
                        Если False, деактивирует пользователя (is_active=False).
            
        Returns:
            True если удаление успешно, False в противном случае.
        """
        if hard_delete:
            try:
                deleted = self.db.delete(
                    table_name=self.table_name,
                    where={"id": user_id}
                )
                return deleted > 0
            except Exception as e:
                print(f"Ошибка при удалении пользователя: {e}")
                return False
        else:
            # Мягкое удаление - деактивация
            return self.update_user(user_id, is_active=False)
    
    def count_users(
        self,
        active_only: bool = False,
        role: Optional[str] = None
    ) -> int:
        """
        Подсчитывает количество пользователей.
        
        Args:
            active_only: Если True, считает только активных
            role: Фильтр по роли
            
        Returns:
            Количество пользователей.
        """
        where = {}
        
        if active_only:
            where["is_active"] = True
        
        if role:
            where["role"] = role
        
        if where:
            return self.db.count(table_name=self.table_name, where=where)
        else:
            return self.db.count(table_name=self.table_name)
    
    def user_exists(self, email: str) -> bool:
        """
        Проверяет, существует ли пользователь с данным email.
        
        Args:
            email: Email адрес для проверки
            
        Returns:
            True если пользователь существует, False в противном случае.
        """
        user = self.get_user_by_email(email)
        return user is not None
    
    def verify_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет правильность пароля для пользователя с указанным email.
        
        Args:
            email: Email адрес пользователя
            password: Пароль для проверки
            
        Returns:
            Словарь с данными пользователя если пароль верен, None в противном случае.
        """
        user = self.get_user_by_email(email)
        
        if user is None:
            return None
        
        if not self._verify_password(password, user.get("password_hash", "")):
            return None
        
        # Возвращаем пользователя без пароля для безопасности
        user_data = dict(user)
        user_data.pop("password_hash", None)
        return user_data
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Изменяет пароль пользователя с проверкой старого пароля.
        
        Args:
            user_id: ID пользователя
            old_password: Текущий пароль
            new_password: Новый пароль
            
        Returns:
            True если пароль успешно изменен, False в противном случае.
        """
        user = self.get_user_by_id(user_id)
        
        if user is None:
            return False
        
        # Проверяем старый пароль
        if not self._verify_password(old_password, user.get("password_hash", "")):
            return False
        
        # Обновляем пароль
        return self.update_user(user_id, password=new_password)
