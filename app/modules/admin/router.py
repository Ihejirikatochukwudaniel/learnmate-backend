from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.core.dependencies import require_admin_by_uuid
from app.schemas.profiles import ProfileCreate
import secrets
import string

router = APIRouter(tags=["Admin"])

@router.get("/metrics")
def get_admin_metrics(_: dict = Depends(require_admin_by_uuid)):
    """
    Get admin metrics. Admin only.
    """
    try:
        # Total users
        total_users = supabase.table("profiles").select("id", count="exact").execute()
        total_users_count = total_users.count if hasattr(total_users, 'count') else len(total_users.data)

        # Active users (users with recent activity - last 30 days)
        # For simplicity, we'll count users who have logged in recently
        # This would need activity_logs table to be properly implemented
        active_users_count = total_users_count  # Placeholder

        # Attendance count (total attendance records)
        attendance_count = supabase.table("attendance").select("id", count="exact").execute()
        attendance_count = attendance_count.count if hasattr(attendance_count, 'count') else len(attendance_count.data)

        # Assignments created
        assignments_count = supabase.table("assignments").select("id", count="exact").execute()
        assignments_count = assignments_count.count if hasattr(assignments_count, 'count') else len(assignments_count.data)

        # Grades entered
        grades_count = supabase.table("grades").select("id", count="exact").execute()
        grades_count = grades_count.count if hasattr(grades_count, 'count') else len(grades_count.data)

        # Classes count
        classes_count = supabase.table("classes").select("id", count="exact").execute()
        classes_count = classes_count.count if hasattr(classes_count, 'count') else len(classes_count.data)

        # Students enrolled
        students_enrolled = supabase.table("class_students").select("student_id", count="exact").execute()
        students_enrolled_count = students_enrolled.count if hasattr(students_enrolled, 'count') else len(students_enrolled.data)

        return {
            "total_users": total_users_count,
            "active_users": active_users_count,
            "total_classes": classes_count,
            "students_enrolled": students_enrolled_count,
            "attendance_records": attendance_count,
            "assignments_created": assignments_count,
            "grades_entered": grades_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@router.get("/users")
def get_all_users(_: dict = Depends(require_admin_by_uuid)):
    """
    Get all users with their profiles. Admin only.
    """
    try:
        result = supabase.table("profiles").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

@router.post("/users")
def create_user(user_data: ProfileCreate, _: dict = Depends(require_admin_by_uuid)):
    """
    Create a new user (teacher or student). Admin only.
    Creates user in Supabase auth.users and profiles table.
    Uses UUID-based admin verification.
    """
    try:
        # Debug logging
        print("=" * 50)
        print("DEBUG: create_user function called")
        print(f"DEBUG: Raw user_data object: {user_data}")
        print(f"DEBUG: user_data.email: '{user_data.email}' (type: {type(user_data.email)})")
        print(f"DEBUG: user_data.firstName: '{user_data.firstName}' (type: {type(user_data.firstName)})")
        print(f"DEBUG: user_data.lastName: '{user_data.lastName}' (type: {type(user_data.lastName)})")
        print(f"DEBUG: user_data.role: '{user_data.role}' (type: {type(user_data.role)})")
        print(f"DEBUG: user_data.password: '{user_data.password}' (type: {type(user_data.password)})")
        print("=" * 50)

        # Validate role
        if user_data.role not in ["teacher", "student"]:
            raise HTTPException(status_code=400, detail="Role must be 'teacher' or 'student'")

        # Generate password if not provided
        password = user_data.password
        if not password:
            # Generate a secure 12-character password
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for i in range(12))

        # Create user in Supabase Auth with user_metadata
        try:
            auth_response = supabase.auth.admin.create_user({
                "email": user_data.email,
                "password": password,
                "email_confirm": False,  # Disable email confirmation
                "user_metadata": {
                    "firstName": user_data.firstName,
                    "lastName": user_data.lastName,
                    "role": user_data.role
                }
            })
            user_id = auth_response.user.id
        except Exception as auth_error:
            # Extract more detailed error information
            error_detail = str(auth_error)
            if hasattr(auth_error, '__dict__'):
                error_detail += f" | Details: {auth_error.__dict__}"

            # Check for common error patterns
            if "email" in error_detail.lower() and ("already" in error_detail.lower() or "exists" in error_detail.lower()):
                error_detail = f"Email '{user_data.email}' is already registered. Please use a different email address."
            elif "password" in error_detail.lower():
                error_detail = f"Password validation failed: {error_detail}"
            elif "role" in error_detail.lower():
                error_detail = f"Role validation failed: {error_detail}"

            raise HTTPException(status_code=400, detail=f"Failed to create auth user: {error_detail}")

        # Create profile in profiles table using upsert
        try:
            profile_data = {
                "id": user_id,
                "email": user_data.email,
                "first_name": user_data.firstName,
                "last_name": user_data.lastName,
                "full_name": f"{user_data.firstName} {user_data.lastName}",
                "role": user_data.role
            }
            # Use upsert to handle case where profile might already exist from a trigger
            supabase.table("profiles").upsert(profile_data).execute()
            
        except Exception as profile_error:
            # If profile creation fails, clean up the auth user
            try:
                supabase.auth.admin.delete_user(user_id)
            except Exception as cleanup_error:
                print(f"WARNING: Failed to cleanup auth user after profile creation failure: {cleanup_error}")
            raise HTTPException(status_code=400, detail=f"Failed to create user profile: {str(profile_error)}")

        response = {
            "message": f"{user_data.role.title()} user created successfully",
            "user_id": user_id,
            "email": user_data.email,
            "role": user_data.role,
            "first_name": user_data.firstName,
            "last_name": user_data.lastName
        }
        if not user_data.password:
            response["generated_password"] = password

        return response
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error creating user: {str(e)}")

