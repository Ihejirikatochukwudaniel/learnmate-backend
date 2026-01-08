from fastapi import FastAPI
from app.modules.auth.router import router as auth_router

app = FastAPI(title="LearnMate Backend MVP")

# Root route (test)
@app.get("/")
def root():
    return {"message": "Hello World from LearnMate!"}

# Include auth router
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
