from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Создаем менеджера по умолчанию
        if not User.query.filter_by(username=app.config['MANAGER_USERNAME']).first():
            manager = User(
                username=app.config['MANAGER_USERNAME'],
                email=app.config['MANAGER_EMAIL'],
                password_hash=generate_password_hash(app.config['MANAGER_PASSWORD']),
                role='manager',
                is_approved=True
            )
            db.session.add(manager)
            db.session.commit()
            print(f"✅ Менеджер создан: {app.config['MANAGER_USERNAME']} / {app.config['MANAGER_PASSWORD']}")
    
    print("\n🏖️ Сервер запущен!")
    print(f"📌 http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
