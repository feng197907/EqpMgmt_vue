# 装饰器工具
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user, login_required

from config import ROLES, ROLE_LABELS, normalize_role
from extensions import login_manager


def admin_required(view_func):
    """管理员权限装饰器"""

    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("仅管理员可执行此操作。", "warning")
            return redirect(url_for("auth.index"))
        return view_func(*args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


def role_required(*allowed_roles):
    """
    角色权限装饰器
    
    用法:
        @role_required("admin", "qa_manager")
        def my_view():
            ...
    
    参数:
        allowed_roles: 允许访问的角色列表（可以是角色键或角色对象）
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # 标准化当前用户的角色（处理旧角色兼容）
            user_role = normalize_role(current_user.role)

            # 检查是否是admin角色（admin拥有所有权限）
            if user_role == "admin":
                return view_func(*args, **kwargs)

            # 检查用户角色是否在允许列表中
            # 支持传入角色键或角色对象
            normalized_allowed = [normalize_role(r) if isinstance(r, str) else r for r in allowed_roles]

            if user_role not in normalized_allowed:
                flash(f"您没有权限执行此操作（需要角色: {', '.join(normalized_allowed)}）。", "danger")
                return redirect(url_for("auth.index"))

            return view_func(*args, **kwargs)

        wrapper.__name__ = view_func.__name__
        return login_required(wrapper)

    return decorator


def permission_required(*required_permissions):
    """
    功能权限装饰器
    
    用法:
        @permission_required("document_upload", "document_archive")
        def upload_document():
            ...
    
    参数:
        required_permissions: 需要的功能权限列表
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            from config import has_permission

            # 标准化当前用户的角色
            user_role = normalize_role(current_user.role)

            # 检查每个所需权限
            for perm in required_permissions:
                if not has_permission(user_role, perm):
                    flash(f"您没有执行此操作所需的权限。", "danger")
                    return redirect(url_for("auth.index"))

            return view_func(*args, **kwargs)

        wrapper.__name__ = view_func.__name__
        return login_required(wrapper)

    return decorator
