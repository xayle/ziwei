#!/usr/bin/env bash
# scripts/backup_db.sh — BaZi API v7.0 数据库备份脚本 (M0 任务 0.34)
#
# 用途: 每日 cron 备份 data/mingli.db
# 建议 crontab: 0 2 * * * /path/to/scripts/backup_db.sh >> /var/log/bazi_backup.log 2>&1
#
set -euo pipefail

# --- 配置 ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DB_PATH="${DB_PATH:-$PROJECT_DIR/data/mingli.db}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/data/backups}"
RETAIN_DAYS="${RETAIN_DAYS:-30}"  # 保留最近30天备份

# --- 检查数据库文件 ---
if [ ! -f "$DB_PATH" ]; then
    echo "[$(date -Iseconds)] ERROR: DB not found at $DB_PATH" >&2
    exit 1
fi

# --- 创建备份目录 ---
mkdir -p "$BACKUP_DIR"

# --- 生成备份文件名 ---
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$BACKUP_DIR/mingli_${TIMESTAMP}.db"
BACKUP_WAL="$BACKUP_FILE.wal"

# --- 使用 SQLite .backup 命令（安全热备份，不锁定业务） ---
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
echo "[$(date -Iseconds)] INFO: Backup created: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# --- 清理过期备份 ---
find "$BACKUP_DIR" -name "mingli_*.db" -mtime "+$RETAIN_DAYS" -exec rm -f {} \;
echo "[$(date -Iseconds)] INFO: Cleaned backups older than $RETAIN_DAYS days"

# --- 统计 ---
COUNT=$(find "$BACKUP_DIR" -name "mingli_*.db" | wc -l)
echo "[$(date -Iseconds)] INFO: Total backup files retained: $COUNT"
