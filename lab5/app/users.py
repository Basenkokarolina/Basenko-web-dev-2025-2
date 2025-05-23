from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from mysql import connector
from .decorators import check_rights
from .repositories import UserRepository, RoleRepository
from app import db
from .decorators import before_request
import re

user_repository = UserRepository(db)
role_repository = RoleRepository(db)

bp = Blueprint('users', __name__, url_prefix='/users')

def validate_username(username):
    if not username:
        return "Поле не может быть пустым"
    if len(username) < 5:
        return "Логин должен содержать не менее 5 символов"
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return "Логин должен содержать только латинские буквы и цифры"
    return None

def validate_password(password):
    if not password:
        return "Поле не может быть пустым"
    if len(password) < 8:
        return "Пароль должен содержать не менее 8 символов"
    if len(password) > 128:
        return "Пароль должен содержать не более 128 символов"
    if ' ' in password:
        return "Пароль не должен содержать пробелов"
    if not re.search(r'[A-ZА-Я]', password):
        return "Пароль должен содержать хотя бы одну заглавную букву"
    if not re.search(r'[a-zа-я]', password):
        return "Пароль должен содержать хотя бы одну строчную букву"
    if not re.search(r'[0-9]', password):
        return "Пароль должен содержать хотя бы одну цифру"
    if not re.match(r'^[A-Za-zА-Яа-я0-9~!?@#$%^&*_\-+()\[\]{}><\/\\|"\'\.,:;]+$', password):
        return "Пароль содержит недопустимые символы"
    return None

def validate_name(name, field_name):
    if not name:
        return f"Поле {field_name} не может быть пустым"
    return None


@bp.errorhandler(connector.errors.DatabaseError)
def handler():
    pass

@bp.route('/')
@before_request()
def index():
    if current_user.is_authenticated:
        current_user_id = current_user.get_id()
    else:
        current_user_id = None

    if current_user.is_authenticated:
        user_role = user_repository.get_by_id(current_user_id).role
    else:
        user_role = None

    return render_template('users/index.html', users=user_repository.all(), user_role=user_role)

@bp.route('/<int:user_id>')
@before_request()
@check_rights('view')
def show(user_id):
    user = user_repository.get_by_id(user_id)
    if user is None:
        flash('Пользователя нет в базе данных', 'danger')
        return redirect(url_for('users.index'))
    user_role = role_repository.get_by_id(user.role_id)
    return render_template('users/show.html', user_data=user, user_role=getattr(user_role, 'name', ''))


@bp.route('/new', methods=['POST', 'GET'])
@before_request()
@login_required
@check_rights('create')
def new():
    if current_user.is_authenticated:
        current_user_id = current_user.get_id()
    else:
        current_user_id = None

    if current_user.is_authenticated:
        user_role = user_repository.get_by_id(current_user_id).role
    else:
        user_role = None

    user_data = {}
    errors = {}

    if request.method == 'POST':
        fields = ('username', 'password', 'first_name', 'middle_name', 'last_name', 'role_id')
        user_data = {field: request.form.get(field) or None for field in fields}

        errors['username'] = validate_username(user_data['username'])
        errors['password'] = validate_password(user_data['password'])
        errors['first_name'] = validate_name(user_data['first_name'], 'имя')
        errors['last_name'] = validate_name(user_data['last_name'], 'фамилия')

        if not any(errors.values()):
            try:
                user_repository.create(**user_data)
                flash('Учетная запись успешно создана', 'success')
                return redirect(url_for('users.index'))
            except connector.errors.DatabaseError as e:
                flash(f'Произошла ошибка при создании записи: {str(e)}', 'danger')
                db.connect().rollback()
        else:
            flash('Произошла ошибка при создании записи', 'danger')

    return render_template('users/new.html',
                           user_data=user_data,
                           roles=role_repository.all(),
                           errors=errors,
                           user_role=user_role)


@bp.route('/<int:user_id>/delete', methods=['POST', 'GET'])
@before_request()
@login_required
@check_rights('delete')
def delete(user_id):
    try:
        user = user_repository.get_by_id(user_id)
        if not user:
            flash('Пользователь не найден', 'danger')
            return redirect(url_for('users.index'))

        user_repository.delete(user_id)
        flash('Учетная запись успешно удалена', 'success')

    except connector.errors.DatabaseError as e:
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
        db.connect().rollback()

    except Exception as e:
        flash(f'Произошла непредвиденная ошибка: {str(e)}', 'danger')
        db.connect().rollback()

    return redirect(url_for('users.index'))

@bp.route('/<int:user_id>/edit', methods = ['POST', 'GET'])
@before_request()
@login_required
@check_rights('edit')
def edit(user_id):
    if current_user.is_authenticated:
        current_user_id = current_user.get_id()
    else:
        current_user_id = None

    if current_user.is_authenticated:
        user_role = user_repository.get_by_id(current_user_id).role
    else:
        user_role = None

    user_data = {}
    errors = {}

    user = user_repository.get_by_id(user_id)
    if user is None:
        flash('Пользователя нет в базе данных', 'danger')
        return redirect(url_for('users.index'))
    
    if request.method == 'POST':
        fields = ('first_name', 'middle_name', 'last_name', 'role_id')
        user_data = { field: request.form.get(field) or None for field in fields}

        errors['first_name'] = validate_name(user_data['first_name'], 'имя')
        errors['last_name'] = validate_name(user_data['last_name'], 'фамилия')

        user_data["user_id"] = user_id
        if not any(errors.values()):
            try:
                user_repository.update(**user_data)
                flash('Учетная запись успешно изменена', 'success')
                return redirect(url_for('users.index'))
            except connector.errors.DatabaseError as e:
                flash(f'Произошла ошибка при редактировании записи: {str(e)}', 'danger')
                db.connect().rollback()
        else:
            flash('Произошла ошибка при редактировании записи.', 'danger')

    return render_template('users/edit.html',
                           user_data=user,
                           roles=role_repository.all(),
                           errors=errors,
                           user_role=user_role)


@bp.route('/change-password', methods=['GET', 'POST'])
@before_request()
@login_required
def change_password():
    errors = {}

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not user_repository.check_password(current_user.id, current_password):
            errors['current_password'] = "Неверный текущий пароль"

        password_error = validate_password(new_password)
        if password_error:
            errors['new_password'] = password_error

        if new_password != confirm_password:
            errors['confirm_password'] = "Пароли не совпадают"

        if not errors:
            try:
                user_repository.verify_password(current_user.id, new_password)
                flash('Пароль успешно изменен', 'success')
                return redirect(url_for('index'))
            except connector.errors.DatabaseError as e:
                flash(f'Ошибка при изменении пароля: {str(e)}', 'danger')
                db.connect().rollback()
        else:
            flash('Произошла ошибка при изменении пароля.', 'danger')

    return render_template('users/change_password.html', errors=errors)