#!/usr/bin/env python
"""Database initialization script using SQLModel"""

import os
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from app.models import (
    User, RefreshToken, Case, Snapshot, Member, Event, 
    Scenario, Delegation, AuditLog
)
from app.config import settings

def init_db():
    """Initialize database with SQLModel metadata"""
    db_url: str = settings.database_url or f"sqlite:///{settings.db_path}"
    print(f"Initializing database at: {db_url}")

    # Create engine
    engine = create_engine(db_url, echo=False)
    
    # Create all tables
    print("Creating tables...")
    SQLModel.metadata.create_all(engine)
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\nSuccess! Created {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    return tables

if __name__ == "__main__":
    tables = init_db()
    if tables:
        print("\n✓ Database initialization complete!")
    else:
        print("\n✗ No tables were created!")
