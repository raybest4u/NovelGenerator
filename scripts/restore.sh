
# scripts/restore.sh
#!/bin/bash
# 数据恢复脚本

set -e

if [ $# -eq 0 ]; then
    echo "用法: $0 <backup_file>"
    echo "可用备份文件:"
    ls -1 backups/fantasy_novel_backup_*.tar.gz 2>/dev/null || echo "无可用备份文件"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "从备份恢复数据: $BACKUP_FILE"

# 确认操作
read -p "这将覆盖现有数据，确定要继续吗？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 1
fi

# 停止服务
echo "停止服务..."
docker-compose down 2>/dev/null || true

# 备份当前数据
if [ -d "data" ]; then
    echo "备份当前数据..."
    mv data data.backup.$(date +"%Y%m%d_%H%M%S")
fi

# 恢复数据
echo "恢复数据..."
tar -xzf "$BACKUP_FILE"

echo "✅ 数据恢复完成"

# 重启服务
echo "重启服务..."
docker-compose up -d

echo "🎉 恢复操作完成！"
