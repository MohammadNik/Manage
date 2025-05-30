# backend/app/routes.py
from flask import Blueprint, jsonify, request
from . import db # db به صورت سراسری در app/__init__.py تعریف شده و قابل وارد کردن است
from .models import Student, Grade, Homework, HomeworkStatus, Attendance, DailyPerformanceLog
from datetime import datetime # برای استفاده احتمالی از تاریخ و زمان

main_bp = Blueprint('main', __name__)

# --- مسیرهای پایه و بررسی سلامت ---
@main_bp.route('/')
def index():
    return jsonify(message="سلام از Flask! به API مدیریت کلاس خوش آمدید. (ساختار با Blueprint)")

@main_bp.route('/api/health')
def health_check():
    return jsonify(status="OK", message="سرور بک‌اند فعال و در دسترس است.")

# --- API Endpoints برای دانش‌آموزان (Students) ---
@main_bp.route('/api/students', methods=['GET'])
def get_students():
    try:
        students_from_db = Student.query.order_by(Student.last_name, Student.first_name).all()
        students_list = []
        for student in students_from_db:
            students_list.append({
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "student_class": student.student_class
            })
        return jsonify(students_list)
    except Exception as e:
        print(f"خطا در دریافت اطلاعات دانش‌آموزان: {e}")
        return jsonify(message="خطا در دریافت اطلاعات دانش‌آموزان", error=str(e)), 500

@main_bp.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    try:
        student = Student.query.get(student_id)
        if student:
            return jsonify({
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "student_class": student.student_class
            })
        else:
            return jsonify(message="دانش‌آموز با این شناسه یافت نشد."), 404
    except Exception as e:
        print(f"خطا در دریافت اطلاعات دانش‌آموز {student_id}: {e}")
        return jsonify(message="خطا در دریافت اطلاعات دانش‌آموز", error=str(e)), 500

