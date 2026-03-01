"""
查询优化 - N+1 问题消除和关系预加载
"""
import logging
from typing import List, Type, TypeVar, Optional, Any
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RelationshipLoader:
    """关系加载优化工具 - 消除 N+1 问题"""
    
    @staticmethod
    def load_with_relationships(session: Session, model_class: Type[T], 
                               primary_key: Any, relationships: Optional[List[str]] = None) -> Optional[T]:
        """
        在单个查询中加载关联数据（消除 N+1）
        
        Args:
            session: SQLModel Session
            model_class: 数据模型类
            primary_key: 主键值
            relationships: 要预加载的关系列表 (属性名)
            
        Returns:
            带有关联数据的模型实例
            
        Example:
            # 加载用户及其所有事件
            user = RelationshipLoader.load_with_relationships(
                session, User, user_id, 
                relationships=['events', 'members']
            )
        """
        try:
            stmt = select(model_class).where(model_class.id == primary_key)  # type: ignore[union-attr]
            
            # 应用关系预加载
            if relationships:
                for rel in relationships:
                    if hasattr(model_class, rel):
                        stmt = stmt.options(selectinload(getattr(model_class, rel)))
                        logger.debug(f"📦 预加载关系: {model_class.__name__}.{rel}")
            
            result = session.exec(stmt).first()
            logger.info(f"✅ 关系加载成功: {model_class.__name__}#{primary_key}")
            return result
        except Exception as e:
            logger.error(f"❌ 关系加载失败: {str(e)}")
            raise
    
    @staticmethod
    def load_multiple_with_relationships(session: Session, model_class: Type[T],
                                        filter_criteria: Optional[dict] = None,
                                        relationships: Optional[List[str]] = None,
                                        limit: int = 100) -> List[T]:
        """
        批量加载带关联数据的多个对象
        
        Args:
            session: SQLModel Session
            model_class: 数据模型类
            filter_criteria: 过滤条件字典
            relationships: 要预加载的关系列表
            limit: 最大返回数量
            
        Returns:
            模型实例列表
            
        Example:
            # 加载所有活跃用户及其成员
            users = RelationshipLoader.load_multiple_with_relationships(
                session, User,
                filter_criteria={'is_active': True},
                relationships=['members']
            )
        """
        try:
            stmt = select(model_class)
            
            # 应用过滤条件
            if filter_criteria:
                conditions = []
                for key, value in filter_criteria.items():
                    if hasattr(model_class, key):
                        conditions.append(getattr(model_class, key) == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            # 应用关系预加载
            if relationships:
                for rel in relationships:
                    if hasattr(model_class, rel):
                        stmt = stmt.options(selectinload(getattr(model_class, rel)))
            
            stmt = stmt.limit(limit)
            results = session.exec(stmt).all()
            
            logger.info(f"✅ 批量关系加载成功: {len(results)} 个 {model_class.__name__}")
            return list(results)
        except Exception as e:
            logger.error(f"❌ 批量关系加载失败: {str(e)}")
            raise


class EagerLoadingHelper:
    """预加载辅助工具"""
    
    @staticmethod
    def eager_load_users_with_members(session: Session, user_ids: List[int]) -> dict:
        """
        预加载用户及其成员列表
        
        效率提升:
        - 优化前: 1 次查询用户 + N 次查询成员 = N+1 次查询
        - 优化后: 2 次查询 (1 个用户查询 + 1 个批量成员查询)
        """
        from models import User, Member
        
        try:
            # 单次查询所有用户及其成员
            stmt = select(User).where(
                User.id.in_(user_ids),  # type: ignore[union-attr]
                User.deleted_at.is_(None)  # type: ignore[union-attr]
            ).options(
                selectinload(User.members)  # type: ignore[attr-defined]  # 假设存在 members 关系
            )
            
            users = session.exec(stmt).unique().all()
            
            logger.info(f"✅ 预加载完成: {len(users)} 个用户及其成员")
            return {user.id: user for user in users}
        except Exception as e:
            logger.warning(f"⚠️  关系可能不存在，使用手动加载: {str(e)}")
            # 回退方案：手动加载
            users_dict = {}
            for user_id in user_ids:
                stmt = select(User).where(
                    User.id == user_id,
                    User.deleted_at.is_(None)  # type: ignore[union-attr]
                )
                user = session.exec(stmt).first()
                if user:
                    users_dict[user_id] = user
            return users_dict
    
    @staticmethod
    def eager_load_events_with_members(session: Session, member_ids: List[int]) -> dict:
        """
        预加载成员及其事件列表
        """
        from models import Member, Event
        
        try:
            stmt = select(Member).where(
                Member.id.in_(member_ids),  # type: ignore[union-attr]
                Member.deleted_at.is_(None)  # type: ignore[union-attr]
            ).options(
                selectinload(Member.events)  # type: ignore[attr-defined]  # 假设存在 events 关系
            )
            
            members = session.exec(stmt).unique().all()
            
            logger.info(f"✅ 预加载完成: {len(members)} 个成员及其事件")
            return {member.id: member for member in members}
        except Exception as e:
            logger.warning(f"⚠️  关系可能不存在，使用手动加载: {str(e)}")
            # 回退方案：手动加载
            members_dict = {}
            for member_id in member_ids:
                stmt = select(Member).where(
                    Member.id == member_id,
                    Member.deleted_at.is_(None)  # type: ignore[union-attr]
                )
                member = session.exec(stmt).first()
                if member:
                    members_dict[member_id] = member
            return members_dict


class ComplexQueryOptimizer:
    """复杂查询优化"""
    
    @staticmethod
    def count_with_optimization(session: Session, model_class: Type[T],
                               filter_criteria: Optional[dict] = None) -> int:
        """
        优化的记录计数（避免加载完整数据）
        
        Example:
            count = ComplexQueryOptimizer.count_with_optimization(
                session, Event,
                filter_criteria={'owner_id': user_id}
            )
        """
        from sqlalchemy import func
        
        try:
            stmt = select(func.count(model_class.id))  # type: ignore[attr-defined]
            
            if filter_criteria:
                conditions = []
                for key, value in filter_criteria.items():
                    if hasattr(model_class, key):
                        conditions.append(getattr(model_class, key) == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = session.exec(stmt).one()  # type: ignore[attr-defined]
            return result or 0
        except Exception as e:
            logger.error(f"❌ 计数失败: {str(e)}")
            return 0
    
    @staticmethod
    def exists_query(session: Session, model_class: Type[T],
                    filter_criteria: dict) -> bool:
        """
        优化的存在性检查（只检查是否存在，不加载数据）
        
        Example:
            exists = ComplexQueryOptimizer.exists_query(
                session, Event,
                filter_criteria={'id': event_id, 'deleted_at': None}
            )
        """
        try:
            stmt = select(model_class)
            
            conditions = []
            for key, value in filter_criteria.items():
                if hasattr(model_class, key):
                    if value is None:
                        conditions.append(getattr(model_class, key).is_(None))
                    else:
                        conditions.append(getattr(model_class, key) == value)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.limit(1)
            result = session.exec(stmt).first()
            return result is not None
        except Exception as e:
            logger.error(f"❌ 存在性检查失败: {str(e)}")
            return False
    
    @staticmethod
    def batch_fetch(session: Session, model_class: Type[T],
                   id_list: List[int]) -> dict:
        """
        批量获取（单次查询获取多条记录，避免 N 次查询）
        
        Example:
            events = ComplexQueryOptimizer.batch_fetch(
                session, Event, [1, 2, 3, 4, 5]
            )
        """
        try:
            stmt = select(model_class).where(model_class.id.in_(id_list))  # type: ignore[union-attr]
            results = session.exec(stmt).all()
            
            logger.info(f"✅ 批量获取: {len(results)} 个 {model_class.__name__}")
            return {item.id: item for item in results}  # type: ignore[attr-defined]
        except Exception as e:
            logger.error(f"❌ 批量获取失败: {str(e)}")
            return {}
