
# Makefile
# 项目管理Makefile

.PHONY: help install dev test lint format clean build deploy backup

# 默认目标
help:
	@echo "Fantasy Novel MCP - 可用命令:"
	@echo "  install     - 安装依赖"
	@echo "  dev         - 启动开发环境"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo "  build       - 构建Docker镜像"
	@echo "  deploy      - 部署到生产环境"
	@echo "  backup      - 备份数据"

# 安装依赖
install:
	pip install -r requirements.txt

# 安装开发依赖
install-dev:
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

# 启动开发服务器
dev:
	python main.py server --debug

# 运行测试
test:
	python -m pytest tests/ -v --cov=fantasy_novel_mcp

# 代码检查
lint:
	flake8 --max-line-length=100 .
	mypy --ignore-missing-imports .

# 代码格式化
format:
	black --line-length=100 .
	isort .

# 清理临时文件
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/

# 构建Docker镜像
build:
	docker-compose build

# 部署到生产环境
deploy:
	./scripts/deploy.sh

# 启动开发环境
up-dev:
	docker-compose -f docker-compose.dev.yml up -d

# 停止服务
down:
	docker-compose down

# 查看日志
logs:
	docker-compose logs -f fantasy-novel-mcp

# 备份数据
backup:
	./scripts/backup.sh

# 初始化数据库
init-db:
	python -c "from data.models import init_database; init_database()"

# 生成示例小说
demo:
	python main.py generate --title "仙路征途" --genre "玄幻" --chapters 5 --theme "修仙"
