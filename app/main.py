from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.profiles.router import router as profiles_router
from app.modules.classes.router import router as classes_router
from app.modules.attendance.router import router as attendance_router
from app.modules.assignments.router import router as assignments_router
from app.modules.submissions.router import router as submissions_router
from app.modules.grades.router import router as grades_router
from app.modules.admin.router import router as admin_router

app = FastAPI(
    title="LearnMate Backend MVP",
    description="Education platform backend with role-based access control",
    version="1.0.0"
)

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

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(profiles_router, prefix="/profiles", tags=["Profiles"])
app.include_router(classes_router, prefix="/classes", tags=["Classes"])
app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
app.include_router(assignments_router, prefix="/assignments", tags=["Assignments"])
app.include_router(submissions_router, prefix="/submissions", tags=["Submissions"])
app.include_router(grades_router, prefix="/grades", tags=["Grades"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
