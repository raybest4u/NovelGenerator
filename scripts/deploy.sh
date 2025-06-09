
# scripts/deploy.sh
#!/bin/bash
# 部署脚本

set -e

echo "开始部署 Fantasy Novel MCP..."

# 检查环境变量
if [ -z "$LLM_API_KEY" ]; then
    echo "错误: 请设置 LLM_API_KEY 环境变量"
    exit 1
fi

# 拉取最新代码
echo "拉取最新代码..."
git pull origin main

# 构建Docker镜像
echo "构建Docker镜像..."
docker-compose build

# 停止旧容器
echo "停止旧服务..."
docker-compose down

# 启动新容器
echo "启动新服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 健康检查
echo "进行健康检查..."
if curl -f http://localhost:8080/health; then
    echo "✅ 部署成功！服务运行正常"
else
    echo "❌ 部署失败！服务健康检查未通过"
    docker-compose logs fantasy-novel-mcp
    exit 1
fi

echo "🎉 部署完成！"
echo "访问地址: http://localhost:8080"
echo "API文档: http://localhost:8080/docs"

