#!/bin/bash

# 本体数据标注平台启动脚本

echo "======================================"
echo "   本体数据标注平台 启动脚本"
echo "======================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装后端依赖..."
pip install -r requirements.txt -q

# 创建必要的目录
mkdir -p backend/uploads
mkdir -p backend/logs
mkdir -p backend/data

# 启动后端服务
echo "启动后端服务 (端口: 5001)..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 2

# 检查Node环境
if ! command -v node &> /dev/null; then
    echo "警告: 未找到Node.js，跳过前端启动"
    echo "后端服务已启动，访问 http://localhost:5001"
    echo "按 Ctrl+C 停止服务"
    wait $BACKEND_PID
    exit 0
fi

# 安装前端依赖并启动
echo "安装前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi

echo "启动前端服务 (端口: 3000)..."
npm start &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "   服务启动成功！"
echo "======================================"
echo "后端地址: http://localhost:5001"
echo "前端地址: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "======================================"

# 捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait

