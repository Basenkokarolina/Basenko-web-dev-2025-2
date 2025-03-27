import random
from functools import lru_cache
from flask import Flask, render_template
from faker import Faker
from flask import abort
from flask import request, make_response
import re

fake = Faker()

app = Flask(__name__)
application = app

images_ids = ['7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
              '2d2ab7df-cdbc-48a8-a936-35bba702def5',
              '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
              'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
              'cab5b7f2-774e-4884-a200-0c0180fa777f']

def generate_comments(replies=True):
    comments = []
    for _ in range(random.randint(1, 3)):
        comment = { 'author': fake.name(), 'text': fake.text() }
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    return {
        'title': 'Заголовок поста',
        'text': fake.paragraph(nb_sentences=100),  
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.jpg',
        'comments': generate_comments()
    }

@lru_cache
def posts_list():
    return sorted([generate_post(i) for i in range(5)], key=lambda p: p['date'], reverse=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/args')
def args():
    return render_template('args.html')

@app.route('/headers')
def headers():
    return render_template('headers.html')

@app.route('/cookies')
def cookies():
    resp = make_response(render_template('cookies.html'))
    if 'good' not in request.cookies:
        resp.set_cookie('good', 'day')
    else:
        resp.set_cookie('good', expires=0)
    return resp

@app.route('/form', methods=['GET', 'POST'])
def form():
    return render_template('form.html')

@app.route('/phone', methods=['GET', 'POST'])
def phone():
    formatted_number = ""
    error_message = ""
    
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        if not re.match(r'^[\d\s()+.-]*$', phone): 
            error_message = "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
        if not error_message:
            digits = re.sub(r'\D', '', phone)
            if len(digits) == 11 and digits.startswith(('8', '7')):
                pass  
            elif len(digits) == 10:
                digits = '8' + digits
            else:
                error_message = "Недопустимый ввод. Неверное количество цифр."
            if not error_message:
                formatted_number = f"8-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return render_template('phone.html', formatted_number=formatted_number, error_message=error_message)

@app.route('/posts')
def posts():
    return render_template('posts.html', title='Посты', posts=posts_list())

@app.route('/posts/<int:index>')
def post(index):
    try:
        p = posts_list()[index]
        return render_template('post.html', title=p['title'], post=p)
    except IndexError:
        abort(404) 

@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')


