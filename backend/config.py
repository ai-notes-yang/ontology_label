import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "ontology_review.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

