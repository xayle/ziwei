"""
权限管理服务 - 基于角色的访问控制 (RBAC)
"""

from enum import Enum


# 定义权限枚举
class Permission(str, Enum):
    """系统权限定义"""

    # 成员管理
    CREATE_MEMBER = "create_member"
    READ_MEMBER = "read_member"
    UPDATE_MEMBER = "update_member"
    DELETE_MEMBER = "delete_member"

    # 事件管理
    CREATE_EVENT = "create_event"
    READ_EVENT = "read_event"
    UPDATE_EVENT = "update_event"
    DELETE_EVENT = "delete_event"

    # 场景管理
    CREATE_SCENARIO = "create_scenario"
    READ_SCENARIO = "read_scenario"
    UPDATE_SCENARIO = "update_scenario"
    DELETE_SCENARIO = "delete_scenario"

    # 权限委托
    DELEGATE_PERMISSIONS = "delegate_permissions"
    REVOKE_PERMISSIONS = "revoke_permissions"

    # 管理员
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOG = "view_audit_log"

    # 委托级别权限 (高级聚合权限，供用户间委托使用)
    # 对应: view=只读 / edit=读写 / share=可再委托 / manage=完整管理
    VIEW = "view"
    EDIT = "edit"
    SHARE = "share"
    MANAGE = "manage"


class Role(str, Enum):
    """系统角色定义"""

    OWNER = "owner"  # 所有者 - 完全权限
    EDITOR = "editor"  # 编辑者 - 创建、编辑、删除
    VIEWER = "viewer"  # 查看者 - 仅读取
    GUEST = "guest"  # 宾客 - 受限查看


# 角色权限映射表
ROLE_PERMISSIONS = {
    Role.OWNER: [
        Permission.CREATE_MEMBER,
        Permission.READ_MEMBER,
        Permission.UPDATE_MEMBER,
        Permission.DELETE_MEMBER,
        Permission.CREATE_EVENT,
        Permission.READ_EVENT,
        Permission.UPDATE_EVENT,
        Permission.DELETE_EVENT,
        Permission.CREATE_SCENARIO,
        Permission.READ_SCENARIO,
        Permission.UPDATE_SCENARIO,
        Permission.DELETE_SCENARIO,
        Permission.DELEGATE_PERMISSIONS,
        Permission.REVOKE_PERMISSIONS,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG,
        # 委托级别权限：OWNER 可委托全部级别
        Permission.VIEW,
        Permission.EDIT,
        Permission.SHARE,
        Permission.MANAGE,
    ],
    Role.EDITOR: [
        Permission.READ_MEMBER,
        Permission.UPDATE_MEMBER,
        Permission.CREATE_EVENT,
        Permission.READ_EVENT,
        Permission.UPDATE_EVENT,
        Permission.DELETE_EVENT,
        Permission.CREATE_SCENARIO,
        Permission.READ_SCENARIO,
        Permission.UPDATE_SCENARIO,
        Permission.DELETE_SCENARIO,
        # 委托级别权限：EDITOR 可委托只读和编辑
        Permission.VIEW,
        Permission.EDIT,
    ],
    Role.VIEWER: [
        Permission.READ_MEMBER,
        Permission.READ_EVENT,
        Permission.READ_SCENARIO,
        # 委托级别权限：VIEWER 只能委托只读
        Permission.VIEW,
    ],
    Role.GUEST: [
        Permission.READ_MEMBER,
    ],
}


def has_permission(user_role: Role, required_permission: Permission) -> bool:
    """
    检查用户是否拥有指定权限

    Args:
        user_role: 用户角色
        required_permission: 需要的权限

    Returns:
        bool: 是否拥有权限
    """
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in permissions


def check_member_access(user_id: int, member_owner_id: int, required_permission: Permission, user_role: Role) -> bool:
    """
    检查用户是否可以访问特定成员

    Rules:
    - 如果是所有者，有完全权限
    - 如果有权限委托，检查委托权限

    Args:
        user_id: 当前用户ID
        member_owner_id: 成员所有者ID
        required_permission: 需要的权限
        user_role: 用户角色

    Returns:
        bool: 是否可以访问
    """
    # 所有者可以访问自己的成员
    if user_id == member_owner_id:
        return has_permission(user_role, required_permission)

    # 其他用户需要权限委托
    # 这里将在db中实现，检查delegations表
    return False


def get_user_role(is_admin: bool = False) -> Role:
    """
    根据用户属性获取默认角色

    Args:
        is_admin: 是否是管理员

    Returns:
        Role: 用户角色
    """
    if is_admin:
        return Role.OWNER
    return Role.EDITOR
