from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import threading

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

_engine = None
_engine_lock = threading.Lock()


def _ensure_data_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_engine():
    """
    获取数据库引擎（线程安全单例模式）

    支持 SQLite（开发）和 PostgreSQL（生产）。
    配置从 app.config.settings 获取。
    """
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                if settings.use_postgres:
                    # PostgreSQL 生产配置（带连接池优化）
                    _pg_url: str = settings.database_url  # type: ignore[assignment]  # use_postgres guarantees str
                    _engine = create_engine(
                        _pg_url,
                        pool_size=settings.db_pool_size,
                        max_overflow=settings.db_max_overflow,
                        pool_pre_ping=True,
                        pool_recycle=settings.db_pool_recycle,
                        echo=settings.debug,
                    )
                else:
                    # SQLite 开发配置
                    _ensure_data_dir(settings.db_path)
                    _engine = create_engine(
                        f"sqlite:///{settings.db_path}", connect_args={"check_same_thread": False}, echo=settings.debug
                    )

                    # 开启 WAL 模式＋外键约束（必须在 engine 创建后立即设置）
                    @event.listens_for(_engine, "connect")
                    def _set_sqlite_pragmas(dbapi_conn, connection_record):  # type: ignore
                        cursor = dbapi_conn.cursor()
                        cursor.execute("PRAGMA journal_mode=WAL")  # 高并发读写不冲突
                        cursor.execute("PRAGMA foreign_keys=ON")  # 开启外键约束
                        cursor.execute("PRAGMA synchronous=NORMAL")  # WAL+NORMAL 是安全且性能最佳平衡
                        cursor.close()

    return _engine


def init_db() -> None:
    """初始化数据库 - 导入所有模型并创建表"""
    from app.models import AuditLog, Case, Delegation, Event, Member, RefreshToken, Scenario, Snapshot, User

    # 确保所有SQLModel类都已注册
    _ = (User, RefreshToken, Case, Snapshot, Member, Event, Scenario, Delegation, AuditLog)

    engine = get_engine()
    SQLModel.metadata.create_all(engine)

    # SQLite 兼容：直接补充 snapshots.deleted_at 列（老库升级用）
    # 已通过 Alembic 迁移管理，此处仅保留 SELECT-free 的 ADD COLUMN 兼容逻辑
    if not settings.use_postgres:
        with engine.connect() as conn:
            cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(snapshots);")]
            if "deleted_at" not in cols:
                conn.exec_driver_sql("ALTER TABLE snapshots ADD COLUMN deleted_at TIMESTAMP;")


def get_session() -> Generator[Session, None, None]:
    engine = get_engine()
    with Session(engine) as session:
        yield session
