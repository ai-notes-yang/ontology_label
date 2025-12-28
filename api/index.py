# Vercel serverless function entry point
import sys
import os

# 将backend目录添加到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 导入Flask应用
from app import app

# Vercel需要这个handler
def handler(request):
    return app(request.environ, request.start_response)

# 也需要导出app本身
app = app

