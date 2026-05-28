from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_tokens, decode_token
)
from app.core.dependencies import get_current_user
from app.models.models import User, TokenBlacklist
from app.schemas.schemas import (
    UserCreate, UserLogin, RegisterResponse,
    TokenResponse, RefreshRequest, LogoutRequest, MessageResponse
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_data.username, email=user_data.email,
        first_name=user_data.first_name, last_name=user_data.last_name,
        phone=user_data.phone, role=user_data.role,
        password=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user": user, "tokens": create_tokens(user.id)}


# @router.post("/login", response_model=RegisterResponse)
# def login(credentials: UserLogin, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.username == credentials.username).first()
#     if not user or not verify_password(credentials.password, user.password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
#     if not user.is_active:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
#     return {"user": user, "tokens": create_tokens(user.id)}

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    tokens = create_tokens(user.id)
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == request.refresh_token).first()
    if blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    db.add(TokenBlacklist(token=request.refresh_token, expires_at=datetime.fromtimestamp(payload.get("exp"))))
    db.commit()
    return create_tokens(user.id)


@router.post("/logout", response_model=MessageResponse)
def logout(request: LogoutRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payload = decode_token(request.refresh_token)
    if payload:
        db.add(TokenBlacklist(token=request.refresh_token, expires_at=datetime.fromtimestamp(payload.get("exp"))))
        db.commit()
    return {"message": "Logged out successfully"}
