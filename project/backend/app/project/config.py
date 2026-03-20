import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///beach.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    TIME_INTERVALS = ['08:00-12:00', '12:00-16:00', '16:00-20:00']
    
    MANAGER_USERNAME = os.environ.get('MANAGER_USERNAME', 'manager')
    MANAGER_PASSWORD = os.environ.get('MANAGER_PASSWORD', '12345')
    MANAGER_EMAIL = os.environ.get('MANAGER_EMAIL', 'manager@beach.com')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
