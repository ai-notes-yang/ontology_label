import logging
import os
from datetime import datetime

def setup_logger():
    """设置日志记录器"""
    # 创建logger
    logger = logging.getLogger('ontology_review')
    logger.setLevel(logging.DEBUG)
    
    # 检查是否在Vercel环境中
    is_vercel = os.environ.get('VERCEL') == '1'
    
    # 创建控制台handler（总是需要）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加handler到logger
    if not logger.handlers:  # 避免重复添加handler
        logger.addHandler(console_handler)
        
        # 只在非Vercel环境下添加文件handler
        if not is_vercel:
            try:
                from config import Config
                log_dir = os.path.dirname(Config.LOG_FILE)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"无法创建文件日志: {e}")
    
    return logger

# 全局logger实例
logger = setup_logger()
