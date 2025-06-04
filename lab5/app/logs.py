import re
from flask import Flask, render_template, session, request, redirect, url_for, flash, Blueprint, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from mysql import connector
from .decorators import check_rights, before_request
import io
import csv

from .repositories import UserRepository, RoleRepository, LogsRepository
from app import db

user_repository = UserRepository(db)
role_repository = RoleRepository(db)
logs_repository = LogsRepository(db)

bp = Blueprint('logs', __name__, url_prefix='/logs')


@bp.route('/', endpoint='index')
@before_request
@login_required
def index():
    if current_user.is_authenticated:
        current_user_id = current_user.get_id()
    else:
        current_user_id = None

    if current_user.is_authenticated:
        user_role = user_repository.get_by_id(current_user_id).role
    else:
        user_role = None

    page = request.args.get('page', 1, type=int)
    per_page = 20

    user_id_for_filter = current_user_id if user_role != 'admin' else None
    visits = logs_repository.get_paginated(
        page=page,
        per_page=per_page,
        user_id=user_id_for_filter
    )

    def get_user(user_id):
        return user_repository.get_by_id(user_id) if user_id else None

    return render_template('logs/index.html',
                           visits=visits,
                           get_user=get_user,
                           user_role=user_role)

@bp.route('/by_pages')
@before_request
@login_required
@check_rights('by_pages')
def by_pages():
    stats = logs_repository.get_page_stats()
    return render_template('logs/by_pages.html', stats=stats)


@bp.route('/by_users')
@before_request
@login_required
@check_rights('by_users')
def by_users():
    stats = logs_repository.get_user_stats()

    def get_user(user_id):
        return user_repository.get_by_id(user_id) if user_id else None

    return render_template('logs/by_users.html',
                           stats=stats,
                           get_user=get_user)

@bp.route('/export_pages_csv')
@login_required
@check_rights('by_pages')
def export_pages_csv():
    stats = logs_repository.get_page_stats()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow(['№', 'Страница', 'Количество посещений'])
    
    for i, stat in enumerate(stats, 1):
        writer.writerow([i, stat.path, stat.visit_count])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=page_stats.csv'
    return response

@bp.route('/export_users_csv')
@login_required
@check_rights('by_users')
def export_users_csv():
    stats = logs_repository.get_user_stats()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow(['№', 'Пользователь', 'Количество посещений'])
    
    for i, stat in enumerate(stats, 1):
        if stat.user_id:
            user = user_repository.get_by_id(stat.user_id)
            user_name = f"{user.last_name} {user.first_name} {user.middle_name or ''}"
        else:
            user_name = "Неаутентифицированный пользователь"
        
        writer.writerow([i, user_name, stat.visit_count])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=user_stats.csv'
    return response