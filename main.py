from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import user
from routers.user import router as user_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-commerce API",
    description="API for E-commerce",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)

@app.get("/api/v1/")
def root():
    return {"message": "Welcome to the E-commerce API"}