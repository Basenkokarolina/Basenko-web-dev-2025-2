from functools import lru_cache, wraps
from flask import Blueprint, render_template, session, redirect, url_for, request, make_response, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from .repositories import UserRepository
from .decorators import before_request
from app import db

user_repository = UserRepository(db)
bp = Blueprint('auth', __name__, url_prefix='/auth')

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Для доступа к запрашиваемой странице необходимо пройти процедуру аутентификации.'
login_manager.login_message_category = 'warning'


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.user_login = username


@login_manager.user_loader
def load_user(user_id):  # загружает пользователя по user_id из сессии
    user = user_repository.get_by_id(user_id)
    if user is not None:
        return User(user.id, user.username)
    return None


@bp.route('/login', methods=['GET', 'POST'])
@before_request()
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me', None) == 'on'

        user = user_repository.get_by_username_and_password(username, password)

        if user is not None:
            flash('Вы успешно аутентифицированы!', 'success')
            login_user(User(user.id, user.username), remember=remember_me)  # записываем данные пользователя в сессию
            next_url = request.args.get('next', url_for('index'))
            return redirect(next_url)
        flash('Пользователь не найден, проверьте корректность данных', 'danger')
    return render_template('auth/login.html')


@bp.route('/logout')
@before_request()
def logout():
    logout_user()
    return redirect(url_for('users.index'))