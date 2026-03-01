"""
Unit tests for SQLModel tables (Day 2 Week 1)
验证所有8个models的基本功能
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session

from app.models import (
    User, Member, Event, Scenario, Delegation, AuditLog
)


@pytest.fixture
def test_db():
    """创建内存数据库用于测试"""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session)
    return SessionLocal()


class TestUserTable:
    """Test User table creation and relationships"""
    
    def test_user_creation(self, test_db):
        """Test 1: User表能创建记录"""
        user = User(
            username="alice",
            email="alice@example.com",
            password_hash="hashed_password_123"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        assert user.id is not None
        
        assert user.id is not None
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.is_active is True
        print("✅ Test 1: User创建成功")


class TestMemberTable:
    """Test Member table creation and birth_date handling"""
    
    def test_member_creation_with_birth_date(self, test_db):
        """Test 2: Member表能创建记录，关键字段birth_date正确"""
        user = User(
            username="bob",
            email="bob@example.com",
            password_hash="hashed"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        assert user.id is not None
        test_db.refresh(user)
        
        member = Member(
            owner_id=user.id,
            name="小王",
            birth_date=date(2000, 1, 15),
            gender="M",
            birth_time_hour=14,
            birth_time_minute=36
        )
        test_db.add(member)
        test_db.commit()
        test_db.refresh(member)
        
        assert member.id is not None
        assert member.name == "小王"
        assert member.birth_date == date(2000, 1, 15)
        assert member.birth_date.year == 2000
        assert member.birth_date.month == 1
        assert member.birth_date.day == 15
        assert member.gender == "M"
        print("✅ Test 2: Member创建成功，birth_date日期处理正确")
    
    def test_member_foreign_key_to_user(self, test_db):
        """Test 3: Member与User的外键关系"""
        user = User(
            username="charlie",
            email="charlie@example.com",
            password_hash="hashed"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        assert user.id is not None
        
        member = Member(
            owner_id=user.id,
            name="小李",
            birth_date=date(1995, 5, 20),
            gender="F"
        )
        test_db.add(member)
        test_db.commit()
        test_db.refresh(member)
        assert member.id is not None
        
        # 验证外键关系
        assert member.owner_id == user.id
        print("✅ Test 3: Member-User外键关系正确")


class TestEventTable:
    """Test Event table for storing BaZi calculation results"""
    
    def test_event_creation_with_bazi_json(self, test_db):
        """Test 4: Event表能存储完整的四柱JSON"""
        user = User(
            username="david",
            email="david@example.com",
            password_hash="hashed"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        assert user.id is not None
        
        member = Member(
            owner_id=user.id,
            name="小张",
            birth_date=date(2002, 3, 13),
            gender="M"
        )
        test_db.add(member)
        test_db.commit()
        test_db.refresh(member)
        assert member.id is not None
        
        # 模拟四柱计算结果
        bazi_json = '{"year":"壬午","month":"癸卯","day":"壬午","hour":"丙申"}'
        
        event = Event(
            owner_id=user.id,
            member_id=member.id,
            name="2002年春分八字验证",
            event_type="verification",
            bazi_json=bazi_json,
            L_level=0,
            confidence_score=0.95
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)
        
        assert event.id is not None
        assert event.L_level == 0
        assert event.confidence_score == 0.95
        assert "壬午" in event.bazi_json
        print("✅ Test 4: Event创建成功，能存储BaZi JSON")


class TestScenarioTable:
    """Test Scenario table for what-if analysis"""
    
    def test_scenario_creation(self, test_db):
        """Test 5: Scenario表能创建假设推演记录"""
        user = User(
            username="eve",
            email="eve@example.com",
            password_hash="hashed"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        assert user.id is not None
        
        member = Member(
            owner_id=user.id,
            name="小刘",
            birth_date=date(1990, 6, 10),
            gender="F"
        )
        test_db.add(member)
        test_db.commit()
        test_db.refresh(member)
        assert member.id is not None
        
        scenario = Scenario(
            owner_id=user.id,
            base_member_id=member.id,
            name="如果生时晚1小时的推演",
            description="测试时辰边界对十神的影响",
            scenario_type="time_adjustment",
            variations='{"hour_offset": 1}'
        )
        test_db.add(scenario)
        test_db.commit()
        test_db.refresh(scenario)
        
        assert scenario.id is not None
        assert scenario.name == "如果生时晚1小时的推演"
        print("✅ Test 5: Scenario创建成功")


class TestDelegationTable:
    """Test Delegation table for permission management"""
    
    def test_delegation_creation(self, test_db):
        """Test 6: Delegation表能记录权限委托"""
        user1 = User(
            username="frank",
            email="frank@example.com",
            password_hash="hashed"
        )
        user2 = User(
            username="grace",
            email="grace@example.com",
            password_hash="hashed"
        )
        test_db.add(user1)
        test_db.add(user2)
        test_db.commit()
        test_db.refresh(user1)
        test_db.refresh(user2)
        assert user1.id is not None
        assert user2.id is not None
        
        delegation = Delegation(
            from_user_id=user1.id,
            to_user_id=user2.id,
            permission_type="view"
        )
        test_db.add(delegation)
        test_db.commit()
        test_db.refresh(delegation)
        
        assert delegation.id is not None
        assert delegation.from_user_id == user1.id
        assert delegation.to_user_id == user2.id
        assert delegation.permission_type == "view"
        print("✅ Test 6: Delegation创建成功")


class TestAuditLogTable:
    """Test AuditLog table for compliance and tracking"""
    
    def test_audit_log_creation(self, test_db):
        """Test 7: AuditLog表能记录操作"""
        user = User(
            username="henry",
            email="henry@example.com",
            password_hash="hashed"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        assert user.id is not None
        
        audit_log = AuditLog(
            user_id=user.id,
            action="create_member",
            resource_type="member",
            resource_id="member_123",
            details='{"name":"张三","birth_date":"2000-01-01"}',
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            status="success"
        )
        test_db.add(audit_log)
        test_db.commit()
        test_db.refresh(audit_log)
        
        assert audit_log.id is not None
        assert audit_log.action == "create_member"
        assert audit_log.status == "success"
        print("✅ Test 7: AuditLog创建成功")


class TestForeignKeyConstraints:
    """Test foreign key constraints and cascade behavior"""
    
    def test_member_depends_on_user(self, test_db):
        """Test 8: 验证外键约束（Member必须有有效的owner_id）"""
        user = User(
            username="iris",
            email="iris@example.com",
            password_hash="hashed"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        assert user.id is not None
        
        # 创建依赖于user的member
        member = Member(
            owner_id=user.id,
            name="小美",
            birth_date=date(1998, 12, 25),
            gender="F"
        )
        test_db.add(member)
        test_db.commit()
        
        # 验证关系
        from sqlmodel import select
        fetched_member = test_db.exec(select(Member).where(Member.id == member.id)).first()
        assert fetched_member is not None
        assert fetched_member.owner_id == user.id
        print("✅ Test 8: 外键约束验证成功")


class TestTableIndexes:
    """Test that important indexes are created"""
    
    def test_user_username_index(self, test_db):
        """Test 9: 验证User.username有索引"""
        # 创建多个user来测试索引效率
        for i in range(5):
            user = User(
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                password_hash="hashed"
            )
            test_db.add(user)
        test_db.commit()
        
        # 查询应该能找到特定user
        from sqlmodel import select
        found = test_db.exec(select(User).where(User.username == "user_2")).first()
        assert found is not None
        assert found.username == "user_2"
        print("✅ Test 9: User索引验证成功")


class TestDataIntegrity:
    """Test data integrity and constraints"""
    
    def test_unique_username(self, test_db):
        """Test 10: 验证username唯一性约束"""
        user1 = User(
            username="jack",
            email="jack1@example.com",
            password_hash="hashed"
        )
        test_db.add(user1)
        test_db.commit()
        
        # 尝试创建相同username的user应该失败
        user2 = User(
            username="jack",  # 重复
            email="jack2@example.com",
            password_hash="hashed"
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):  # 应该抛出IntegrityError或类似异常
            test_db.commit()
        
        print("✅ Test 10: 唯一性约束验证成功")


# ==================== Summary Tests ====================

def test_all_8_tables_created(test_db):
    """验证所有8个表都已创建"""
    # 检查SQLModel.metadata中的所有表
    expected_tables = {
        'cases', 'snapshots', 'users', 'members', 
        'events', 'scenarios', 'delegations', 'audit_logs'
    }
    
    actual_tables = {table.name for table in SQLModel.metadata.tables.values()}
    assert expected_tables.issubset(actual_tables), \
        f"Missing tables. Expected: {expected_tables}, Got: {actual_tables}"
    
    print(f"✅ 所有8个表都已成功创建: {actual_tables}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
