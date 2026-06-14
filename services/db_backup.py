"""
services/db_backup.py — O1: SQLite 定时备份服务

功能：
  - backup_sqlite_db(): 使用 VACUUM INTO 热备份（不锁表）
  - 保留最近 keep 份，自动清理旧备份
  - schedule_backup(): 注册到 APScheduler，每日 03:00 触发

调用方式（run.py lifespan startup）：
    from services.db_backup import schedule_backup
    scheduler = schedule_backup()
    yield
    scheduler.shutdown(wait=False)
"""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

# 默认配置
_DEFAULT_DB_PATH = Path("mingli.db")
_DEFAULT_BACKUP_DIR = Path("data/backups")
_DEFAULT_KEEP = 7


def backup_sqlite_db(
    src: Path = _DEFAULT_DB_PATH,
    dest_dir: Path = _DEFAULT_BACKUP_DIR,
    keep: int = _DEFAULT_KEEP,
) -> Path:
    """执行一次 SQLite 热备份（VACUUM INTO，不锁表）。

    Args:
        src:      源数据库文件路径
        dest_dir: 备份目录（自动创建）
        keep:     保留最近 keep 份，旧文件自动删除

    Returns:
        备份文件路径
    """
    if not src.exists():
        logger.warning("[O1-BACKUP] 数据库文件不存在，跳过备份: %s", src)
        return src

    dest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"mingli_{ts}.db"

    try:
        conn = sqlite3.connect(str(src))
        conn.execute("VACUUM INTO ?", (str(dest),))
        conn.close()
        size_kb = dest.stat().st_size // 1024
        logger.info("[O1-BACKUP] 备份成功: %s (%d KB)", dest.name, size_kb)
    except Exception as exc:
        logger.error("[O1-BACKUP] 备份失败: %s", exc)
        raise

    # 清理旧备份，保留最近 keep 份
    old_files = sorted(dest_dir.glob("mingli_*.db"))[:-keep]
    for f in old_files:
        try:
            f.unlink()
            logger.debug("[O1-BACKUP] 清理旧备份: %s", f.name)
        except Exception:
            pass

    return dest


def schedule_backup(
    src: Path = _DEFAULT_DB_PATH,
    dest_dir: Path = _DEFAULT_BACKUP_DIR,
    keep: int = _DEFAULT_KEEP,
    hour: int = 3,
    minute: int = 0,
):
    """向 APScheduler BackgroundScheduler 注册每日备份任务并启动。

    Returns:
        scheduler 实例（调用方在 shutdown 时调用 scheduler.shutdown(wait=False)）
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    except ImportError:
        logger.warning("[O1-BACKUP] APScheduler 未安装，跳过定时备份注册")
        return None

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        backup_sqlite_db,
        trigger="cron",
        hour=hour,
        minute=minute,
        kwargs={"src": src, "dest_dir": dest_dir, "keep": keep},
        id="daily_db_backup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[O1-BACKUP] 定时备份已注册，每日 %02d:%02d 执行", hour, minute)
    return scheduler
