import pytest
from app import app, posts_list
import re


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Лабораторная работа № 1" in response.text


def test_index_template(client, captured_templates):
    with captured_templates as templates:
        _ = client.get("/")
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "index.html"

def test_posts_page(client):
    response = client.get("/posts")
    assert response.status_code == 200
    assert "Посты" in response.text


def test_posts_template(client, captured_templates, mocker):
    with captured_templates as templates:
        mocker.patch("app.posts_list", return_value=posts_list(), autospec=True)
        _ = client.get("/posts")
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "posts.html"
        assert "posts" in context
        assert "title" in context


def test_post_page(client):
    response = client.get("/posts/0")
    assert response.status_code == 200
    assert "Заголовок поста" in response.text


def test_post_template(client, captured_templates, mocker):
    with captured_templates as templates:
        mocker.patch("app.posts_list", return_value=posts_list(), autospec=True)
        _ = client.get("/posts/0")
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "post.html"
        assert "post" in context


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert "Об авторе" in response.text


def test_about_template(client, captured_templates):
    with captured_templates as templates:
        _ = client.get("/about")
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "about.html"


def test_post_date_format(client):
    response = client.get("/posts/0")
    assert response.status_code == 200
    date_pattern = r"\b\d{2}\.\d{2}\.\d{4}\b"
    assert re.search(date_pattern, response.text), "Дата публикации не соответствует формату DD.MM.YYYY"


def test_post_contains_image(client):
    response = client.get("/posts/0")
    assert response.status_code == 200
    assert '<img src="' in response.text


def test_comments_are_present(client):
    response = client.get("/posts/0")
    assert response.status_code == 200
    assert "Оставьте комментарий" in response.text

def test_comments_and_replies(client):
    response = client.get("/posts/1")  
    assert response.status_code == 200
    assert '<h3 class="mt-5 text-start">Комментарии</h3>' in response.text
    assert '<div class="d-flex mt-4">' in response.text   
    assert '<h5 class="text-start">' in response.text  
    assert '<p class="text-justify">' in response.text  
    assert '<div class="d-flex mt-3 ms-4">' in response.text  
    assert '<h6 class="text-start">' in response.text  
    assert '<p class="text-justify">' in response.text  
 

def test_comment_form(client):
    response = client.get("/posts/0")
    assert response.status_code == 200
    assert '<textarea class="form-control"' in response.text
    assert '<button type="submit" class="btn btn-primary">Отправить</button>' in response.text


def test_avatar_is_present(client):
    response = client.get("/posts/0")
    assert response.status_code == 200
    assert 'avatar.jpg' in response.text


def test_404_for_nonexistent_post(client):
    response = client.get("/posts/999")
    assert response.status_code == 404


