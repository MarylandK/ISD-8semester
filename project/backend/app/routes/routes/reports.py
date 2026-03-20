from flask import Blueprint, render_template_string, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import BeachZone, Duty, Visitor, Report
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('reports', __name__, url_prefix='/reports')

REPORT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Отчеты</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; }
        .header { background: #2c3e50; color: white; padding: 15px 20px; }
        .header a { color: white; text-decoration: none; margin-right: 15px; }
        .container { max-width: 1200px; margin: 20px auto; padding: 20px; background: white; border-radius: 10px; }
        form { background: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        select, input { padding: 8px; margin: 5px 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #27ae60; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background: #3498db; color: white; }
        .interval-header { background: #2980b9; }
        h3 { color: #2c3e50; margin-top: 20px; }
        .btn { background: #3498db; padding: 8px 15px; border-radius: 5px; text-decoration: none; color: white; display: inline-block; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header"><a href="/beach">← Назад</a> <span>Формирование отчетов</span></div>
    <div class="container">
        <h2>📊 Формирование отчета по посетителям</h2>
        
        {% if report_data %}
        <h3>Отчет по зоне: {{ zone_name }}</h3>
        <p><strong>Период:</strong> {{ start_date }} - {{ end_date }}</p>
        <p><strong>Дата формирования:</strong> {{ generated_at }}</p>
        
        <table>
            <tr>
                <th rowspan="2">Дата</th>
                <th colspan="3">08:00-12:00</th>
                <th colspan="3">12:00-16:00</th>
                <th colspan="3">16:00-20:00</th>
            </tr>
            <tr>
                <th>Ш</th><th>П</th><th>М</th>
                <th>Ш</th><th>П</th><th>М</th>
                <th>Ш</th><th>П</th><th>М</th>
            </tr>
            {% for day in report_data %}
            <tr>
                <td><b>{{ day.date }}</b></td>
                {% for interval in intervals %}
                <td>{{ day.intervals[interval]['sunbed'] }}</td>
                <td>{{ day.intervals[interval]['float'] }}</td>
                <td>{{ day.intervals[interval]['mattress'] }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>
        
        <a href="{{ url_for('reports.report') }}" class="btn">Сформировать новый отчет</a>
        {% else %}
        <form method="post">
            <select name="zone_id" required>
                <option value="">Выберите пляжную зону</option>
                {% for zone in zones %}
                <option value="{{ zone.id }}">{{ zone.name }}</option>
                {% endfor %}
            </select>
            <input type="date" name="start_date" required>
            <input type="date" name="end_date" required>
            <button type="submit">Сформировать отчет</button>
        </form>
        {% endif %}
        
        <h3 style="margin-top: 30px;">📜 Сохраненные отчеты</h3>
        <table style="margin-top: 10px;">
            <tr><th>ID</th><th>Зона</th><th>Период</th><th>Дата создания</th><th></th></tr>
            {% for report in saved_reports %}
            <tr>
                <td>{{ report.id }}</td>
                <td>{{ report.zone.name }}</td>
                <td>{{ report.start_date }} - {{ report.end_date }}</td>
                <td>{{ report.generated_at.strftime('%d.%m.%Y %H:%M') }}</td>
                <td><a href="{{ url_for('reports.view_report', report_id=report.id) }}" style="color: #27ae60;">Просмотреть</a></td>
            </tr>
            {% else %}
            <tr><td colspan="5">Нет сохраненных отчетов</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

@bp.route('/', methods=['GET', 'POST'])
@login_required
def report():
    zones = BeachZone.query.all()
    saved_reports = Report.query.filter_by(generated_by=current_user.id).order_by(Report.generated_at.desc()).all()
    
    if request.method == 'POST':
        zone_id = int(request.form['zone_id'])
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        zone = BeachZone.query.get(zone_id)
        intervals = current_app.config['TIME_INTERVALS']
        
        duties = Duty.query.filter(
            Duty.zone_id == zone_id,
            Duty.duty_date >= start_date,
            Duty.duty_date <= end_date
        ).all()
        
        report_data = []
        current_date = start_date
        
        while current_date <= end_date:
            day_data = {'date': current_date.strftime('%d.%m.%Y'), 'intervals': {}}
            
            for interval in intervals:
                duty = next((d for d in duties if d.duty_date == current_date and d.time_interval == interval), None)
                
                if duty:
                    sunbed = Visitor.query.filter_by(duty_id=duty.id, used_sunbed=True).count()
                    float_cnt = Visitor.query.filter_by(duty_id=duty.id, used_float=True).count()
                    mattress = Visitor.query.filter_by(duty_id=duty.id, used_mattress=True).count()
                    
                    day_data['intervals'][interval] = {
                        'sunbed': sunbed,
                        'float': float_cnt,
                        'mattress': mattress
                    }
                else:
                    day_data['intervals'][interval] = {'sunbed': 0, 'float': 0, 'mattress': 0}
            
            report_data.append(day_data)
            current_date += timedelta(days=1)
        
        # Сохраняем отчет в базу
        saved_report = Report(
            zone_id=zone_id,
            start_date=start_date,
            end_date=end_date,
            generated_by=current_user.id,
            report_data=report_data
        )
        db.session.add(saved_report)
        db.session.commit()
        
        return render_template_string(REPORT_TEMPLATE,
            report_data=report_data,
            zone_name=zone.name,
            start_date=start_date.strftime('%d.%m.%Y'),
            end_date=end_date.strftime('%d.%m.%Y'),
            generated_at=datetime.now().strftime('%d.%m.%Y %H:%M'),
            intervals=intervals,
            zones=zones,
            saved_reports=Report.query.filter_by(generated_by=current_user.id).order_by(Report.generated_at.desc()).all())
    
    return render_template_string(REPORT_TEMPLATE, zones=zones, saved_reports=saved_reports, report_data=None)

@bp.route('/view/<int:report_id>')
@login_required
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    
    if report.generated_by != current_user.id and not current_user.is_manager():
        return "Доступ запрещен", 403
    
    intervals = current_app.config['TIME_INTERVALS']
    zones = BeachZone.query.all()
    saved_reports = Report.query.filter_by(generated_by=current_user.id).order_by(Report.generated_at.desc()).all()
    
    return render_template_string(REPORT_TEMPLATE,
        report_data=report.report_data,
        zone_name=report.zone.name,
        start_date=report.start_date.strftime('%d.%m.%Y'),
        end_date=report.end_date.strftime('%d.%m.%Y'),
        generated_at=report.generated_at.strftime('%d.%m.%Y %H:%M'),
        intervals=intervals,
        zones=zones,
        saved_reports=saved_reports)
