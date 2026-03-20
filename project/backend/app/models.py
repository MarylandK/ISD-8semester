from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Пользователь системы (сотрудник или менеджер)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default='employee')  # 'employee' or 'manager'
    is_approved = db.Column(db.Boolean, default=False)
    google_calendar_id = db.Column(db.String(255))
    google_credentials = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    duties = db.relationship('Duty', backref='employee', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'


class BeachZone(db.Model):
    """Пляжная зона"""
    __tablename__ = 'beach_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    polygon_data = db.Column(db.JSON)  # Координаты полигона
    center_lat = db.Column(db.Float)
    center_lng = db.Column(db.Float)
    color = db.Column(db.String(20), default='#FF0000')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    duties = db.relationship('Duty', backref='zone', lazy=True)
    visitors = db.relationship('Visitor', backref='zone', lazy=True)
    
    def __repr__(self):
        return f'<BeachZone {self.name}>'


class Duty(db.Model):
    """Дежурство сотрудника"""
    __tablename__ = 'duties'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('beach_zones.id'), nullable=False)
    duty_date = db.Column(db.Date, nullable=False)
    time_interval = db.Column(db.String(20), nullable=False)  # '08:00-12:00', etc.
    calendar_event_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'duty_date', 'time_interval', name='unique_duty'),
    )
    
    def __repr__(self):
        return f'<Duty {self.user_id} - {self.duty_date} {self.time_interval}>'


class Visitor(db.Model):
    """Посетитель пляжа"""
    __tablename__ = 'visitors'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('beach_zones.id'), nullable=False)
    duty_id = db.Column(db.Integer, db.ForeignKey('duties.id'), nullable=True)
    arrival_time = db.Column(db.DateTime, nullable=False)
    departure_time = db.Column(db.DateTime)
    used_sunbed = db.Column(db.Boolean, default=False)   # Ш - шезлонг
    used_float = db.Column(db.Boolean, default=False)    # П - плавсредства
    used_mattress = db.Column(db.Boolean, default=False) # М - матрас
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    duty = db.relationship('Duty', backref='visitors')
    
    def __repr__(self):
        return f'<Visitor {self.id} - {self.arrival_time}>'


class Report(db.Model):
    """Отчет по наблюдениям"""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('beach_zones.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    report_data = db.Column(db.JSON)
    google_doc_link = db.Column(db.String(500))
    
    zone = db.relationship('BeachZone')
    generator = db.relationship('User')
    
    def __repr__(self):
        return f'<Report {self.id} - {self.start_date} to {self.end_date}>'
