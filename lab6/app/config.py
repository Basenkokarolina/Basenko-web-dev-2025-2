import os

SECRET_KEY = '6e623c8a4de6314bcc23fbd0d2ac48b02440494590cb6c68d98390899a6e9d21'

SQLALCHEMY_DATABASE_URI = 'sqlite:///project.db'
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:mars2006@localhost:3306/vebdb'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    '..',
    'media', 
    'images'
)
