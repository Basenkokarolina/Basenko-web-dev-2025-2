import pytest
from datetime import datetime
from app.repositories import LogsRepository

@pytest.fixture
def login_user_user_role(app, client, db_connector, example_roles):
    user_data = ("karolina", "karolina", "karolina", "karolina", "karolina", example_roles[1]['id'])
    connection = db_connector.connect()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users(username, password_hash, first_name, middle_name, last_name, role_id) "
            "VALUES (%s, SHA2(%s, 256), %s, %s, %s, %s);",
            user_data
        )
        connection.commit()
        cursor.execute("SELECT id FROM users WHERE username = %s;", (user_data[0],))
        user_id = cursor.fetchone()[0]

    yield {"id": user_id, "username": user_data[0], "password": user_data[1]}

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM visit_logs;")
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        connection.commit()


def test_user_cannot_access_admin_page_edit(client, app, login_user_user_role):
    with app.test_request_context():
        with client.session_transaction() as session:
            session['_user_id'] = str(login_user_user_role['id'])

        response = client.get('/users/1/edit', follow_redirects=False)
        assert response.status_code in (302, 308)

        assert '/users/' in response.location

def test_user_cannot_access_admin_page_new(client, app, login_user_user_role):
    with app.test_request_context():
        with client.session_transaction() as session:
            session['_user_id'] = str(login_user_user_role['id'])

        response = client.get('/users/new', follow_redirects=False)
        assert response.status_code in (302, 308)

        assert '/users/' in response.location

def test_user_cannot_access_admin_page_delete(client, app, login_user_user_role):
    with app.test_request_context():
        with client.session_transaction() as session:
            session['_user_id'] = str(login_user_user_role['id'])

        response = client.post('/users/2/delete', follow_redirects=False)
        assert response.status_code in (302, 308)

        assert '/users/' in response.location

def test_user_cannot_access_admin_by_pages(client, app, login_user_user_role):
    with app.test_request_context():
        with client.session_transaction() as session:
            session['_user_id'] = str(login_user_user_role['id'])

        response = client.get('/logs/by_pages', follow_redirects=False)
        assert response.status_code in (302, 308)

        assert '/users/' in response.location

def test_user_cannot_access_admin_by_users(client, app, login_user_user_role):
    with app.test_request_context():
        with client.session_transaction() as session:
            session['_user_id'] = str(login_user_user_role['id'])

        response = client.get('/logs/by_pages', follow_redirects=False)
        assert response.status_code in (302, 308)

        assert '/users/' in response.location

@pytest.fixture(autouse=True)
def clear_logs_table(db_connector):
    connection = db_connector.connect()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM visit_logs;")
        cursor.execute("ALTER TABLE visit_logs AUTO_INCREMENT = 1;")
    connection.commit()

def test_log_creation_and_storage(db_connector):
    repo = LogsRepository(db_connector)
    repo.create("/test-page", user_id=None)

    connection = db_connector.connect()
    with connection.cursor(named_tuple=True) as cursor:
        cursor.execute("SELECT * FROM visit_logs WHERE path = %s;", ("/test-page",))
        log_entry = cursor.fetchone()

    assert log_entry is not None
    assert log_entry.path == "/test-page"
    assert log_entry.user_id is None


def test_pagination_functionality(db_connector):
    repo = LogsRepository(db_connector)
    for i in range(25):
        repo.create(f"/page-{i}", user_id=None)

    pagination = repo.get_paginated(page=2, per_page=10, user_id=None)

    assert pagination.total_items == 25
    assert pagination.items_per_page == 10
    assert pagination.current_page == 2
    assert len(pagination.data_slice) == 10


def test_page_visit_statistics(db_connector):
    repo = LogsRepository(db_connector)
    repo.create("/home", user_id=None)
    repo.create("/home", user_id=None)
    repo.create("/about", user_id=None)

    stats = repo.get_page_stats()

    home_stat = next((stat for stat in stats if stat.path == "/home"), None)
    about_stat = next((stat for stat in stats if stat.path == "/about"), None)

    assert home_stat is not None
    assert home_stat.visit_count == 2
    assert about_stat is not None
    assert about_stat.visit_count == 1


def test_log_persistence(db_connector):
    repo = LogsRepository(db_connector)
    repo.create("/test-page", user_id=None)

    connection = db_connector.connect()
    with connection.cursor(named_tuple=True) as cursor:
        cursor.execute("SELECT * FROM visit_logs WHERE path = %s;", ("/test-page",))
        log = cursor.fetchone()

    assert log is not None
    assert log.path == "/test-page"
    assert log.user_id is None


def test_logs_ordering(db_connector):
    repo = LogsRepository(db_connector)

    connection = db_connector.connect()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM visit_logs;")
    connection.commit()

    repo.create("/page1", user_id=None)
    import time
    time.sleep(1)
    repo.create("/page2", user_id=None)

    with connection.cursor(named_tuple=True) as cursor:
        cursor.execute("SELECT * FROM visit_logs ORDER BY created_at DESC;")
        logs = cursor.fetchall()

    assert len(logs) == 2
    assert logs[0].path == "/page2"
    assert logs[1].path == "/page1"


def test_aggregated_page_stats_report(db_connector):
    repo = LogsRepository(db_connector)

    connection = db_connector.connect()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM visit_logs;")
    connection.commit()

    repo.create("/home", user_id=None)
    repo.create("/about", user_id=None)
    repo.create("/home", user_id=None)
    repo.create("/contact", user_id=None)
    repo.create("/home", user_id=None)

    stats = repo.get_page_stats()

    assert len(stats) == 3

    home_stat = next((s for s in stats if s.path == "/home"), None)
    about_stat = next((s for s in stats if s.path == "/about"), None)
    contact_stat = next((s for s in stats if s.path == "/contact"), None)

    assert home_stat is not None
    assert home_stat.visit_count == 3

    assert about_stat is not None
    assert about_stat.visit_count == 1

    assert contact_stat is not None
    assert contact_stat.visit_count == 1
    assert stats[0].path == "/home"
    assert stats[0].visit_count == 3
    assert stats[1].visit_count == 1
    assert stats[2].visit_count == 1

