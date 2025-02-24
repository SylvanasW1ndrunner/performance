import os

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:123456@172.22.0.43:5432/performance'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'super-secret-key-keep-it-safe!')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时有效期

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True