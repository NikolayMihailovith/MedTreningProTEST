from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os

# --- Настройка приложения ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'medtraining-secret-key-2024'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# --- Модели базы данных ---
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    hire_date = db.Column(db.DateTime, default=datetime.utcnow)
    termination_date = db.Column(db.DateTime, nullable=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    duration_hours = db.Column(db.Integer)
    passing_score = db.Column(db.Integer, default=70)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='completed')


# --- Маршруты ---
@app.route('/')
def index():
    emp_count = Employee.query.filter_by(is_active=True).count()
    training_count = Training.query.count()
    course_count = Course.query.filter_by(is_active=True).count()
    avg_score = db.session.query(db.func.avg(Training.score)).scalar()

    return render_template('index.html',
                           emp_count=emp_count,
                           training_count=training_count,
                           course_count=course_count,
                           avg_score=round(avg_score, 1) if avg_score else 0)


@app.route('/employees')
def employees():
    all_employees = Employee.query.order_by(Employee.is_active.desc(), Employee.name).all()
    return render_template('employees.html', employees=all_employees)


@app.route('/add_employee', methods=['POST'])
def add_employee():
    name = request.form['name']
    position = request.form['position']
    dept = request.form['department']
    email = request.form['email']

    new_emp = Employee(
        name=name,
        position=position,
        department=dept,
        email=email,
        is_active=True,
        hire_date=datetime.utcnow()
    )
    db.session.add(new_emp)
    db.session.commit()
    flash(f'Сотрудник {name} успешно добавлен!', 'success')
    return redirect(url_for('employees'))


@app.route('/edit_employee/<int:id>', methods=['POST'])
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    employee.name = request.form['name']
    employee.position = request.form['position']
    employee.department = request.form['department']
    employee.email = request.form['email']
    db.session.commit()
    flash(f'Данные сотрудника {employee.name} обновлены!', 'info')
    return redirect(url_for('employees'))


@app.route('/toggle_employee_status/<int:id>', methods=['POST'])
def toggle_employee_status(id):
    employee = Employee.query.get_or_404(id)
    employee.is_active = not employee.is_active
    if not employee.is_active:
        employee.termination_date = datetime.utcnow()
    else:
        employee.termination_date = None
    db.session.commit()
    flash(f'Статус сотрудника {employee.name} изменен', 'info')
    return redirect(url_for('employees'))


