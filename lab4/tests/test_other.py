import pytest
import re
from app.users import validate_username, validate_password, validate_name

@pytest.mark.parametrize("username, expected_error", [ #некорректные значения
    ("", "Поле не может быть пустым"),
    ("   ", "Логин должен содержать не менее 5 символов"),
    ("a"*4, "Логин должен содержать не менее 5 символов"),
    ("user@name", "Логин должен содержать только латинские буквы и цифры"),
    ("user имя", "Логин должен содержать только латинские буквы и цифры"),
    ("validUser", None),
    ("user123", None),
])
def test_validate_username(username, expected_error): #Проверка логина
    assert validate_username(username) == expected_error


@pytest.mark.parametrize("password, expected_error", [ #некорректные значения
    ("", "Поле не может быть пустым"),
    ("A1b", "Пароль должен содержать не менее 8 символов"),
    ("lowercase1", "Пароль должен содержать хотя бы одну заглавную букву"),
    ("UPPERCASE1", "Пароль должен содержать хотя бы одну строчную букву"),
    ("ValidPass123", None),
])
def test_validate_password(password, expected_error): #Проверка пароля
    assert validate_password(password) == expected_error

def test_validate_name(): #Проверка имени
    assert validate_name("", "имя") == "Поле имя не может быть пустым"
    assert validate_name("Иван", "имя") is None