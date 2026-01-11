from fastapi import Depends, HTTPException, status, Query
from app.core.security import get_current_user
from app.db.supabase import supabase
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

def require_admin_by_uuid(admin_uuid: str = Query(..., description="UUID of the admin user")):
    """
    Dependency to verify admin role by UUID.
    Checks if the provided UUID corresponds to a user with admin role in the profiles table.
    """
    try:
        # Fetch user profile from profiles table using the provided UUID
        profile_response = supabase.table("profiles").select("id, role").eq("id", admin_uuid).execute()

        if not profile_response.data or len(profile_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin user not found"
            )

        profile = profile_response.data[0]

        # Check if role is admin
        if profile.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required"
            )

        return profile

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other exceptions (network issues, Supabase errors, etc.)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify admin access"
        )

def require_teacher_by_uuid(teacher_uuid: str = Query(..., description="UUID of the teacher user")):
    """
    Dependency to verify teacher role by UUID.
    Checks if the provided UUID corresponds to a user with teacher role in the profiles table.
    """
    try:
        # Fetch user profile from profiles table using the provided UUID
        profile_response = supabase.table("profiles").select("id, role").eq("id", teacher_uuid).execute()

        if not profile_response.data or len(profile_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher user not found"
            )

        profile = profile_response.data[0]

        # Check if role is teacher
        if profile.get("role") != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Teacher role required"
            )

        return profile

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other exceptions (network issues, Supabase errors, etc.)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify teacher access"
        )

def require_admin_or_teacher_by_uuid(user_uuid: str = Query(..., description="UUID of the admin or teacher user")):
    """
    Dependency to verify admin or teacher role by UUID.
    Checks if the provided UUID corresponds to a user with admin or teacher role in the profiles table.
    """
    try:
        # Fetch user profile from profiles table using the provided UUID
        profile_response = supabase.table("profiles").select("id, role").eq("id", user_uuid).execute()

        if not profile_response.data or len(profile_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found"
            )

        profile = profile_response.data[0]

        # Check if role is admin or teacher
        if profile.get("role") not in ["admin", "teacher"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin or teacher role required"
            )

        return profile

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other exceptions (network issues, Supabase errors, etc.)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify admin/teacher access"
        )