@main_bp.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        if not data or not data.get('first_name') or not data.get('last_name'):
            return jsonify(message="فیلدهای 'first_name' و 'last_name' ضروری هستند."), 400

        new_student = Student(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            student_class=data.get('student_class', '').strip() or None
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify({
            "id": new_student.id,
            "first_name": new_student.first_name,
            "last_name": new_student.last_name,
            "student_class": new_student.student_class,
            "message": "دانش‌آموز با موفقیت اضافه شد."
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"خطا در افزودن دانش‌آموز: {e}")
        return jsonify(message="خطا در افزودن دانش‌آموز", error=str(e)), 500

@main_bp.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        student_to_update = Student.query.get(student_id)
        if not student_to_update:
            return jsonify(message="دانش‌آموز با این شناسه یافت نشد."), 404

        data = request.get_json()
        if not data:
            return jsonify(message="داده‌ای برای به‌روزرسانی ارسال نشده است."), 400

        if 'first_name' in data and data['first_name'].strip():
            student_to_update.first_name = data['first_name'].strip()
        if 'last_name' in data and data['last_name'].strip():
            student_to_update.last_name = data['last_name'].strip()
        if 'student_class' in data:
            student_to_update.student_class = data.get('student_class', '').strip() or None
        
        db.session.commit()
        return jsonify({
            "id": student_to_update.id,
            "first_name": student_to_update.first_name,
            "last_name": student_to_update.last_name,
            "student_class": student_to_update.student_class,
            "message": "اطلاعات دانش‌آموز با موفقیت به‌روزرسانی شد."
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در به‌روزرسانی دانش‌آموز {student_id}: {e}")
        return jsonify(message="خطا در به‌روزرسانی اطلاعات دانش‌آموز", error=str(e)), 500

@main_bp.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        student_to_delete = Student.query.get(student_id)
        if not student_to_delete:
            return jsonify(message="دانش‌آموز با این شناسه یافت نشد."), 404
        
        # قبل از حذف دانش‌آموز، باید تمام رکوردهای وابسته در جداول دیگر که cascade ندارند یا می‌خواهیم به صورت دستی مدیریت کنیم را حذف کنیم
        # Grade, HomeworkStatus, Attendance, DailyPerformanceLog همگی cascade='all, delete-orphan' دارند، پس خودکار حذف می‌شوند.

        db.session.delete(student_to_delete)
        db.session.commit()
        return jsonify(message=f"دانش‌آموز '{student_to_delete.first_name} {student_to_delete.last_name}' و تمام داده‌های مرتبط با او با موفقیت حذف شدند."), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در حذف دانش‌آموز {student_id}: {e}")
        return jsonify(message="خطا در حذف دانش‌آموز", error=str(e)), 500

# --- API Endpoints برای نمرات (Grades) ---
# با مدل Grade ساده شده (performance رشته‌ای، reason رشته‌ای)
@main_bp.route('/api/grades', methods=['POST'])
def add_grade():
    try:
        data = request.get_json()
        if not data: return jsonify(message="داده‌ای ارسال نشده است."), 400
        
        required_fields = ['student_id', 'date_str', 'subject', 'performance']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify(message=f"فیلد '{field}' ضروری است و نمی‌تواند خالی باشد."), 400
        
        student = Student.query.get(data['student_id'])
        if not student: return jsonify(message=f"دانش‌آموزی با شناسه '{data['student_id']}' یافت نشد."), 404

        new_grade = Grade(
            student_id=data['student_id'],
            date_str=data['date_str'],
            subject=data['subject'],
            performance=data['performance'], # نمره توصیفی
            reason=data.get('reason')      # دلیل یا نمره عددی (به انتخاب شما)
        )
        db.session.add(new_grade)
        db.session.commit()
        return jsonify({
            "id": new_grade.id, "student_id": new_grade.student_id,
            "student_name": f"{new_grade.student.first_name} {new_grade.student.last_name}",
            "date_str": new_grade.date_str, "subject": new_grade.subject,
            "performance": new_grade.performance, "reason": new_grade.reason,
            "message": "نمره با موفقیت ثبت شد."
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"خطا در افزودن نمره: {e}")
        return jsonify(message="خطا در ثبت نمره", error=str(e)), 500

@main_bp.route('/api/grades', methods=['GET'])
def get_grades():
    try:
        student_id = request.args.get('student_id', type=int)
        date_str = request.args.get('date_str')
        subject = request.args.get('subject')
        query = Grade.query
        if date_str: query = query.filter_by(date_str=date_str)
        if student_id: query = query.filter_by(student_id=student_id)
        if subject: query = query.filter_by(subject=subject)
        grades_from_db = query.order_by(Grade.student_id, Grade.id).all()
        grades_list = [{
            "id": grade.id, "student_id": grade.student_id,
            "student_name": f"{grade.student.first_name} {grade.student.last_name}",
            "date_str": grade.date_str, "subject": grade.subject,
            "performance": grade.performance, "reason": grade.reason
        } for grade in grades_from_db]
        return jsonify(grades_list)
    except Exception as e:
        print(f"خطا در دریافت نمرات: {e}")
        return jsonify(message="خطا در دریافت اطلاعات نمرات", error=str(e)), 500

@main_bp.route('/api/grades/<int:grade_id>', methods=['PUT'])
def update_grade(grade_id):
    try:
        grade_to_update = Grade.query.get(grade_id)
        if not grade_to_update: return jsonify(message="نمره با این شناسه یافت نشد."), 404
        data = request.get_json()
        if not data: return jsonify(message="داده‌ای برای به‌روزرسانی ارسال نشده است."), 400

        if 'student_id' in data:
            student = Student.query.get(data['student_id'])
            if not student: return jsonify(message=f"دانش‌آموزی با شناسه '{data['student_id']}' یافت نشد."), 404
            grade_to_update.student_id = data['student_id']
        if 'date_str' in data and data['date_str'].strip(): grade_to_update.date_str = data['date_str'].strip()
        if 'subject' in data and data['subject'].strip(): grade_to_update.subject = data['subject'].strip()
        if 'performance' in data and data['performance'].strip(): grade_to_update.performance = data['performance'].strip()
        if 'reason' in data: grade_to_update.reason = data.get('reason', '').strip() or None
        
        db.session.commit()
        return jsonify({
            "id": grade_to_update.id, "student_id": grade_to_update.student_id,
            "student_name": f"{grade_to_update.student.first_name} {grade_to_update.student.last_name}",
            "date_str": grade_to_update.date_str, "subject": grade_to_update.subject,
            "performance": grade_to_update.performance, "reason": grade_to_update.reason,
            "message": "نمره با موفقیت به‌روزرسانی شد."
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در به‌روزرسانی نمره {grade_id}: {e}")
        return jsonify(message="خطا در به‌روزرسانی نمره", error=str(e)), 500

@main_bp.route('/api/grades/<int:grade_id>', methods=['DELETE'])
def delete_grade(grade_id):
    try:
        grade_to_delete = Grade.query.get(grade_id)
        if not grade_to_delete: return jsonify(message="نمره با این شناسه یافت نشد."), 404
        db.session.delete(grade_to_delete)
        db.session.commit()
        return jsonify(message=f"نمره با شناسه {grade_id} با موفقیت حذف شد."), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در حذف نمره {grade_id}: {e}")
        return jsonify(message="خطا در حذف نمره", error=str(e)), 500

# --- API Endpoints برای تکالیف (Homeworks) ---
@main_bp.route('/api/homeworks', methods=['POST'])
def create_homework():
    try:
        data = request.get_json()
        if not data: return jsonify(message="داده‌ای ارسال نشده است."), 400
        required_fields = ['title', 'due_date', 'defined_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify(message=f"فیلد '{field}' ضروری است و نمی‌تواند خالی باشد."), 400

        new_homework = Homework(
            title=data['title'],
            subject=data.get('subject'), 
            defined_date=data['defined_date'], 
            due_date=data['due_date'],
            description=data.get('description')
        )
        db.session.add(new_homework)
        db.session.flush()
        target_student_ids = data.get('target_student_ids', [])
        if isinstance(target_student_ids, list) and target_student_ids:
            created_statuses = 0
            for student_id in target_student_ids:
                student = Student.query.get(student_id)
                if student:
                    existing_status = HomeworkStatus.query.filter_by(homework_id=new_homework.id, student_id=student.id).first()
                    if not existing_status:
                        status_entry = HomeworkStatus(homework_id=new_homework.id, student_id=student.id, status="محول شده")
                        db.session.add(status_entry)
                        created_statuses +=1
            print(f"{created_statuses} وضعیت تکلیف برای دانش‌آموزان هدف ایجاد شد.")
        db.session.commit()
        return jsonify({
            "id": new_homework.id, "title": new_homework.title, "subject": new_homework.subject,
            "defined_date": new_homework.defined_date, "due_date": new_homework.due_date,
            "description": new_homework.description,
            "message": "تکلیف با موفقیت ایجاد و به دانش‌آموزان هدف تخصیص داده شد."
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"خطا در ایجاد تکلیف: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(message="خطا در ایجاد تکلیف", error=str(e)), 500

@main_bp.route('/api/homeworks', methods=['GET'])
def get_all_homeworks():
    try:
        homework_assignments = Homework.query.order_by(Homework.due_date.desc()).all()
        homeworks_list = [{
            "id": hw.id, "title": hw.title, "subject": hw.subject,
            "defined_date": hw.defined_date, "due_date": hw.due_date,
            "description": hw.description
        } for hw in homework_assignments]
        return jsonify(homeworks_list)
    except Exception as e:
        print(f"خطا در دریافت لیست تکالیف: {e}")
        return jsonify(message="خطا در دریافت لیست تکالیف", error=str(e)), 500

@main_bp.route('/api/homeworks/<int:homework_id>', methods=['GET'])
def get_homework(homework_id):
    try:
        hw = Homework.query.get(homework_id)
        if not hw: return jsonify(message="تکلیف با این شناسه یافت نشد."), 404
        return jsonify({
            "id": hw.id, "title": hw.title, "subject": hw.subject,
            "defined_date": hw.defined_date, "due_date": hw.due_date,
            "description": hw.description
        })
    except Exception as e:
        print(f"خطا در دریافت تکلیف {homework_id}: {e}")
        return jsonify(message="خطا در دریافت تکلیف", error=str(e)), 500

@main_bp.route('/api/homeworks/<int:homework_id>', methods=['PUT'])
def update_homework(homework_id):
    try:
        hw_to_update = Homework.query.get(homework_id)
        if not hw_to_update: return jsonify(message="تکلیف با این شناسه یافت نشد."), 404
        data = request.get_json()
        if not data: return jsonify(message="داده‌ای برای به‌روزرسانی ارسال نشده است."), 400

        if 'title' in data and data['title'].strip(): hw_to_update.title = data['title'].strip()
        if 'subject' in data: hw_to_update.subject = data.get('subject', '').strip() or None
        if 'due_date' in data and data['due_date'].strip(): hw_to_update.due_date = data['due_date'].strip()
        if 'description' in data: hw_to_update.description = data.get('description', '').strip() or None
        # defined_date معمولا در ویرایش تغییر نمی‌کند
        
        db.session.commit()
        return jsonify({
            "id": hw_to_update.id, "title": hw_to_update.title, "subject": hw_to_update.subject,
            "defined_date": hw_to_update.defined_date, "due_date": hw_to_update.due_date,
            "description": hw_to_update.description,
            "message": "تکلیف با موفقیت به‌روزرسانی شد."
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در به‌روزرسانی تکلیف {homework_id}: {e}")
        return jsonify(message="خطا در به‌روزرسانی تکلیف", error=str(e)), 500

@main_bp.route('/api/homeworks/<int:homework_id>', methods=['DELETE'])
def delete_homework(homework_id):
    try:
        hw_to_delete = Homework.query.get(homework_id)
        if not hw_to_delete: return jsonify(message="تکلیف با این شناسه یافت نشد."), 404
        db.session.delete(hw_to_delete) # Cascade delete باید HomeworkStatus های مرتبط را حذف کند
        db.session.commit()
        return jsonify(message=f"تکلیف '{hw_to_delete.title}' با موفقیت حذف شد."), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در حذف تکلیف {homework_id}: {e}")
        return jsonify(message="خطا در حذف تکلیف", error=str(e)), 500

# --- API Endpoints برای وضعیت تکالیف دانش‌آموزان (HomeworkStatus) ---
@main_bp.route('/api/homeworks/<int:homework_id>/statuses', methods=['GET'])
def get_homework_statuses(homework_id):
    try:
        homework = Homework.query.get(homework_id)
        if not homework: return jsonify(message="تکلیف با این شناسه یافت نشد."), 404
        statuses_from_db = homework.statuses.all()
        statuses_list = [{
            "id": status_entry.id, "homework_id": status_entry.homework_id,
            "student_id": status_entry.student_id,
            "student_name": f"{status_entry.student.first_name} {status_entry.student.last_name}",
            "status": status_entry.status, "submission_notes": status_entry.submission_notes
        } for status_entry in statuses_from_db]
        return jsonify(statuses_list)
    except Exception as e:
        print(f"خطا در دریافت وضعیت تکالیف برای تکلیف {homework_id}: {e}")
        return jsonify(message="خطا در دریافت وضعیت تکالیف", error=str(e)), 500

@main_bp.route('/api/homeworks/<int:homework_id>/statuses', methods=['POST'])
def set_homework_statuses(homework_id):
    try:
        homework = Homework.query.get(homework_id)
        if not homework: return jsonify(message="تکلیف با این شناسه یافت نشد."), 404
        statuses_data = request.get_json()
        if not isinstance(statuses_data, list): return jsonify(message="داده‌های ارسالی باید یک لیست از وضعیت‌ها باشند."), 400
        
        updated_count = 0
        created_count = 0
        for status_item in statuses_data:
            student_id = status_item.get('student_id')
            new_status = status_item.get('status')
            notes = status_item.get('submission_notes', '')
            if not student_id or not new_status: continue 
            student = Student.query.get(student_id)
            if not student: continue
            existing_status = HomeworkStatus.query.filter_by(homework_id=homework_id, student_id=student_id).first()
            if existing_status:
                existing_status.status = new_status
                existing_status.submission_notes = notes
                updated_count += 1
            else:
                new_status_entry = HomeworkStatus(homework_id=homework_id, student_id=student_id, status=new_status, submission_notes=notes)
                db.session.add(new_status_entry)
                created_count +=1
        db.session.commit()
        return jsonify(message=f"وضعیت تکالیف ثبت شد. {created_count} جدید، {updated_count} به‌روز."), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در ثبت وضعیت تکالیف برای {homework_id}: {e}")
        return jsonify(message="خطا در ثبت وضعیت تکالیف", error=str(e)), 500

# --- API Endpoints برای غیبت‌ها (Attendance) ---
@main_bp.route('/api/attendance', methods=['POST'])
def record_attendance():
    try:
        data = request.get_json()
        if not data or 'date_str' not in data: return jsonify(message="فیلد 'date_str' ضروری است."), 400
        date_str = data['date_str']
        absent_students_info = data.get('absent_students', [])
        Attendance.query.filter_by(date_str=date_str).delete()
        newly_recorded_absences = 0
        for student_info in absent_students_info:
            student_id = student_info.get('student_id')
            reason = student_info.get('reason', '').strip() or None
            if not student_id: continue
            student = Student.query.get(student_id)
            if not student: continue
            new_absence = Attendance(student_id=student_id, date_str=date_str, reason=reason)
            db.session.add(new_absence)
            newly_recorded_absences += 1
        db.session.commit()
        return jsonify(message=f"اطلاعات حضور و غیاب برای تاریخ {date_str} ثبت شد. {newly_recorded_absences} غیبت ثبت گردید."), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در ثبت اطلاعات حضور و غیاب: {e}")
        return jsonify(message="خطا در ثبت اطلاعات حضور و غیاب", error=str(e)), 500

@main_bp.route('/api/attendance', methods=['GET'])
def get_attendance_records():
    try:
        date_str = request.args.get('date_str')
        student_id = request.args.get('student_id', type=int)
        if not date_str and not student_id: return jsonify(message="حداقل 'date_str' یا 'student_id' مورد نیاز است."), 400
        query = Attendance.query
        if date_str: query = query.filter_by(date_str=date_str)
        if student_id: query = query.filter_by(student_id=student_id)
        attendance_records_from_db = query.order_by(Attendance.student_id).all()
        records_list = [{
            "id": record.id, "student_id": record.student_id,
            "student_name": f"{record.student.first_name} {record.student.last_name}",
            "date_str": record.date_str, "reason": record.reason
        } for record in attendance_records_from_db]
        return jsonify(records_list)
    except Exception as e:
        print(f"خطا در دریافت سوابق حضور و غیاب: {e}")
        return jsonify(message="خطا در دریافت سوابق حضور و غیاب", error=str(e)), 500

# --- API Endpoints برای لاگ عملکرد روزانه دانش آموزان (DailyPerformanceLog) ---
@main_bp.route('/api/performance_logs', methods=['POST'])
def add_performance_log():
    try:
        data = request.get_json()
        if not data: return jsonify(message="داده‌ای ارسال نشده است."), 400
        required_fields = ['student_id', 'date_str', 'log_text']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify(message=f"فیلد '{field}' ضروری است."), 400
        student = Student.query.get(data['student_id'])
        if not student: return jsonify(message=f"دانش‌آموزی با شناسه '{data['student_id']}' یافت نشد."), 404
        new_log = DailyPerformanceLog(student_id=data['student_id'], date_str=data['date_str'], log_text=data['log_text'])
        db.session.add(new_log)
        db.session.commit()
        return jsonify({
            "id": new_log.id, "student_id": new_log.student_id,
            "student_name": f"{new_log.student.first_name} {new_log.student.last_name}",
            "date_str": new_log.date_str, "log_text": new_log.log_text,
            "created_at": new_log.created_at.isoformat(),
            "message": "لاگ عملکرد با موفقیت ثبت شد."
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"خطا در افزودن لاگ عملکرد: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(message="خطا در ثبت لاگ عملکرد", error=str(e)), 500

@main_bp.route('/api/performance_logs', methods=['GET'])
def get_performance_logs():
    try:
        student_id = request.args.get('student_id', type=int)
        date_str = request.args.get('date_str')
        query = DailyPerformanceLog.query
        if student_id: query = query.filter_by(student_id=student_id)
        if date_str: query = query.filter_by(date_str=date_str)
        logs_from_db = query.order_by(DailyPerformanceLog.created_at.desc(), DailyPerformanceLog.student_id).all()
        logs_list = [{
            "id": log_entry.id, "student_id": log_entry.student_id,
            "student_name": f"{log_entry.student.first_name} {log_entry.student.last_name}",
            "date_str": log_entry.date_str, "log_text": log_entry.log_text,
            "created_at": log_entry.created_at.isoformat()
        } for log_entry in logs_from_db]
        return jsonify(logs_list)
    except Exception as e:
        print(f"خطا در دریافت لاگ‌های عملکرد: {e}")
        return jsonify(message="خطا در دریافت لاگ‌های عملکرد", error=str(e)), 500

@main_bp.route('/api/performance_logs/<int:log_id>', methods=['PUT'])
def update_performance_log(log_id):
    try:
        log_to_update = DailyPerformanceLog.query.get(log_id)
        if not log_to_update: return jsonify(message="لاگ عملکرد با این شناسه یافت نشد."), 404
        data = request.get_json()
        if not data: return jsonify(message="داده‌ای برای به‌روزرسانی ارسال نشده است."), 400
        if 'log_text' in data and data['log_text'].strip():
            log_to_update.log_text = data['log_text'].strip()
        else:
            return jsonify(message="فیلد 'log_text' برای به‌روزرسانی ضروری است."), 400
        db.session.commit()
        return jsonify({
            "id": log_to_update.id, "student_id": log_to_update.student_id,
            "student_name": f"{log_to_update.student.first_name} {log_to_update.student.last_name}",
            "date_str": log_to_update.date_str, "log_text": log_to_update.log_text,
            "created_at": log_to_update.created_at.isoformat(),
            "message": "لاگ عملکرد با موفقیت به‌روزرسانی شد."
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در به‌روزرسانی لاگ عملکرد {log_id}: {e}")
        return jsonify(message="خطا در به‌روزرسانی لاگ عملکرد", error=str(e)), 500

@main_bp.route('/api/performance_logs/<int:log_id>', methods=['DELETE'])
def delete_performance_log(log_id):
    try:
        log_to_delete = DailyPerformanceLog.query.get(log_id)
        if not log_to_delete: return jsonify(message="لاگ عملکرد با این شناسه یافت نشد."), 404
        db.session.delete(log_to_delete)
        db.session.commit()
        return jsonify(message=f"لاگ عملکرد با شناسه {log_id} با موفقیت حذف شد."), 200
    except Exception as e:
        db.session.rollback()
        print(f"خطا در حذف لاگ عملکرد {log_id}: {e}")
        return jsonify(message="خطا در حذف لاگ عملکرد", error=str(e)), 500

# --- API Endpoint برای گزارش دانش‌آموز ---
@main_bp.route('/api/reports/student/<int:student_id>', methods=['GET'])
def get_student_report(student_id):
    try:
        student = Student.query.get(student_id)
        if not student: return jsonify(message="دانش‌آموز با این شناسه یافت نشد."), 404
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        report_data = {
            "student_info": {"id": student.id, "first_name": student.first_name, "last_name": student.last_name, "student_class": student.student_class},
            "date_range": {"start": start_date_str or "ابتدا", "end": end_date_str or "انتها"},
            "grades_summary": [], "homework_summary": [],
            "attendance_summary": {"total_absences": 0, "absences": []},
            "daily_performance_logs": []
        }

        # نمرات
        grades_query = Grade.query.filter_by(student_id=student.id)
        if start_date_str: grades_query = grades_query.filter(Grade.date_str >= start_date_str)
        if end_date_str: grades_query = grades_query.filter(Grade.date_str <= end_date_str)
        student_grades = grades_query.order_by(Grade.subject, Grade.date_str).all()
        grades_by_subject = {}
        for grade in student_grades:
            if grade.subject not in grades_by_subject: grades_by_subject[grade.subject] = []
            grades_by_subject[grade.subject].append({
                "date_str": grade.date_str, "performance": grade.performance, # با فرض مدل ساده Grade
                "reason": grade.reason
            })
        for subject, entries in grades_by_subject.items():
             report_data["grades_summary"].append({"subject": subject, "entries": entries})

        # تکالیف
        homework_statuses_query = HomeworkStatus.query.filter_by(student_id=student.id)
        if start_date_str or end_date_str:
            homework_statuses_query = homework_statuses_query.join(Homework, Homework.id == HomeworkStatus.homework_id)
            if start_date_str: homework_statuses_query = homework_statuses_query.filter(Homework.due_date >= start_date_str)
            if end_date_str: homework_statuses_query = homework_statuses_query.filter(Homework.due_date <= end_date_str)
        student_homework_statuses = homework_statuses_query.order_by(Homework.due_date).all()
        for hs in student_homework_statuses:
            if hs.homework_details:
                report_data["homework_summary"].append({
                    "homework_title": hs.homework_details.title, "due_date": hs.homework_details.due_date,
                    "status": hs.status, "submission_notes": hs.submission_notes
                })
        
        # غیبت‌ها
        attendance_query = Attendance.query.filter_by(student_id=student.id)
        if start_date_str: attendance_query = attendance_query.filter(Attendance.date_str >= start_date_str)
        if end_date_str: attendance_query = attendance_query.filter(Attendance.date_str <= end_date_str)
        student_absences = attendance_query.order_by(Attendance.date_str).all()
        report_data["attendance_summary"]["total_absences"] = len(student_absences)
        for absence in student_absences:
            report_data["attendance_summary"]["absences"].append({"date_str": absence.date_str, "reason": absence.reason})

        # لاگ‌های عملکرد روزانه
        performance_log_query = DailyPerformanceLog.query.filter_by(student_id=student.id)
        if start_date_str: performance_log_query = performance_log_query.filter(DailyPerformanceLog.date_str >= start_date_str)
        if end_date_str: performance_log_query = performance_log_query.filter(DailyPerformanceLog.date_str <= end_date_str)
        student_performance_logs = performance_log_query.order_by(DailyPerformanceLog.date_str.desc(), DailyPerformanceLog.created_at.desc()).all()
        for log_entry in student_performance_logs:
            report_data["daily_performance_logs"].append({
                "id": log_entry.id, "date_str": log_entry.date_str,
                "log_text": log_entry.log_text, "created_at": log_entry.created_at.isoformat()
            })

        return jsonify(report_data), 200
    except Exception as e:
        print(f"خطا در تولید گزارش برای دانش‌آموز {student_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(message="خطا در تولید گزارش", error=str(e)), 500
