from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, session
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models import db, Review, Course
from app.repositories import CourseRepository, UserRepository, CategoryRepository, ImageRepository

user_repository = UserRepository(db)
course_repository = CourseRepository(db)
category_repository = CategoryRepository(db)
image_repository = ImageRepository(db)

RATING_LABELS = {
    5: "Отлично",
    4: "Хорошо",
    3: "Удовлетворительно",
    2: "Плохо",
    1: "Ужасно"
}

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    pagination = course_repository.get_pagination_info(**search_params())
    courses = course_repository.get_all_courses(pagination=pagination)
    categories = category_repository.get_all_categories()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

@bp.route('/new')
@login_required
def new():
    course = course_repository.new_course()
    categories = category_repository.get_all_categories()
    users = user_repository.get_all_users()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = None 

    try:
        if f and f.filename:
            img = image_repository.add_image(f)

        image_id = img.id if img else None
        course = course_repository.add_course(**params(), background_image_id=image_id)
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        categories = category_repository.get_all_categories()
        users = user_repository.get_all_users()
        return render_template('courses/new.html',
                            categories=categories,
                            users=users,
                            course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))

def submit_review(course, existing_review, rating, text):
    rating = int(rating)
    if existing_review:
        course.rating_sum += rating - existing_review.rating
        existing_review.rating = rating
        existing_review.text = text
        existing_review.created_at = datetime.now()
    else:
        new_review = Review(
            rating=rating,
            text=text,
            course_id=course.id,
            user_id=current_user.id,
            created_at=datetime.now()
        )
        db.session.add(new_review)
        course.rating_sum += rating
        course.rating_num += 1


@bp.route('/<int:course_id>', methods=['GET', 'POST'])
def show(course_id):
    course = db.session.query(Course).get(course_id)
    if course is None:
        abort(404)

    existing_review = None
    if current_user.is_authenticated:
        existing_review = db.session.query(Review).filter_by(course_id=course_id, user_id=current_user.id).first()

    if request.method == 'POST' and current_user.is_authenticated:
        rating = request.form['rating']
        text = request.form['text']
        submit_review(course, existing_review, rating, text)
        db.session.commit()
        return redirect(url_for('courses.show', course_id=course_id))

    reviews = (
        db.session.query(Review)
        .filter_by(course_id=course_id)
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'courses/show.html',
        course=course,
        reviews=reviews,
        existing_review=existing_review,
        rating_labels=RATING_LABELS
    )


@bp.route('/<int:course_id>/reviews', methods=['GET', 'POST'])
@login_required
def course_reviews(course_id):
    course = db.session.query(Course).get(course_id)
    if course is None:
        abort(404)

    existing_review = db.session.query(Review).filter_by(course_id=course_id, user_id=current_user.id).first()

    if request.method == 'POST':
        rating = request.form['rating']
        text = request.form['text']
        submit_review(course, existing_review, rating, text)
        db.session.commit()
        return redirect(url_for('courses.course_reviews', course_id=course_id))

    sort_by = request.args.get('sort_by', 'new')
    if sort_by == 'positive':
        order = Review.rating.desc()
    elif sort_by == 'negative':
        order = Review.rating.asc()
    else:
        order = Review.created_at.desc()

    page = request.args.get('page', 1, type=int)
    reviews = (
        db.session.query(Review)
        .filter_by(course_id=course_id)
        .order_by(order)
        .paginate(page=page, per_page=5)
    )

    return render_template(
        'courses/reviews.html',
        course=course,
        reviews=reviews,
        existing_review=existing_review,
        sort_by=sort_by,
        rating_labels=RATING_LABELS
    )
