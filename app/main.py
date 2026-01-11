from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from app.modules.auth.router import router as auth_router
from app.modules.profiles.router import router as profiles_router
from app.modules.classes.router import router as classes_router
from app.modules.attendance.router import router as attendance_router
from app.modules.assignments.router import router as assignments_router
from app.modules.submissions.router import router as submissions_router
from app.modules.grades.router import router as grades_router
from app.modules.admin.router import router as admin_router

# Create security scheme for JWT Bearer tokens
security = HTTPBearer()

app = FastAPI(
    title="LearnMate Backend MVP",
    description="Education platform backend with role-based access control",
    version="1.0.0"
)

# Custom OpenAPI schema to configure security properly
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="LearnMate Backend MVP",
        version="1.0.0",
        description="Education platform backend with role-based access control",
        routes=app.routes,
    )

    # Add security schemes for Swagger UI
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Add security requirements to endpoints that need authentication
    # This makes the lock icon appear in Swagger UI for protected endpoints
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            # Skip endpoints that don't need authentication
            if path in ["/", "/health"] or path.startswith("/auth/") or path == "/admin/bootstrap-admin":
                continue

            # Add security requirement for all other endpoints
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Root route (test)
@app.get("/")
def root():
    return {"message": "Hello World from LearnMate!"}

# Health check route
@app.get("/health")
def health_check():
    """Check if the service and database connection are healthy"""
    try:
        from app.db.supabase import supabase
        # Test database connection
        test_response = supabase.table('profiles').select('id').limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2026-01-09T23:14:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"error: {str(e)}",
            "timestamp": "2026-01-09T23:14:00Z"
        }

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(profiles_router, prefix="/profiles", tags=["Profiles"])
app.include_router(classes_router, prefix="/classes", tags=["Classes"])
app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
app.include_router(assignments_router, prefix="/assignments", tags=["Assignments"])
app.include_router(submissions_router, prefix="/submissions", tags=["Submissions"])
app.include_router(grades_router, prefix="/grades", tags=["Grades"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
