from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserRole, UserStatus, SellerProfile, SellerApprovalStatus, Cart, Wishlist
from ..schemas import (
    UserRegister, UserLogin, Token, PasswordChange, ForgotPasswordRequest, ResetPasswordRequest, UserOut
)
from ..security import hash_password, verify_password, create_access_token
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new Customer or Seller account."""
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken"
        )
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    # Hash password
    pwd_hash = hash_password(user_in.password)
    
    new_user = User(
        full_name=user_in.full_name,
        username=user_in.username,
        email=user_in.email,
        phone=user_in.phone,
        password_hash=pwd_hash,
        role=user_in.user_type,
        status=UserStatus.ACTIVE
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize cart and wishlist for customer/seller
    cart = Cart(user_id=new_user.id)
    wishlist = Wishlist(user_id=new_user.id)
    db.add(cart)
    db.add(wishlist)

    # If seller, create seller profile (PENDING approval)
    if user_in.user_type == UserRole.SELLER:
        business_name = user_in.business_name or f"{user_in.full_name}'s Store"
        seller_profile = SellerProfile(
            user_id=new_user.id,
            business_name=business_name,
            business_description=user_in.business_description or "Registered digital marketplace merchant",
            business_address=user_in.business_address or "",
            approval_status=SellerApprovalStatus.PENDING
        )
        db.add(seller_profile)

    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email or username and return JWT token."""
    login_id = login_data.username_or_email.strip()
    user = db.query(User).filter(
        (User.username == login_id) | (User.email == login_id)
    ).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your username/email and password."
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}. Please contact support."
        )

    # If seller, check approval status details for info
    seller_status = None
    if user.role == UserRole.SELLER and user.seller_profile:
        seller_status = user.seller_profile.approval_status.value

    # Token payload
    expires_delta = timedelta(days=30) if login_data.remember_me else timedelta(days=7)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "email": user.email
        },
        expires_delta=expires_delta
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value,
            "seller_status": seller_status,
            "avatar": user.avatar
        }
    }


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout current user (client clears JWT token)."""
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Simulated password reset code delivery."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # Don't leak user existence for production, but provide helpful demo response
        return {"message": "If that email exists, a password reset code has been generated.", "demo_code": "123456"}
    return {
        "message": "Reset code sent successfully to registered email.",
        "demo_code": "123456"
    }


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using verified reset code."""
    if data.reset_code != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password has been successfully reset. Please login with your new password."}


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password does not match"
        )
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
