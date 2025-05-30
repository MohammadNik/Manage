# backend/app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate # جدید: وارد کردن Migrate
from flask_cors import CORS # جدید: وارد کردن CORS
from .config import Config

db = SQLAlchemy()
migrate = Migrate() # جدید: ایجاد یک نمونه سراسری از Migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # جدید: فعال‌سازی CORS برای برنامه
    # resources={r"/api/*": {"origins": "*"}} یعنی به تمام مسیرهایی که با /api/ شروع می‌شوند
    # از هر مبدا (origins: "*") اجازه دسترسی بده. برای محیط توسعه این تنظیم مناسب است.
    # در محیط محصول نهایی، بهتر است origins را به دامنه فرانت‌اند خود محدود کنید.
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # بخش اشکال‌زدایی قبلی را می‌توانید حذف کنید اگر دیگر نیازی نیست
    # print("--- وضعیت app.config دقیقا قبل از db.init_app(app) ---")
    # ...
    # print("----------------------------------------------------")

    db.init_app(app)
    migrate.init_app(app, db) # جدید: مقداردهی اولیه migrate با app و db


    from .routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context(): # این اطمینان می‌دهد که مدل‌ها در context برنامه شناخته می‌شوند
        from . import models

    return app