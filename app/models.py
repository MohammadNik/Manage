# backend/app/models.py
from . import db
from datetime import datetime

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(50), nullable=True)
    
    grades = db.relationship('Grade', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    homework_statuses = db.relationship('HomeworkStatus', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    performance_logs = db.relationship('DailyPerformanceLog', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Student {self.id}: {self.first_name} {self.last_name}>"

class Grade(db.Model):
    __tablename__ = 'grade' # افزودن نام صریح جدول برای اطمینان
    id = db.Column(db.Integer, primary_key=True)
    date_str = db.Column(db.String(10), nullable=False) 
    subject = db.Column(db.String(100), nullable=False)
    performance = db.Column(db.String(50), nullable=False) # برای نمره توصیفی
    reason = db.Column(db.String(200), nullable=True) # برای توضیحات یا نمره عددی (به انتخاب شما)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    def __repr__(self):
        return f"<Grade {self.id}: S_ID={self.student_id}, Subj='{self.subject}', Perf='{self.performance}', Reason='{self.reason}'>"

class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=True) 
    defined_date = db.Column(db.String(10), nullable=False) 
    due_date = db.Column(db.String(10), nullable=False)     
    description = db.Column(db.Text, nullable=True)
    statuses = db.relationship('HomeworkStatus', backref='homework_details', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Homework {self.id}: '{self.title}' - Due: {self.due_date}>"

class HomeworkStatus(db.Model):
    __tablename__ = 'homework_status'
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="انجام نداده")
    submission_notes = db.Column(db.Text, nullable=True) 
    __table_args__ = (db.UniqueConstraint('homework_id', 'student_id', name='_homework_student_uc'),)

    def __repr__(self):
        return f"<HomeworkStatus HS_ID:{self.homework_id}-S_ID:{self.student_id} Status: '{self.status}'>"

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date_str = db.Column(db.String(10), nullable=False) 
    reason = db.Column(db.String(200), nullable=True)   
    __table_args__ = (db.UniqueConstraint('student_id', 'date_str', name='_student_date_attendance_uc'),)

    def __repr__(self):
        return f"<Attendance Record S_ID:{self.student_id} Date:{self.date_str} Reason: '{self.reason}'>"

class DailyPerformanceLog(db.Model):
    __tablename__ = 'daily_performance_log'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date_str = db.Column(db.String(10), nullable=False)  
    log_text = db.Column(db.Text, nullable=False)       
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 

    def __repr__(self):
        return f"<DailyPerformanceLog ID:{self.id} S_ID:{self.student_id} Date:{self.date_str}>"