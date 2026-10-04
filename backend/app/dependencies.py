from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, UserRole, UserStatus, SellerProfile, SellerApprovalStatus
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Return user if valid token present, otherwise None."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None
    user = db.query(User).filter(User.id == user_id_int).first()
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Validate token and return active user. Raise 401 if missing/invalid."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
        
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
        
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id_int).first()
    if user is None:
        raise credentials_exception
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account status is {user.status.value}. Please contact support."
        )
        
    return user


def get_current_seller(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SellerProfile:
    """Ensure user is an approved seller or admin."""
    if current_user.role == UserRole.ADMIN:
        # Admin can access seller tools through a fallback or query
        seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
        if not seller:
            # Create a mock/admin seller profile if missing
            seller = SellerProfile(
                user_id=current_user.id,
                business_name="Marketplace Admin Store",
                approval_status=SellerApprovalStatus.APPROVED
            )
            db.add(seller)
            db.commit()
            db.refresh(seller)
        return seller

    if current_user.role != UserRole.SELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Seller privileges required"
        )
    
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found. Please complete registration."
        )
        
    if seller.approval_status != SellerApprovalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Seller account is {seller.approval_status.value}. Awaiting admin approval."
        )
        
    return seller


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is an administrator."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required"
        )
    return current_user
