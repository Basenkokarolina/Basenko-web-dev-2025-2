import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Тесты на правильную обработку номера телефона
def test_valid_phone_with_spaces(client):
    response = client.post('/phone', data={'phone': ' +7 (123) 456-75-90 '})
    assert "Форматированный номер: 8-123-456-75-90" in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' not in response.data.decode('utf-8')  

def test_valid_phone_without_spaces(client):
    response = client.post('/phone', data={'phone': '8(123)4567590'})
    assert "Форматированный номер: 8-123-456-75-90" in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' not in response.data.decode('utf-8')  

def test_valid_phone_with_dots(client):
    response = client.post('/phone', data={'phone': '123.456.75.90'})
    assert "Форматированный номер: 8-123-456-75-90" in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' not in response.data.decode('utf-8')  

def test_valid_phone_with_plus(client):
    response = client.post('/phone', data={'phone': '+7 (123) 456-75-90'})
    assert "Форматированный номер: 8-123-456-75-90" in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' not in response.data.decode('utf-8')  

def test_invalid_phone_too_short(client):
    response = client.post('/phone', data={'phone': '123456789'})
    assert "Недопустимый ввод. Неверное количество цифр." in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' in response.data.decode('utf-8')  

def test_invalid_phone_too_long(client):
    response = client.post('/phone', data={'phone': '812345678901'})
    assert "Недопустимый ввод. Неверное количество цифр." in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' in response.data.decode('utf-8')  

def test_invalid_phone_with_letters(client):
    response = client.post('/phone', data={'phone': 'hhjjk'})
    assert "Недопустимый ввод. В номере телефона встречаются недопустимые символы." in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' in response.data.decode('utf-8')  

def test_invalid_phone_with_special_chars(client):
    response = client.post('/phone', data={'phone': '7899??44'})
    assert "Недопустимый ввод. В номере телефона встречаются недопустимые символы." in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' in response.data.decode('utf-8')  

# Тесты на отображение формы без отправки
def test_page_render(client):
    response = client.get('/phone')
    assert 'Введите номер телефона' in response.data.decode('utf-8')  
    assert 'Проверить' in response.data.decode('utf-8')  

# Тест на отсутствие ошибок при пустом поле
def test_empty_phone_field(client):
    response = client.post('/phone', data={'phone': ''})
    assert "Недопустимый ввод. Неверное количество цифр." in response.data.decode('utf-8')
    assert 'class="form-control is-invalid"' in response.data.decode('utf-8')  

#Тест на отображение переданных параметров URL
def test_args_with_parameters(client):
    response = client.get('/args?name=John&age=25')
    assert b'name' in response.data
    assert b'John' in response.data
    assert b'age' in response.data
    assert b'25' in response.data

#Тест на отображение заголовков запроса
def test_headers(client):
    response = client.get('/headers', headers={'X-Test-Header': 'TestValue'})
    assert b'X-Test-Header' in response.data
    assert b'TestValue' in response.data

#Тест на отображение стандартных заголовков запроса
def test_standard_headers(client):
    response = client.get('/headers')
    assert b'Host' in response.data  
    assert b'User-Agent' in response.data  

# Тест на установку cookie
def test_cookie_set(client):
    response = client.get('/cookies')
    assert 'good' in response.headers.get('Set-Cookie', '')
    assert 'good=day' in response.headers.get('Set-Cookie', '')

# Тест на удаление cookie
def test_cookie_absence_after_delete(client):
    client.get('/cookies') 
    client.get('/cookies')  
    response = client.get('/cookies') 
    assert b'good' not in response.data

# Тест для формы с введёнными данными
def test_form_submission(client):
    data = {
        'theme': 'Тема теста',
        'text': 'Текст для тестирования формы'
    }
    response = client.post('/form', data=data)
    assert 'Тема' in response.data.decode('utf-8')
    assert 'Тема теста' in response.data.decode('utf-8')
    assert 'Текст' in response.data.decode('utf-8')
    assert 'Текст для тестирования формы' in response.data.decode('utf-8')

# Тест для пустой формы
def test_empty_form_submission(client):
    response = client.post('/form', data={})
    assert 'Тема' in response.data.decode('utf-8')
    assert 'Текст' in response.data.decode('utf-8')
    assert '' in response.data.decode('utf-8')  


    
