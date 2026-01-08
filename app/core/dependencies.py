from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from typing import Dict

def require_role(required_role: str):
    """
    Dependency to check if user has the required role.
    """
    def role_checker(user: Dict = Depends(get_current_user)):
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return user
    return role_checker

def require_admin(user: Dict = Depends(get_current_user)):
    """Require admin role"""
    return require_role("admin")(user)

def require_teacher(user: Dict = Depends(get_current_user)):
    """Require teacher role"""
    return require_role("teacher")(user)

def require_student(user: Dict = Depends(get_current_user)):
    """Require student role"""
    return require_role("student")(user)

def require_admin_or_teacher(user: Dict = Depends(get_current_user)):
    """Require admin or teacher role"""
    if user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Required role: admin or teacher"
        )
    return user