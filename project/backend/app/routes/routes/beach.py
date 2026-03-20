from flask import Blueprint, render_template_string, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import BeachZone, Duty, Visitor, User
from datetime import datetime, date
from functools import wraps

bp = Blueprint('beach', __name__, url_prefix='/beach')

def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_manager():
            flash('Доступ запрещен. Требуются права менеджера.', 'error')
            return redirect(url_for('beach.dashboard'))
        return f(*args, **kwargs)
    return decorated

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Панель управления</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 20px; }
        .header a { color: white; text-decoration: none; margin-left: 15px; }
        .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; flex: 1; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-card .number { font-size: 32px; font-weight: bold; color: #2c3e50; }
        .menu { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .menu h2 { margin-bottom: 15px; color: #2c3e50; }
        .menu-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .menu-item { background: #3498db; color: white; padding: 15px; text-align: center; border-radius: 8px; text-decoration: none; transition: 0.3s; }
        .menu-item:hover { background: #2980b9; transform: translateY(-2px); }
        .flash { padding: 10px; margin-bottom: 20px; border-radius: 5px; }
        .flash.error { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
        .flash.success { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        button, .btn { background: #3498db; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-danger { background: #e74c3c; }
        .btn-success { background: #27ae60; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏖️ Пляжный учет</h1>
        <div>
            <span>👤 {{ username }} ({{ role }})</span>
            <a href="{{ url_for('auth.logout') }}">Выход</a>
        </div>
    </div>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        
        <div class="stats">
            <div class="stat-card"><h3>👥 Сотрудников</h3><div class="number">{{ stats.employees }}</div></div>
            <div class="stat-card"><h3>🗺️ Зон</h3><div class="number">{{ stats.zones }}</div></div>
            <div class="stat-card"><h3>📅 Сегодня дежурств</h3><div class="number">{{ stats.today_duties }}</div></div>
            <div class="stat-card"><h3>👤 Посетителей сегодня</h3><div class="number">{{ stats.today_visitors }}</div></div>
        </div>
        
        <div class="menu">
            <h2>📋 Меню</h2>
            <div class="menu-grid">
                {% if is_manager %}
                <a href="{{ url_for('beach.users_list') }}" class="menu-item">👥 Управление сотрудниками</a>
                <a href="{{ url_for('beach.zones_list') }}" class="menu-item">🗺️ Пляжные зоны</a>
                <a href="{{ url_for('beach.assign_duty') }}" class="menu-item">📅 Назначить дежурство</a>
                <a href="{{ url_for('reports.report') }}" class="menu-item">📊 Отчеты</a>
                {% else %}
                <a href="{{ url_for('beach.add_visitor') }}" class="menu-item">➕ Добавить посетителя</a>
                <a href="{{ url_for('beach.my_duties') }}" class="menu-item">📅 Мои дежурства</a>
                <a href="{{ url_for('beach.visitors_list') }}" class="menu-item">📋 Список посетителей</a>
                {% endif %}
            </div>
        </div>
        
        {% if not is_manager and today_duties %}
        <div class="menu" style="margin-top: 20px;">
            <h2>📌 Ваши дежурства на сегодня</h2>
            <table>
                <tr><th>Время</th><th>Зона</th></tr>
                {% for duty in today_duties %}
                <tr><td>{{ duty.time_interval }}</td><td>{{ duty.zone.name }}</td></tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@bp.route('/')
@login_required
def dashboard():
    stats = {
        'employees': User.query.filter_by(role='employee', is_approved=True).count(),
        'zones': BeachZone.query.count(),
        'today_duties': Duty.query.filter_by(duty_date=date.today()).count(),
        'today_visitors': Visitor.query.filter(db.func.date(Visitor.arrival_time) == date.today()).count()
    }
    
    today_duties = []
    if not current_user.is_manager():
        today_duties = Duty.query.filter_by(user_id=current_user.id, duty_date=date.today()).all()
    
    return render_template_string(DASHBOARD_TEMPLATE,
        username=current_user.username,
        role='Менеджер' if current_user.is_manager() else 'Сотрудник',
        is_manager=current_user.is_manager(),
        stats=stats,
        today_duties=today_duties)

@bp.route('/users')
@login_required
@manager_required
def users_list():
    pending = User.query.filter_by(is_approved=False, role='employee').all()
    approved = User.query.filter_by(is_approved=True, role='employee').all()
    
    template = '''
    <!DOCTYPE html>
    <html>
    <head><title>Сотрудники</title><style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; }
        .header { background: #2c3e50; color: white; padding: 15px 20px; }
        .header a { color: white; text-decoration: none; margin-right: 15px; }
        .container { max-width: 1000px; margin: 20px auto; padding: 20px; background: white; border-radius: 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        .btn { padding: 5px 10px; border-radius: 5px; text-decoration: none; color: white; }
        .btn-success { background: #27ae60; }
        .btn-danger { background: #e74c3c; }
    </style></head>
    <body>
        <div class="header"><a href="/beach">← Назад</a> <span>Управление сотрудниками</span></div>
        <div class="container">
            <h2>👥 Ожидают подтверждения</h2>
            <table><tr><th>ID</th><th>Имя</th><th>Email</th><th>Действие</th></tr>
            {% for u in pending %}
            <tr><td>{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.email }}</td><td><a href="/beach/users/approve/{{ u.id }}" class="btn btn-success">Подтвердить</a></td></tr>
            {% else %}<tr><td colspan="4">Нет ожидающих</td></tr>{% endfor %}
            </table>
            <h2>✅ Активные сотрудники</h2>
            <table><tr><th>ID</th><th>Имя</th><th>Email</th><th>Действие</th></tr>
            {% for u in approved %}
            <tr><td>{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.email }}</td><td><a href="/beach/users/delete/{{ u.id }}" class="btn btn-danger" onclick="return confirm('Удалить?')">Удалить</a></td></tr>
            {% endfor %}
            </table>
        </div>
    </body>
    </html>
    '''
    return render_template_string(template, pending=pending, approved=approved)

@bp.route('/users/approve/<int:user_id>')
@login_required
@manager_required
def approve_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_approved = True
        db.session.commit()
        flash(f'Сотрудник {user.username} подтвержден', 'success')
    return redirect(url_for('beach.users_list'))

@bp.route('/users/delete/<int:user_id>')
@login_required
@manager_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user and user.id != current_user.id:
        db.session.delete(user)
        db.session.commit()
        flash('Сотрудник удален', 'success')
    return redirect(url_for('beach.users_list'))

@bp.route('/zones', methods=['GET', 'POST'])
@login_required
@manager_required
def zones_list():
    if request.method == 'POST':
        zone = BeachZone(
            name=request.form['name'],
            center_lat=float(request.form.get('lat', 55.751244)),
            center_lng=float(request.form.get('lng', 37.618423))
        )
        db.session.add(zone)
        db.session.commit()
        flash('Зона добавлена', 'success')
    
    zones = BeachZone.query.all()
    template = '''
    <!DOCTYPE html>
    <html>
    <head><title>Пляжные зоны</title><style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; }
        .header { background: #2c3e50; color: white; padding: 15px 20px; }
        .header a { color: white; text-decoration: none; margin-right: 15px; }
        .container { max-width: 800px; margin: 20px auto; padding: 20px; background: white; border-radius: 10px; }
        input, select { padding: 8px; margin: 5px 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #27ae60; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        .btn-danger { background: #e74c3c; padding: 5px 10px; border-radius: 5px; text-decoration: none; color: white; font-size: 12px; }
    </style></head>
    <body>
        <div class="header"><a href="/beach">← Назад</a> <span>Пляжные зоны</span></div>
        <div class="container">
            <h2>➕ Добавить зону</h2>
            <form method="post">
                <input type="text" name="name" placeholder="Название зоны" required>
                <input type="text" name="lat" placeholder="Широта" value="55.751244">
                <input type="text" name="lng" placeholder="Долгота" value="37.618423">
                <button type="submit">Добавить</button>
            </form>
            <h2>🗺️ Список зон</h2>
            <table><tr><th>ID</th><th>Название</th><th>Координаты</th><th></th></tr>
            {% for z in zones %}
            <tr><td>{{ z.id }}</td><td>{{ z.name }}</td><td>{{ z.center_lat }}, {{ z.center_lng }}</td><td><a href="/beach/zones/delete/{{ z.id }}" class="btn-danger" onclick="return confirm('Удалить?')">Удалить</a></td></tr>
            {% endfor %}
            </table>
        </div>
    </body>
    </html>
    '''
    return render_template_string(template, zones=zones)

@bp.route('/zones/delete/<int:zone_id>')
@login_required
@manager_required
def delete_zone(zone_id):
    zone = BeachZone.query.get(zone_id)
    if zone:
        db.session.delete(zone)
        db.session.commit()
        flash('Зона удалена', 'success')
    return redirect(url_for('beach.zones_list'))

@bp.route('/duties/assign', methods=['GET', 'POST'])
@login_required
@manager_required
def assign_duty():
    employees = User.query.filter_by(role='employee', is_approved=True).all()
    zones = BeachZone.query.all()
    duties = Duty.query.order_by(Duty.duty_date.desc()).all()
    
    if request.method == 'POST':
        duty = Duty(
            user_id=request.form['user_id'],
            zone_id=request.form['zone_id'],
            duty_date=datetime.strptime(request.form['duty_date'], '%Y-%m-%d').date(),
            time_interval=request.form['time_interval']
        )
        db.session.add(duty)
        db.session.commit()
        flash('Дежурство назначено', 'success')
        return redirect(url_for('beach.assign_duty'))
    
    template = '''
    <!DOCTYPE html>
    <html>
    <head><title>Назначение дежурств</title><style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; }
        .header { background: #2c3e50; color: white; padding: 15px 20px; }
        .header a { color: white; text-decoration: none; margin-right: 15px; }
        .container { max-width: 1000px; margin: 20px auto; padding: 20px; background: white; border-radius: 10px; }
        form { background: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        select, input { padding: 8px; margin: 5px 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #27ae60; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
    </style></head>
    <body>
        <div class="header"><a href="/beach">← Назад</a> <span>Назначение дежурств</span></div>
        <div class="container">
            <h2>📅 Назначить дежурство</h2>
            <form method="post">
                <select name="user_id" required><option value="">Сотрудник</option>{% for e in employees %}<option value="{{ e.id }}">{{ e.username }}</option>{% endfor %}</select>
                <select name="zone_id" required><option value="">Зона</option>{% for z in zones %}<option value="{{ z.id }}">{{ z.name }}</option>{% endfor %}</select>
                <input type="date" name="duty_date" required>
                <select name="time_interval" required><option value="08:00-12:00">08:00-12:00</option><option value="12:00-16:00">12:00-16:00</option><option value="16:00-20:00">16:00-20:00</option></select>
                <button type="submit">Назначить</button>
            </form>
            <h2>📋 Список дежурств</h2>
            <table><tr><th>Дата</th><th>Сотрудник</th><th>Зона</th><th>Время</th></tr>
            {% for d in duties %}<tr><td>{{ d.duty_date }}</td><td>{{ d.employee.username }}</td><td>{{ d.zone.name }}</td><td>{{ d.time_interval }}</td></tr>{% endfor %}
            </table>
        </div>
    </body>
    </html>
    '''
    return render_template_string(template, employees=employees, zones=zones, duties=duties)

@bp.route('/visitors/add', methods=['GET', 'POST'])
@login_required
def add_visitor():
    if current_user.is_manager():
        zones = BeachZone.query.all()
    else:
        zones = BeachZone.query.all()
    
    if request.method == 'POST':
        visitor = Visitor(
            zone_id=request.form['zone_id'],
            used_sunbed='used_sunbed' in request.form,
            used_float='used_float' in request.form,
            used_mattress='used_mattress' in request.form
        )
        db.session.add(visitor)
        db.session.commit()
        flash('Посетитель добавлен', 'success')
        return redirect(url_for('beach.add_visitor'))
    
    recent = Visitor.query.order_by(Visitor.arrival_time.desc()).limit(10).all()
    
    template = '''
    <!DOCTYPE html>
    <html>
    <head><title>Добавить посетителя</title><style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; }
        .header { background: #2c3e50; color: white; padding: 15px 20px; }
        .header a { color: white; text-decoration: none; margin-right: 15px; }
        .container { max-width: 600px; margin: 20px auto; padding: 20px; background: white; border-radius: 10px; }
        select, input { padding: 8px; margin: 5px 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; }
        .checkbox-group { display: flex; gap: 15px; margin: 10px 0; }
        .checkbox-group label { display: flex; align-items: center; gap: 5px; }
        button { background: #27ae60; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
    </style></head>
    <body>
        <div class="header"><a href="/beach">← Назад</a> <span>Добавить посетителя</span></div>
        <div class="container">
            <h2>➕ Новый посетитель</h2>
            <form method="post">
                <select name="zone_id" required><option value="">Выберите зону</option>{% for z in zones %}<option value="{{ z.id }}">{{ z.name }}</option>{% endfor %}</select>
                <div class="checkbox-group">
                    <label><input type="checkbox" name="used_sunbed"> 🪑 Шезлонг (Ш)</label>
                    <label><input type="checkbox" name="used_float"> 🏊 Плавсредства (П)</label>
                    <label><input type="checkbox" name="used_mattress"> 🛟 Матрас (М)</label>
                </div>
                <button type="submit">Добавить</button>
            </form>
            <h3>📋 Последние посетители</h3>
            <table><tr><th>Время</th><th>Зона</th><th>Ш</th><th>П</th><th>М</th></tr>
            {% for v in recent %}<tr><td>{{ v.arrival_time.strftime('%H:%M') }}</td><td>{{ v.zone.name }}</td><td>{% if v.used_sunbed %}✅{% else %}❌{% endif %}</td><td>{% if v.used_float %}✅{% else %}❌{% endif %}</td><td>{% if v.used_mattress %}✅{% else %}❌{% endif %}</td></tr>{% endfor %}
            </table>
        </div>
    </body>
    </html>
    '''
    return render_template_string(template, zones=zones, recent=recent)

@bp.route('/visitors')
@login_required
def visitors_list():
    visitors = Visitor.query.order_by(Visitor.arrival_time.desc()).limit(50).all()
    template = '''
    <!DOCTYPE html>
    <html>
    <head><title>Посетители</title><style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; }
        .header { background: #2c3e50; color: white;