@app.route('/delete_employee/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    name = employee.name
    Training.query.filter_by(employee_id=id).delete()
    db.session.delete(employee)
    db.session.commit()
    flash(f'Сотрудник {name} удален', 'danger')
    return redirect(url_for('employees'))


# --- Управление курсами ---
@app.route('/courses')
def courses():
    all_courses = Course.query.order_by(Course.is_active.desc(), Course.category, Course.title).all()
    return render_template('courses_management.html', courses=all_courses)


@app.route('/add_course', methods=['POST'])
def add_course():
    title = request.form['title']
    description = request.form.get('description', '')
    category = request.form.get('category', '')
    duration_hours = int(request.form['duration_hours']) if request.form.get('duration_hours') else None
    passing_score = int(request.form['passing_score'])

    new_course = Course(
        title=title,
        description=description,
        category=category,
        duration_hours=duration_hours,
        passing_score=passing_score,
        is_active=True
    )
    db.session.add(new_course)
    db.session.commit()
    flash(f'Курс "{title}" добавлен!', 'success')
    return redirect(url_for('courses'))


@app.route('/edit_course/<int:id>', methods=['POST'])
def edit_course(id):
    course = Course.query.get_or_404(id)
    course.title = request.form['title']
    course.description = request.form.get('description', '')
    course.category = request.form.get('category', '')
    course.duration_hours = int(request.form['duration_hours']) if request.form.get('duration_hours') else None
    course.passing_score = int(request.form['passing_score'])
    db.session.commit()
    flash(f'Курс "{course.title}" обновлён!', 'info')
    return redirect(url_for('courses'))


@app.route('/toggle_course_status/<int:id>', methods=['POST'])
def toggle_course_status(id):
    course = Course.query.get_or_404(id)
    course.is_active = not course.is_active
    db.session.commit()
    status = "активирован" if course.is_active else "архивирован"
    flash(f'Курс "{course.title}" {status}', 'info')
    return redirect(url_for('courses'))


@app.route('/delete_course/<int:id>', methods=['POST'])
def delete_course(id):
    course = Course.query.get_or_404(id)
    title = course.title
    # Проверяем, есть ли связанные тренинги
    if Training.query.filter_by(course_id=id).count() > 0:
        flash(f'Нельзя удалить курс "{title}" — есть связанные тренинги', 'warning')
    else:
        db.session.delete(course)
        db.session.commit()
        flash(f'Курс "{title}" удалён', 'danger')
    return redirect(url_for('courses'))


@app.route('/trainings')
def trainings():
    all_trainings = db.session.query(Training, Employee, Course) \
        .join(Employee, Training.employee_id == Employee.id) \
        .outerjoin(Course, Training.course_id == Course.id) \
        .filter(Employee.is_active == True) \
        .order_by(Training.date_taken.desc()) \
        .all()

    employees = Employee.query.filter_by(is_active=True).all()
    active_courses = Course.query.filter_by(is_active=True).all()

    return render_template('trainings.html',
                           trainings=all_trainings,
                           employees=employees,
                           courses=active_courses)


@app.route('/add_training', methods=['POST'])
def add_training():
    emp_id = request.form['employee_id']
    course_id = request.form.get('course_id')
    score = int(request.form['score'])

    if course_id:
        course = db.session.get(Course, course_id)
        title = course.title
        passing_score = course.passing_score
    else:
        title = "Без названия"
        passing_score = 70

    new_training = Training(
        title=title,
        course_id=course_id if course_id else None,
        employee_id=emp_id,
        score=score,
        status='completed' if score >= passing_score else 'failed'
    )
    db.session.add(new_training)
    db.session.commit()
    flash('Результат тренинга сохранен!', 'success')
    return redirect(url_for('trainings'))


@app.route('/analytics')
def analytics():
    query = db.session.query(
        Employee.name,
        Employee.department,
        Training.title,
        Training.score
    ).join(Training, Employee.id == Training.employee_id) \
        .filter(Employee.is_active == True) \
        .all()

    if not query:
        return render_template('analytics.html', tables=[], titles=[], has_data=False)

    df = pd.DataFrame(query, columns=['Сотрудник', 'Отделение', 'Курс', 'Баллы'])

    dept_stats = df.groupby('Отделение')['Баллы'].mean().round(1).reset_index()
    dept_stats.columns = ['Отделение', 'Средний балл']
    dept_stats = dept_stats.sort_values('Средний балл', ascending=False)

    df['Сдал'] = df['Баллы'] >= 70
    course_pass_rate = df.groupby('Курс')['Сдал'].mean() * 100
    course_pass_rate = course_pass_rate.round(1).reset_index()
    course_pass_rate.columns = ['Курс', 'Процент сдачи']
    course_pass_rate = course_pass_rate.sort_values('Процент сдачи', ascending=False)

    top_employees = df.groupby('Сотрудник')['Баллы'].agg(['mean', 'count']).round(1)
    top_employees.columns = ['Средний балл', 'Кол-во курсов']
    top_employees = top_employees[top_employees['Кол-во курсов'] >= 1].sort_values('Средний балл',
                                                                                   ascending=False).head(5)
    top_employees = top_employees.reset_index()

    dept_html = dept_stats.to_html(classes='table table-striped table-hover', index=False)
    course_html = course_pass_rate.to_html(classes='table table-bordered table-hover', index=False)
    top_html = top_employees.to_html(classes='table table-striped', index=False)

    tables = [dept_html, course_html, top_html]
    titles = ['Средний балл по отделениям', 'Успеваемость по курсам', 'Топ-5 сотрудников']

    return render_template('analytics.html', tables=tables, titles=titles, has_data=True)


# --- Инициализация базы данных ---
def init_db():
    """Создает таблицы и тестовые данные, если база пустая"""
    db.create_all()

    # Проверяем, есть ли уже данные
    if Course.query.count() == 0:
        print("📝 Добавляем тестовые курсы...")
        courses = [
            Course(title="Базовая СЛР (BLS)",
                   description="Базовые навыки сердечно-легочной реанимации",
                   category="Неотложная помощь", duration_hours=8, passing_score=70),
            Course(title="Радиационная безопасность",
                   description="Правила работы с источниками ионизирующего излучения",
                   category="Безопасность", duration_hours=4, passing_score=80),
            Course(title="ЭКГ диагностика",
                   description="Основы интерпретации электрокардиограмм",
                   category="Диагностика", duration_hours=12, passing_score=70),
            Course(title="Инфекционная безопасность",
                   description="Профилактика внутрибольничных инфекций",
                   category="Безопасность", duration_hours=6, passing_score=75),
        ]
        for course in courses:
            db.session.add(course)
        db.session.commit()
        print(f"✅ Добавлено {len(courses)} курсов")

    if Employee.query.count() == 0:
        print("📝 Добавляем тестовых сотрудников...")
        employees = [
            Employee(name="Иван Петров", position="Врач-рентгенолог",
                     department="Лучевая диагностика", email="i.petrov@mtp.ru", is_active=True),
            Employee(name="Анна Сидорова", position="Медсестра",
                     department="Хирургия", email="a.sidorova@mtp.ru", is_active=True),
            Employee(name="Петр Иванов", position="Врач",
                     department="Кардиология", email="p.ivanov@mtp.ru", is_active=True),
            Employee(name="Мария Козлова", position="Старшая медсестра",
                     department="Терапия", email="m.kozlova@mtp.ru", is_active=True),
        ]
        for emp in employees:
            db.session.add(emp)
        db.session.commit()
        print(f"✅ Добавлено {len(employees)} сотрудников")

    if Training.query.count() == 0 and Course.query.count() > 0 and Employee.query.count() > 0:
        print("📝 Добавляем тестовые тренинги...")
        trainings = [
            Training(title="Базовая СЛР (BLS)", course_id=1, employee_id=1, score=85, status='completed'),
            Training(title="Радиационная безопасность", course_id=2, employee_id=1, score=95, status='completed'),
            Training(title="Базовая СЛР (BLS)", course_id=1, employee_id=2, score=65, status='failed'),
            Training(title="ЭКГ диагностика", course_id=3, employee_id=3, score=90, status='completed'),
            Training(title="Инфекционная безопасность", course_id=4, employee_id=4, score=78, status='completed'),
            Training(title="Базовая СЛР (BLS)", course_id=1, employee_id=4, score=92, status='completed'),
        ]
        for train in trainings:
            db.session.add(train)
        db.session.commit()
        print(f"✅ Добавлено {len(trainings)} тренингов")


# --- Запуск ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)