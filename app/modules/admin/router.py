from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.core.dependencies import require_admin_by_uuid, get_current_school_id, get_school_id_for_user
from app.schemas.profiles import ProfileCreate
import secrets
import string
from uuid import UUID

router = APIRouter(tags=["Admin"])

@router.get("/metrics")
def get_admin_metrics(school_id: UUID = Depends(get_current_school_id)):
    """
    Get admin metrics for the current user's school. Admin only.
    """
    try:
        # Total users in school
        total_users = supabase.table("profiles").select("id", count="exact").eq("school_id", str(school_id)).execute()
        total_users_count = total_users.count if hasattr(total_users, 'count') else len(total_users.data)

        # Active users (users with recent activity - last 30 days)
        active_users_count = total_users_count  # Placeholder

        # Attendance count (total attendance records in school)
        attendance_count = supabase.table("attendance").select("id", count="exact").eq("school_id", str(school_id)).execute()
        attendance_count = attendance_count.count if hasattr(attendance_count, 'count') else len(attendance_count.data)

        # Assignments created in school
        assignments_count = supabase.table("assignments").select("id", count="exact").eq("school_id", str(school_id)).execute()
        assignments_count = assignments_count.count if hasattr(assignments_count, 'count') else len(assignments_count.data)

        # Grades entered in school
        grades_count = supabase.table("grades").select("id", count="exact").eq("school_id", str(school_id)).execute()
        grades_count = grades_count.count if hasattr(grades_count, 'count') else len(grades_count.data)

        # Classes count in school
        classes_count = supabase.table("classes").select("id", count="exact").eq("school_id", str(school_id)).execute()
        classes_count = classes_count.count if hasattr(classes_count, 'count') else len(classes_count.data)

        # Students enrolled in school
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
def get_all_users(school_id: UUID = Depends(get_current_school_id)):
    """
    Get all users with their profiles for the current user's school. Admin only.
    """
    try:
        result = supabase.table("profiles").select("*").eq("school_id", str(school_id)).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@router.post("/users")
def create_user(
    user_data: ProfileCreate,
    admin_user: dict = Depends(require_admin_by_uuid)  # FIXED: Changed to receive dict
):
    """
    Create a new user (teacher or student) in the current user's school. Admin only.
    Creates user in Supabase auth.users and profiles table.
    FIXED: Queries school_id from database instead of relying on JWT to avoid race conditions.
    """
    try:
        # FIXED: Extract user_id from the dict (handles both 'id' and 'user_id' keys)
        admin_user_id = admin_user.get("id") or admin_user.get("user_id")
        
        if not admin_user_id:
            raise HTTPException(status_code=403, detail="Could not identify admin user")
        
        # CRITICAL FIX: Get school_id from database, not from JWT/dependency
        admin_profile = supabase.table("profiles").select("school_id, role").eq("id", admin_user_id).execute()
        if not admin_profile.data:
            raise HTTPException(status_code=403, detail="Admin profile not found")
        
        admin_data = admin_profile.data[0]
        if admin_data.get("role") != "admin":
            raise HTTPException(status_code=403, detail="User is not an admin")
        
        school_id = admin_data.get("school_id")
        if not school_id:
            raise HTTPException(status_code=400, detail="Admin not assigned to a school. Please create or join a school first.")
        
        # Debug logging
        print("=" * 50)
        print("DEBUG: create_user function called")
        print(f"DEBUG: Admin User Object: {admin_user}")
        print(f"DEBUG: Admin ID extracted: {admin_user_id}")
        print(f"DEBUG: School ID from database: {school_id}")
        print(f"DEBUG: user_data.email: '{user_data.email}'")
        print(f"DEBUG: user_data.role: '{user_data.role}'")
        print("=" * 50)

        # Validate role (allow admin, teacher, student)
        if user_data.role not in ["admin", "teacher", "student"]:
            raise HTTPException(status_code=400, detail="Role must be one of: 'admin', 'teacher', 'student'")

        # Generate password if not provided
        password = user_data.password
        if not password:
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for i in range(12))

        # Create user in Supabase Auth with user_metadata
        try:
            auth_response = supabase.auth.admin.create_user({
                "email": user_data.email,
                "password": password,
                "email_confirm": False,
                "user_metadata": {
                    "firstName": user_data.first_name,
                    "lastName": user_data.last_name,
                    "role": user_data.role,
                    "school_id": school_id  # Include school_id in auth metadata
                }
            })
            user_id = auth_response.user.id
        except Exception as auth_error:
            error_detail = str(auth_error)
            if hasattr(auth_error, '__dict__'):
                error_detail += f" | Details: {auth_error.__dict__}"

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
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "full_name": f"{user_data.first_name} {user_data.last_name}",
                "role": user_data.role,
                "school_id": school_id  # Use school_id from database query
            }
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
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "school_id": school_id
        }
        if not user_data.password:
            response["generated_password"] = password

        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error creating user: {str(e)}")
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
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for i in range(12))

        # Create user in Supabase Auth with user_metadata
        try:
            auth_response = supabase.auth.admin.create_user({
                "email": user_data.email,
                "password": password,
                "email_confirm": False,
                "user_metadata": {
                    "firstName": user_data.first_name,
                    "lastName": user_data.last_name,
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
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "full_name": f"{user_data.first_name} {user_data.last_name}",
                "role": user_data.role
            }
            supabase.table("profiles").upsert(profile_data).execute()
            
        except Exception as profile_error:
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


@router.delete("/users/{user_id}")
def delete_user(user_id: str):
    """
    Delete a user and all associated data from the current user's school. Admin only.
    This will permanently remove the user from auth.users and profiles table,
    and cascade delete all related records (classes, attendance, submissions, etc.)
    """
    try:
        # Get school_id for this user
        school_id = get_school_id_for_user(user_id)
        
        # Check if user exists and belongs to the school
        user_check = supabase.table("profiles").select("id, email, role").eq("id", user_id).eq("school_id", str(school_id)).execute()
        if not user_check.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = user_check.data[0]

        # Prevent deletion of the last admin user in the school
        if user_data["role"] == "admin":
            admin_count = supabase.table("profiles").select("id", count="exact").eq("role", "admin").eq("school_id", str(school_id)).execute()
            admin_total = admin_count.count if hasattr(admin_count, 'count') else len(admin_count.data)
            if admin_total <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the last admin user in the school")

        # Delete from profiles table first (this will cascade delete related records)
        try:
            supabase.table("profiles").delete().eq("id", user_id).eq("school_id", str(school_id)).execute()
        except Exception as profile_error:
            raise HTTPException(status_code=500, detail=f"Failed to delete user profile: {str(profile_error)}")

        # Delete from auth.users
        try:
            supabase.auth.admin.delete_user(user_id)
        except Exception as auth_error:
            print(f"WARNING: Failed to delete auth user after profile deletion: {auth_error}")
            raise HTTPException(status_code=500, detail=f"Failed to delete auth user: {str(auth_error)}")

        return {
            "message": f"User {user_data['email']} deleted successfully",
            "user_id": user_id,
            "email": user_data["email"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error deleting user: {str(e)}")


@router.get("/activity")
def get_recent_activity(
    limit: int = 50,
    school_id: UUID = Depends(get_current_school_id)
):
    """
    Get recent activity logs for the current user's school. Admin only.
    """
    try:
        result = supabase.table("activity_logs").select("*").eq("school_id", str(school_id)).order("created_at", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activity logs: {str(e)}")