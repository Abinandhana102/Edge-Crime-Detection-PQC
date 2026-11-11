"""
Authentication & User Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User
from backend.app.schemas import LoginRequest, Token, UserResponse, UserCreate
from backend.app.security.auth_handler import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_admin,
    log_audit_event
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticates police officer or administrator with username & password"""
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Record failed login attempt in audit log
        log_audit_event(
            db=db,
            username=credentials.username,
            action="LOGIN_FAILED",
            details="Invalid username or password attempt",
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is deactivated")

    # Generate JWT
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "badge": user.badge_number}
    )

    # Record successful login
    log_audit_event(
        db=db,
        username=user.username,
        action="LOGIN_SUCCESS",
        details=f"Officer logged in successfully with role '{user.role}'",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_id=user.id
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        role=user.role,
        full_name=user.full_name,
        badge_number=user.badge_number
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns currently authenticated officer profile"""
    return current_user


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to create new police officer accounts"""
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.badge_number == user_data.badge_number)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or Badge Number already registered")

    new_user = User(
        username=user_data.username,
        badge_number=user_data.badge_number,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_event(
        db=db,
        username=current_user.username,
        action="USER_CREATED",
        details=f"Created new user {new_user.username} (Badge: {new_user.badge_number}, Role: {new_user.role})"
    )

    return new_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logs out officer and records audit event"""
    log_audit_event(
        db=db,
        username=current_user.username,
        action="LOGOUT",
        details="Officer logged out of command session",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_id=current_user.id
    )
    return {"message": "Logged out successfully"}
