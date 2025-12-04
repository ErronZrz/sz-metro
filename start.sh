#!/bin/bash

echo "🚇 深圳地铁寻路游戏 - 启动脚本"
echo "================================"
echo ""

# Check if backend dependencies are installed
echo "📦 检查后端依赖..."
cd backend
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  后端依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

# Start backend
echo "🚀 启动后端服务 (端口 8000)..."
uvicorn app.main:app --reload &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

cd ..

# Check if frontend dependencies are installed
echo ""
echo "📦 检查前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "⚠️  前端依赖未安装，正在安装..."
    npm install
fi

# Start frontend
echo "🚀 启动前端服务 (端口 5173)..."
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

echo ""
echo "================================"
echo "✨ 应用已启动！"
echo "📱 前端地址: http://localhost:5173"
echo "🔧 后端地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "================================"

cd ..

# Wait for Ctrl+C
trap "echo ''; echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
