from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from modules.user import User
from schemas.user import UserCreate, UserResponse, UserUpdate, Token, ForgotPasswordRequest, ResetPassword, UserRole
from fastapi.security import OAuth2PasswordRequestForm
import oauth2
import smtplib
from email.message import EmailMessage
from google.oauth2 import id_token #type: ignore
from google.auth.transport import requests as google_requests #type: ignore
import os
from dotenv import load_dotenv
load_dotenv()
import httpx #type: ignore
from jose import jwt, JWTError #type: ignore

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")

router = APIRouter(
    tags=['Users']
)

@router.post("/register", response_model=UserResponse)
def register(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    role: UserRole = Form(UserRole.student),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(User).filter(User.email == email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if username == "":
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    
    if role not in ["student", "instructor"]:
        role = UserRole.student
    
    hashed_password = oauth2.hash_password(password)
    new_user = User(
        username=username, 
        email=email, 
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
    
@router.post("/login", response_model=Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not oauth2.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

# --- OAuth Endpoints ---

@router.post("/auth/google")
def google_auth(token: str, role: UserRole = UserRole.student, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired Google token")

    email = idinfo["email"]
    username = idinfo.get("name", email.split("@")[0])
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            username=username,
            email=email,
            provider="google",
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = oauth2.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/facebook")
async def facebook_auth(token: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = httpx.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,name,email",
                "access_token": token
            }
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Facebook token")
    
    fb_data = response.json()
    
    if "error" in fb_data:
        raise HTTPException(status_code=401, detail="Invalid or expired Facebook token")

    email = fb_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not available from Facebook")

    username = fb_data.get("name", email.split("@")[0])

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            username=username,
            email=email,
            provider="facebook",
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = oauth2.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/apple")
def apple_auth(token: str, db: Session = Depends(get_db)):
    response = httpx.get("https://appleid.apple.com/auth/keys")
    apple_keys = response.json()["keys"]

    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Apple token header")

    public_key = None
    for key in apple_keys:
        if key["kid"] == header["kid"]:
            public_key = key
            break

    if not public_key:
        raise HTTPException(status_code=401, detail="Apple public key not found")

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=APPLE_CLIENT_ID
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Apple token: {str(e)}")

    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not available from Apple")

    username = email.split("@")[0]

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            username=username,
            email=email,
            provider="apple",
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = oauth2.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# @router.post("/auth/google")
# def google_auth(token: str, db: Session = Depends(get_db)):
#     email = f"google_user_{token[:5]}@gmail.com"
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         user = User(username=email.split('@')[0], email=email, provider="google", role="student")
#         db.add(user)
#         db.commit()
#         db.refresh(user)
    
#     access_token = oauth2.create_access_token(data={"user_id": user.id})
#     return {"access_token": access_token, "token_type": "bearer"}

# @router.post("/auth/facebook")
# def facebook_auth(token: str, db: Session = Depends(get_db)):
#     email = f"fb_user_{token[:5]}@facebook.com"
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         user = User(username=email.split('@')[0], email=email, provider="facebook", role="student")
#         db.add(user)
#         db.commit()
#         db.refresh(user)
    
#     access_token = oauth2.create_access_token(data={"user_id": user.id})
#     return {"access_token": access_token, "token_type": "bearer"}

# @router.post("/auth/apple")
# def apple_auth(token: str, db: Session = Depends(get_db)):
#     email = f"apple_user_{token[:5]}@apple.com"
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         user = User(username=email.split('@')[0], email=email, provider="apple", role="student")
#         db.add(user)
#         db.commit()
#         db.refresh(user)
    
#     access_token = oauth2.create_access_token(data={"user_id": user.id})
#     return {"access_token": access_token, "token_type": "bearer"}

# --- User Management ---

@router.get("/me", response_model=UserResponse)
def get_current_user(current_user: User = Depends(oauth2.get_current_user)):
    return current_user

@router.get("/all_users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db), 
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    db_users = db.query(User).all()
    return db_users

@router.get("/user/{id}", response_model=UserResponse)
def user_by_id(id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/update_user/{id}", response_model=UserResponse)
def update_by_id(id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    if current_user.id != id and current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in updated_data and updated_data["password"]:
        updated_data["hashed_password"] = oauth2.hash_password(updated_data.pop("password"))

    for key, value in updated_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/delete_user/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(id: int, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    if current_user.id != id and current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return None

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist")
    
    reset_token = oauth2.create_reset_token(data={"user_email": user.email})

    msg = EmailMessage()
    msg.set_content(f"Hello, your password reset token is: {reset_token}")
    msg['Subject'] = "Password Reset Request"
    msg['From'] = "anasbenmessaoud2000@gmail.com"
    msg['To'] = request.email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('anasbenmessaoud2000@gmail.com', 'beas edue qizi uiso')
            smtp.send_message(msg)
        return {"message": "Password reset token generated and sent", "reset_token": reset_token}
    except Exception as e:
        return {"message": "Token generated but email failed to send", "reset_token": reset_token, "error": str(e)}

@router.post("/reset-password")
def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    email = oauth2.verify_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = oauth2.hash_password(request.new_password)
    user.hashed_password = hashed_password
    db.commit()
    
    return {"message": "Password has been reset successfully"}
