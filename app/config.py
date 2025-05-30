# backend/app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'یک-کلید-مخفی-بسیار-پیچیده-انتخاب-کنید'
    DEBUG = True

    # این دو خط بسیار مهم هستند
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False