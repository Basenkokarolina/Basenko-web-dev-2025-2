from functools import wraps
from flask import redirect, flash, url_for, request
from flask_login import current_user
from .repositories import UserRepository
from app import db
from .repositories.logs_repository import LogsRepository

user_repo = UserRepository(db)
logs_repository = LogsRepository(db)

def check_rights(action):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            # Проверка аутентификации пользователя
            if not current_user.is_authenticated:
                flash('Необходима авторизация', 'danger')
                return redirect(url_for('auth.login'))
            
            # Получение данных пользователя
            user = user_repo.get_by_id(current_user.get_id())
            if not user or not user.role:
                flash('Ошибка доступа к данным пользователя.', 'danger')
                return redirect(url_for('users.index'))
            
            # Определение прав для ролей
            role_permissions = {
                'admin': ['create', 'edit', 'delete', 'view', 'by_pages', 'by_users'],
                'user': ['self_edit', 'self_view']
            }
            
            # Проверка прав доступа
            allowed = False
            if user.role in role_permissions:
                permissions = role_permissions[user.role]
                target_id = kwargs.get('user_id')
                current_id = int(current_user.get_id())
                
                # Основная проверка прав
                if action in permissions:
                    allowed = True
                # Специальные случаи для self-действий
                elif action == 'edit' and target_id == current_id and 'self_edit' in permissions:
                    allowed = True
                elif action == 'view' and target_id == current_id and 'self_view' in permissions:
                    allowed = True
            
            # Если доступ разрешен - выполняем view-функцию
            if allowed:
                return view_func(*args, **kwargs)
            
            # Если доступ запрещен
            flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
            return redirect(url_for('users.index'))
        
        return wrapped_view
    return decorator

def before_request(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        log_request_path()  # Логируем путь запроса
        return view_func(*args, **kwargs)
    return wrapper


def log_request_path():
    if _should_log_request():
        try:
            user_id = _get_current_user_id()
            logs_repository.create(request.path, user_id)
        except Exception as e:
            print(str(e))

def _should_log_request():
    return not request.path.startswith('/static/')

def _get_current_user_id():
    return current_user.get_id() if current_user.is_authenticated else None