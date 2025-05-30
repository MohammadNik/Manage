# backend/run.py
from app import create_app # وارد کردن تابع create_app از پکیج app

app = create_app() # ایجاد نمونه برنامه با استفاده از فاکتوری

if __name__ == '__main__':
    app.run() # debug=True از فایل config خوانده می‌شود