from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from modules import user, course, interaction, earning, messaging, public
from routers import user as user_router_mod, course as course_router_mod, enrollment as enrollment_router_mod, cart as cart_router_mod, review as review_router_mod, instructor as instructor_router_mod, player as player_router_mod, earnings as earnings_router_mod, chat as chat_router_mod, public as public_router_mod

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-commerce Course Platform API",
    description="API for Course Catalog, Enrollment, Progress Tracking, and Shopping Cart",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router_mod.router)
app.include_router(course_router_mod.router)
app.include_router(enrollment_router_mod.router)
app.include_router(cart_router_mod.router)
app.include_router(player_router_mod.router)
app.include_router(review_router_mod.router)
app.include_router(instructor_router_mod.router)
app.include_router(earnings_router_mod.router)
app.include_router(chat_router_mod.router)
app.include_router(public_router_mod.router)

@app.get("/api/v1/")
def root():
    return {"message": "Welcome to the E-commerce Course Platform API"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")