"""User service — user CRUD, random password generation, and audit.

All database mutations go through this module so that audit logging and
password policies are enforced consistently.
"""

import random
import string
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.core.security import get_password_hash, verify_password
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Random Password Generation ────────────────────────────────────────────

_SPECIAL_CHARS = "!@#$%^&*"


def generate_random_password(length: int = 12) -> str:
    """Generate a random password that satisfies the password policy.

    The generated password contains at least one uppercase letter, one
    lowercase letter, one digit, and one special character.
    """
    if length < 8:
        length = 8
    # Guarantee at least one of each required class
    chars = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice(_SPECIAL_CHARS),
    ]
    pool = string.ascii_letters + string.digits + _SPECIAL_CHARS
    chars.extend(random.choice(pool) for _ in range(length - len(chars)))
    random.shuffle(chars)
    return "".join(chars)


# ── CRUD ───────────────────────────────────────────────────────────────────


def list_users(db: Session) -> List[User]:
    """Return all users."""
    return db.query(User).all()


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Return a single user by ID, or None."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Return a single user by username, or None."""
    return db.query(User).filter(User.username == username).first()


def create_user(
    db: Session,
    *,
    username: str,
    password: Optional[str] = None,
    role: str = "equipment_engineer",
    email: Optional[str] = None,
    display_name: Optional[str] = None,
    current_user: Optional[User] = None,
) -> User:
    """Create a new user.  If *password* is not provided a random one is
    generated and ``must_change_password`` is set to True.
    """
    if not password:
        password = generate_random_password()
        must_change = True
    else:
        must_change = False

    hashed = get_password_hash(password)
    user = User(
        username=username,
        password=hashed,
        role=role,
        email=email,
        display_name=display_name,
        must_change_password=must_change,
        status="active",
    )
    db.add(user)
    db.flush()

    operator = current_user.username if current_user else "system"
    log_action(db, operator, "create_user", "user", user.id, f"创建用户 {username}")

    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user_id: int,
    *,
    username: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[str] = None,
    email: Optional[str] = None,
    display_name: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Optional[User] = None,
) -> User:
    """Update an existing user.  Only non-None fields are modified."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    before = {
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status,
    }

    if username is not None and username != user.username:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("Username already exists")
        user.username = username
    if password is not None and password != "__KEEP__":
        user.password = get_password_hash(password)
        user.must_change_password = False
    if role is not None:
        user.role = role
    if email is not None:
        user.email = email
    if display_name is not None:
        user.display_name = display_name
    if status is not None:
        user.status = status

    after = {
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status,
    }

    operator = current_user.username if current_user else "system"
    log_action(
        db,
        operator,
        "update_user",
        "user",
        user.id,
        f"更新用户 {user.username}",
        before_value=str(before),
        after_value=str(after),
    )

    db.commit()
    db.refresh(user)
    return user


def delete_user(
    db: Session,
    user_id: int,
    *,
    current_user: Optional[User] = None,
) -> None:
    """Hard-delete a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    operator = current_user.username if current_user else "system"
    log_action(db, operator, "delete_user", "user", user.id, f"删除用户 {user.username}")

    db.delete(user)
    db.commit()


def change_password(
    db: Session,
    user: User,
    old_password: str,
    new_password: str,
) -> None:
    """Change *user*'s password after verifying the old one."""
    if not verify_password(old_password, user.password):
        raise ValueError("原密码不正确")
    user.password = get_password_hash(new_password)
    user.must_change_password = False
    log_action(db, user.username, "change_password", "user", user.id, "修改密码")
    db.commit()
