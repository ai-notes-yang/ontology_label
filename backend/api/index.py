# Vercel serverless function entry point
import sys
import os

# 将backend目录添加到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# 导入Flask应用
from app import app

# 导出app供Vercel使用
app = app

