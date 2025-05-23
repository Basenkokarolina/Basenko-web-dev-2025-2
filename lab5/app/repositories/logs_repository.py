import csv
import io
from ..pagination import Pagination

class LogsRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_all(self):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM visit_logs ORDER BY created_at DESC;")
            logs = cursor.fetchall()
        return logs

    def create(self, path, user_id=None):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            query = (
                "INSERT INTO visit_logs (path, user_id) VALUES (%s, %s);"
            )
            data = (path, user_id)
            cursor.execute(query, data)
            connection.commit()

    def get_paginated(self, page=1, per_page=20, user_id=None):
        connection = self.db_connector.connect()

        if user_id:
            query = (
                "SELECT * FROM visit_logs WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s;"
            )
            count_query = "SELECT COUNT(*) as count FROM visit_logs WHERE user_id = %s"
            params = (user_id, per_page, (page - 1) * per_page)
            count_params = (user_id,)
        else:
            query = (
                "SELECT * FROM visit_logs ORDER BY created_at DESC LIMIT %s OFFSET %s;"
            )
            count_query = "SELECT COUNT(*) as count FROM visit_logs"
            params = (per_page, (page - 1) * per_page)
            count_params = ()

        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute(query, params)
            items = cursor.fetchall()
            cursor.execute(count_query, count_params)
            total = cursor.fetchone().count

        return Pagination(page, per_page, total, items)

    def get_page_stats(self):
        connection = self.db_connector.connect()
        query = (
           "SELECT path, COUNT(*) as visit_count FROM visit_logs GROUP BY path ORDER BY visit_count DESC;"
        )
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_user_stats(self):
        connection = self.db_connector.connect()
        query = (
           "SELECT user_id, COUNT(*) as visit_count FROM visit_logs GROUP BY user_id ORDER BY visit_count DESC;"
        )
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def export_page_stats_to_csv(self):
        stats = self.get_page_stats()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')

        writer.writerow(['№', 'Страница', 'Количество посещений'])

        for i, stat in enumerate(stats, 1):
            writer.writerow([i, stat.path, stat.visit_count])

        output.seek(0)
        return output

    def export_user_stats_to_csv(self, user_repository):
        stats = self.get_user_stats()

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

        output.seek(0)
        return output