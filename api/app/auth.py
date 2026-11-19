import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .main_config import settings
from .models import Tenant, User

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
password_hash = PasswordHash.recommended()


class RegisterInput(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


def slugify(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60] or "workspace"
    return f"{base}-{secrets.token_hex(3)}"


def make_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user.id, "tenant_id": user.tenant_id, "role": user.role,
         "iat": now, "exp": now + timedelta(minutes=settings.jwt_expire_minutes)},
        settings.jwt_secret, algorithm="HS256",
    )


async def current_user(token: Annotated[str, Depends(oauth2_scheme)],
                       db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Invalid or expired access token",
                                 headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id, tenant_id = payload.get("sub"), payload.get("tenant_id")
        if not user_id or not tenant_id:
            raise unauthorized
    except jwt.PyJWTError:
        raise unauthorized
    user = await db.scalar(select(User).where(
        User.id == user_id, User.tenant_id == tenant_id, User.is_active.is_(True)
    ))
    if user is None:
        raise unauthorized
    return user


@router.post("/register", status_code=201)
async def register(data: RegisterInput, db: Annotated[AsyncSession, Depends(get_db)]):
    email = data.email.lower()
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(409, "An account with this email already exists")
    tenant = Tenant(name=data.organization_name.strip(), slug=slugify(data.organization_name))
    db.add(tenant)
    await db.flush()
    user = User(tenant_id=tenant.id, email=email,
                password_hash=password_hash.hash(data.password), role="owner")
    db.add(user)
    await db.commit()
    return {"access_token": make_token(user), "token_type": "bearer",
            "tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug},
            "user": {"id": user.id, "email": user.email, "role": user.role}}


@router.post("/login")
async def login(data: LoginInput, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not password_hash.verify(data.password, user.password_hash) or not user.is_active:
        raise HTTPException(401, "Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": make_token(user), "token_type": "bearer",
            "tenant_id": user.tenant_id, "role": user.role}


@router.get("/me")
async def me(user: Annotated[User, Depends(current_user)]):
    return {"id": user.id, "email": user.email, "role": user.role,
            "tenant_id": user.tenant_id}
