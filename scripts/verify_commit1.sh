#!/bin/bash
# Commit 1 验证脚本
# 验证Docker化基础设施是否正常工作

set -e

echo "=== Commit 1 验证: Docker化基础设施 ==="
echo ""

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon未运行。请先启动Docker Desktop。"
    exit 1
fi
echo "✓ Docker daemon运行中"

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "⚠️  .env文件不存在，从.env.example创建..."
    cp .env.example .env
    echo "✓ .env文件已创建（请编辑设置SECRET_KEY等配置）"
else
    echo "✓ .env文件存在"
fi

# 检查SECRET_KEY是否设置
if grep -q "SECRET_KEY=change-this" .env 2>/dev/null; then
    echo "⚠️  SECRET_KEY使用默认值，建议生成随机密钥"
    echo "   运行: python3 -c \"import secrets; print('SECRET_KEY=' + secrets.token_hex(32))\""
fi

# 构建Docker镜像
echo ""
echo "构建Docker镜像..."
docker compose build web > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Docker镜像构建成功"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi

# 启动服务（后台运行）
echo ""
echo "启动服务..."
docker compose up -d > /dev/null 2>&1

# 等待服务就绪
echo "等待服务就绪（最多30秒）..."
for i in {1..30}; do
    if curl -s http://localhost:5000/ > /dev/null 2>&1; then
        echo "✓ Web服务已就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Web服务启动超时"
        docker compose logs web | tail -20
        exit 1
    fi
    sleep 1
done

# 验证端点
echo ""
echo "验证端点..."

# 首页
if curl -s http://localhost:5000/ | grep -q "EduFeedback"; then
    echo "✓ 首页可访问"
else
    echo "❌ 首页访问失败"
    exit 1
fi

# API端点
if curl -s http://localhost:5000/api/users | grep -q "teachers\|students\|\[\]"; then
    echo "✓ /api/users端点正常"
else
    echo "❌ /api/users端点失败"
    exit 1
fi

# 演示数据初始化
if curl -s -X POST http://localhost:5000/api/demo/init | grep -q "successfully"; then
    echo "✓ /api/demo/init端点正常"
else
    echo "❌ /api/demo/init端点失败"
    exit 1
fi

# 教师和学生页面
if curl -s http://localhost:5000/teacher | grep -q "teacher\|Instructor"; then
    echo "✓ /teacher页面可访问"
else
    echo "❌ /teacher页面失败"
    exit 1
fi

if curl -s http://localhost:5000/student | grep -q "student\|Student"; then
    echo "✓ /student页面可访问"
else
    echo "❌ /student页面失败"
    exit 1
fi

echo ""
echo "=== ✅ Commit 1 验证通过 ==="
echo ""
echo "服务运行中，可以访问:"
echo "  - http://localhost:5000/"
echo "  - http://localhost:5000/teacher"
echo "  - http://localhost:5000/student"
echo ""
echo "查看日志: docker compose logs -f"
echo "停止服务: docker compose down"
