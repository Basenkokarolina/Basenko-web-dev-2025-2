import pytest
from app import app
from flask import request, session, url_for
from flask_login import current_user, login_manager

@pytest.fixture
def client():
    from app import app
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"  
    with app.test_client() as client:
        yield client

def test_counter_separate_sessions(client):  #Счётчик посещений работает корректно 
    with client.session_transaction() as sess:
        sess.clear() 
    response1 = client.get("/counter")
    assert "Вы посетили эту страницу 1 раз!" in response1.data.decode('utf-8')
    response2 = client.get("/counter")
    assert "Вы посетили эту страницу 2 раз!" in response2.data.decode('utf-8')
    response3 = client.get("/counter")
    assert "Вы посетили эту страницу 3 раз!" in response3.data.decode('utf-8')

def test_counter_independent_clients(client): #Счётчик посещений для каждого пользователя выводит своё значение
    with client.session_transaction() as sess:
        sess.clear()
    response1 = client.get("/counter")
    assert "Вы посетили эту страницу 1 раз!" in response1.data.decode('utf-8')
    with client.session_transaction() as sess:
        sess.clear()
    response2 = client.get("/counter")
    assert "Вы посетили эту страницу 1 раз!" in response2.data.decode('utf-8')  

def login(client, username, password, remember=False): #Функция-аутентификация
    return client.post(
        "/login",
        data={"username": username, "password": password, "remember_me": "on" if remember else "off"},
        follow_redirects=True
    )

def test_successful_login_redirect(client): #После успешной аутентификации пользователь перенаправляется на главную страницу, ему показывается соответствующее сообщение
    response = login(client, "user", "qwerty")
    assert "Вы успешно аутентифицированы!" in response.data.decode('utf-8')  
    assert response.request.path == "/"  

def test_failed_login(client): #После неудачной попытки аутентификации пользователь остаётся на той же странице, ему показывается сообщение об ошибке
    response = login(client, "wrong_user", "wrong_pass")
    assert "Пользователь не найден, проверьте корректность данных" in response.data.decode('utf-8')  
    assert response.request.path == "/login"  

def test_authenticated_access_to_secret_page(client): #Аутентифицированный пользователь имеет доступ к секретной странице
    login(client, "user", "qwerty")
    response = client.get("/secret")
    assert response.status_code == 200 
    assert "Секретная страница" in response.data.decode('utf-8')  

def test_anonymous_access_to_secret_page(client): #Неаутентифицированный пользователь при попытке доступа к секретной странице перенаправляется на страницу аутентификации с соответствующим сообщением
    response = client.get("/secret", follow_redirects=True)
    assert response.request.path == "/login"  
    assert "Для доступа к запрашиваемой странице необходимо пройти процедуру аутентификации." in response.data.decode('utf-8')  

def test_remember_me(client): #Параметр "Запомнить меня" работает корректно
    login(client, "user", "qwerty", remember=True)
    remember_token = client.get_cookie("remember_token")
    assert remember_token is not None 
    remember_token_value = remember_token.value if remember_token else None
    assert remember_token_value is not None and len(remember_token_value) > 0

def test_no_remember_me(client): #Параметр "Запомнить меня" работает корректно
    response = client.post('/login', data={
        'username': 'user',
        'password': 'qwerty',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert current_user.is_authenticated
    cookies = response.headers.getlist('Set-Cookie')
    remember_cookies = [c for c in cookies if 'remember_token' in c]
    assert len(remember_cookies) == 0

def test_redirect_after_authentication(client): #При аутентификации после неудачной попытки доступа к секретной странице пользователь автоматически перенаправляется на секретную страницу
    response = client.get('/secret', follow_redirects=False)
    assert response.status_code == 302
    assert '/login?next=%2Fsecret' in response.location
    response = client.post(response.location, data={
        'username': 'user',
        'password': 'qwerty'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith('/secret')

def test_navbar_for_guest(client): #Тест навбара для неаутентифицированного пользователя
    response = client.get("/")
    assert "Войти" in response.data.decode('utf-8') 
    assert "Выход" not in response.data.decode('utf-8') 
    secret_url = url_for('secret')  
    assert secret_url not in response.data.decode('utf-8')  

def test_navbar_for_authenticated_user(client): #Тест навбара для аутентифицированного пользователя
    login(client, "user", "qwerty") 
    response = client.get("/")
    assert "Выход" in response.data.decode('utf-8')  
    assert "Войти" not in response.data.decode('utf-8')  
    secret_url = url_for('secret')  
    assert secret_url in response.data.decode('utf-8')  
