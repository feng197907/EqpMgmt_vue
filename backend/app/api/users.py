from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db, require_admin
from backend.app.models.user import User
from backend.app.services.auth_service import get_password_hash

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = 'equipment_engineer'


class UserOut(BaseModel):
    id: int
    username: str
    role: str


@router.get("/", response_model=List[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserOut(id=u.id, username=u.username, role=u.role or '') for u in users]


@router.post("/", response_model=UserOut, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail='Username already exists')
    hashed = get_password_hash(payload.password)
    u = User(username=payload.username, password=hashed, role=payload.role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut(id=u.id, username=u.username, role=u.role or '')


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail='User not found')
    return UserOut(id=u.id, username=u.username, role=u.role or '')


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def update_user(user_id: int, payload: UserCreate, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail='User not found')
    u.username = payload.username
    u.password = get_password_hash(payload.password)
    u.role = payload.role
    db.commit()
    db.refresh(u)
    return UserOut(id=u.id, username=u.username, role=u.role or '')


@router.delete("/{user_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail='User not found')
    db.delete(u)
    db.commit()
    return None