@router.post("/bootstrap-admin")
def bootstrap_admin(user_data: ProfileCreate):
    """
    Bootstrap the first admin user. No authentication required.
    Only works when no users exist in the system.
    """
    try:
        # Check if any users exist
        existing_users = supabase.table("profiles").select("id", count="exact").execute()
        total_users = existing_users.count if hasattr(existing_users, 'count') else len(existing_users.data)

        if total_users > 0:
            raise HTTPException(status_code=403, detail="Bootstrap only available for first user creation")

        # Validate that the role is admin for bootstrap
        if user_data.role != "admin":
            raise HTTPException(status_code=400, detail="Bootstrap user must have 'admin' role")

        # Generate password if not provided
        password = user_data.password
        if not password:
            # Generate a secure 12-character password
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for i in range(12))

        # Create user in Supabase Auth with user_metadata
        try:
            auth_response = supabase.auth.admin.create_user({
                "email": user_data.email,
                "password": password,
                "email_confirm": False,  # Disable email confirmation
                "user_metadata": {
                    "firstName": user_data.firstName,
                    "lastName": user_data.lastName,
                    "role": user_data.role
                }
            })
            user_id = auth_response.user.id
        except Exception as auth_error:
            error_detail = str(auth_error)
            if "email" in error_detail.lower() and ("already" in error_detail.lower() or "exists" in error_detail.lower()):
                error_detail = f"Email '{user_data.email}' is already registered. Please use a different email address."
            raise HTTPException(status_code=400, detail=f"Failed to create auth user: {error_detail}")

        # Create profile in profiles table using upsert
        try:
            profile_data = {
                "id": user_id,
                "email": user_data.email,
                "first_name": user_data.firstName,
                "last_name": user_data.lastName,
                "full_name": f"{user_data.firstName} {user_data.lastName}",
                "role": user_data.role
            }
            # Use upsert to handle case where profile might already exist from a trigger
            supabase.table("profiles").upsert(profile_data).execute()
            
        except Exception as profile_error:
            # If profile creation fails, clean up the auth user
            try:
                supabase.auth.admin.delete_user(user_id)
            except Exception as cleanup_error:
                print(f"WARNING: Failed to cleanup auth user after profile creation failure: {cleanup_error}")
            raise HTTPException(status_code=400, detail=f"Failed to create user profile: {str(profile_error)}")

        response = {
            "message": "Admin user created successfully (bootstrap)",
            "user_id": user_id,
            "email": user_data.email,
            "role": user_data.role
        }
        if not user_data.password:
            response["generated_password"] = password

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bootstrap admin: {str(e)}")

@router.get("/activity")
def get_recent_activity(limit: int = 50, _: dict = Depends(require_admin_by_uuid)):
    """
    Get recent activity logs. Admin only.
    """
    try:
        result = supabase.table("activity_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activity logs: {str(e)}")