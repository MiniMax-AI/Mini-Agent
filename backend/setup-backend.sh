#!/bin/bash
# 后端快速安装脚本（推荐方式）

set -e

echo "🚀 Mini-Agent 后端快速安装"
echo "================================"
echo ""

# 检查是否在正确的目录
if [ ! -f "../pyproject.toml" ]; then
    echo "❌ 错误：请从 backend/ 目录运行此脚本"
    echo "   cd Mini-Agent/backend && ./setup-backend.sh"
    exit 1
fi

cd ..

echo "📦 步骤 1: 安装 mini_agent + 后端依赖"
echo "   运行: pip install -e '.[backend]'"
echo ""

# 安装包（可编辑模式）+ 后端依赖
pip install -e ".[backend]"

echo ""
echo "✅ mini_agent 和后端依赖已安装！"
echo ""

# 返回 backend 目录
cd backend

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "📝 步骤 2: 创建 .env 配置文件"
    cp .env.example .env
    echo "   ✅ 已从 .env.example 复制"
    echo "   ⚠️  请编辑 .env 文件，填入你的 API Keys"
    echo ""
else
    echo "✅ .env 文件已存在"
    echo ""
fi

echo "================================"
echo "🎉 安装完成！"
echo ""
echo "下一步："
echo "  1. 编辑 backend/.env 文件，填入 API Keys"
echo "  2. 运行诊断: python diagnose.py"
echo "  3. 启动后端: uvicorn app.main:app --reload"
echo ""
echo "现在可以运行诊断脚本："
echo "  python diagnose.py"
echo ""
