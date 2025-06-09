
# scripts/dev-setup.sh
#!/bin/bash
# 开发环境设置脚本

set -e

echo "设置 Fantasy Novel MCP 开发环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "错误: 需要Python 3.9+，当前版本: $python_version"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 创建必要目录
echo "创建目录结构..."
mkdir -p data/generated data/templates data/references logs

# 复制环境变量示例
if [ ! -f .env ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置您的LLM API信息"
fi

# 初始化数据库
echo "初始化数据库..."
python -c "from data.models import init_database; init_database()"

# 安装git hooks
echo "安装Git hooks..."
pre-commit install

# 运行测试
echo "运行测试..."
python -m pytest tests/ -v

echo "✅ 开发环境设置完成！"
echo ""
echo "下一步:"
echo "1. 编辑 .env 文件配置LLM API"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 启动开发服务器: python main.py server --debug"
echo "4. 访问 http://localhost:8080"

