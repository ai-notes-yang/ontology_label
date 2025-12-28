import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 检查是否在Vercel环境中
IS_VERCEL = os.environ.get('VERCEL') == '1'

# Supabase数据库配置（从环境变量读取）
SUPABASE_DB_URL = os.environ.get('DATABASE_URL')

class Config:
    # 优先使用Supabase数据库URL，否则使用本地SQLite
    if SUPABASE_DB_URL:
        # Supabase使用PostgreSQL
        # 注意：如果URL以postgres://开头，需要改为postgresql://
        if SUPABASE_DB_URL.startswith('postgres://'):
            SQLALCHEMY_DATABASE_URI = SUPABASE_DB_URL.replace('postgres://', 'postgresql://', 1)
        else:
            SQLALCHEMY_DATABASE_URI = SUPABASE_DB_URL
    elif IS_VERCEL:
        # Vercel环境没有配置数据库URL时使用内存数据库（仅用于测试）
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    else:
        # 本地开发使用SQLite
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "ontology_review.db")}'
    
    # Vercel环境使用/tmp目录
    if IS_VERCEL:
        UPLOAD_FOLDER = '/tmp/uploads'
        LOG_FILE = '/tmp/logs/app.log'
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
        LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # 检查连接是否有效
        'pool_recycle': 300,    # 5分钟后回收连接
    }
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
