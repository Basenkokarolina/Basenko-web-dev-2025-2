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
            # Проверка аутентификации
            if not current_user.is_authenticated:
                flash('Необходима авторизация', 'danger')
                return redirect(url_for('auth.login'))

            # Получение пользователя и его роли
            user = user_repo.get_by_id(current_user.get_id())
            if not user or not user.role:
                flash('Ошибка доступа к данным пользователя.', 'danger')
                return redirect(url_for('users.index'))

            # Определение доступных действий для ролей
            role_permissions = {
                'admin': ['create', 'edit', 'delete', 'view', 'by_pages', 'by_users'],
                'user': ['self_edit', 'self_view']
            }

            # Проверка прав
            is_allowed = False
            if user.role in role_permissions:
                allowed_actions = role_permissions[user.role]
                target_user_id = kwargs.get('user_id')
                current_user_id = int(current_user.get_id())

                # Основная проверка доступа
                if action in allowed_actions:
                    is_allowed = True
                elif action == 'edit' and target_user_id == current_user_id and 'self_edit' in allowed_actions:
                    is_allowed = True
                elif action == 'view' and target_user_id == current_user_id and 'self_view' in allowed_actions:
                    is_allowed = True

            if is_allowed:
                return view_func(*args, **kwargs)

            # Если доступ запрещен
            flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
            return redirect(url_for('users.index'))

        return wrapped_view
    return decorator

def before_request():
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            try:
                user_id = current_user.get_id() if current_user.is_authenticated else None
                if not request.path.startswith('/static/'):
                    logs_repository.create(request.path, user_id)
            except Exception as e:
                print(f"Ошибка при логировании посещения: {str(e)}")

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator