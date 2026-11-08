from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select

from backend.db import get_db
from backend.models import User
from backend.schemas import Credentials, UserOut

COOKIE_NAME = "access_token"
TOKEN_LIFETIME = timedelta(days=7)
ALGORITHM = "HS256"

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id, secret_key):
    payload = {"sub": str(user_id), "exp": datetime.now(UTC) + TOKEN_LIFETIME}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def token_user_id(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    header = request.headers.get("Authorization", "")
    if not token and header.startswith("Bearer "):
        token = header.removeprefix("Bearer ")
    if not token:
        return None
    try:
        payload = jwt.decode(token, request.app.state.secret_key, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None


def optional_user(request: Request, db=Depends(get_db)):
    user_id = token_user_id(request)
    return db.get(User, user_id) if user_id is not None else None


def current_user(user=Depends(optional_user)):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user


def set_login_cookie(response: Response, request: Request, user):
    response.set_cookie(
        COOKIE_NAME,
        create_token(user.id, request.app.state.secret_key),
        max_age=int(TOKEN_LIFETIME.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: Credentials, request: Request, response: Response, db=Depends(get_db)):
    if db.execute(select(User).where(User.username == body.username)).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is taken")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    set_login_cookie(response, request, user)
    return user


@router.post("/login", response_model=UserOut)
def login(body: Credentials, request: Request, response: Response, db=Depends(get_db)):
    user = db.execute(select(User).where(User.username == body.username)).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password")
    set_login_cookie(response, request, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)


@router.get("/me", response_model=UserOut)
def me(user=Depends(current_user)):
    return user
