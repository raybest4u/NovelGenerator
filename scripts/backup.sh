
# scripts/backup.sh
#!/bin/bash
# 数据备份脚本

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="fantasy_novel_backup_${TIMESTAMP}.tar.gz"

echo "开始备份数据..."

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据文件
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    --exclude="*.log" \
    --exclude="__pycache__" \
    --exclude=".git" \
    data/ \
    config/ \
    *.db 2>/dev/null || true

echo "✅ 备份完成: ${BACKUP_DIR}/${BACKUP_FILE}"

# 清理旧备份（保留最近10个）
cd $BACKUP_DIR
ls -t fantasy_novel_backup_*.tar.gz | tail -n +11 | xargs -r rm --

echo "备份文件清理完成"
