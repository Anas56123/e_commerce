from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
from modules.user import User
from modules.interaction import Purchase
from modules.course import Course
from modules.earning import PayoutMethod, WithdrawalRequest
from schemas.earning import PayoutMethod as PayoutMethodSchema, PayoutMethodCreate, WithdrawalRequest as WithdrawalRequestSchema, WithdrawalRequestCreate
import oauth2

router = APIRouter(
    prefix="/api/v1/earnings",
    tags=['Earnings']
)

@router.get("/balance")
def get_balance(db: Session = Depends(get_db), current_user: User = Depends(oauth2.check_role(["instructor"]))):
    # Calculate 80% of revenue
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]
    
    total_revenue = db.query(func.sum(Purchase.amount)).filter(Purchase.course_id.in_(course_ids)).scalar() or 0.0
    instructor_share = total_revenue * 0.8
    
    # Calculate withdrawn amount
    withdrawn = db.query(func.sum(WithdrawalRequest.amount)).filter(
        WithdrawalRequest.user_id == current_user.id,
        WithdrawalRequest.status.in_(["approved", "paid", "pending"])
    ).scalar() or 0.0
    
    available_balance = instructor_share - withdrawn
    
    return {
        "total_earnings": instructor_share,
        "withdrawn": withdrawn,
        "available_balance": available_balance
    }

@router.get("/payout-methods", response_model=List[PayoutMethodSchema])
def get_payout_methods(db: Session = Depends(get_db), current_user: User = Depends(oauth2.check_role(["instructor"]))):
    return db.query(PayoutMethod).filter(PayoutMethod.user_id == current_user.id).all()

@router.post("/payout-methods", response_model=PayoutMethodSchema)
def add_payout_method(method: PayoutMethodCreate, db: Session = Depends(get_db), current_user: User = Depends(oauth2.check_role(["instructor"]))):
    if method.is_default == 1:
        # Unset others
        db.query(PayoutMethod).filter(PayoutMethod.user_id == current_user.id).update({"is_default": 0})
        
    new_method = PayoutMethod(
        user_id=current_user.id,
        provider=method.provider,
        account_id=method.account_id,
        is_default=method.is_default
    )
    db.add(new_method)
    db.commit()
    db.refresh(new_method)
    return new_method

@router.post("/withdraw", response_model=WithdrawalRequestSchema)
def request_withdrawal(req: WithdrawalRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(oauth2.check_role(["instructor"]))):
    # Check balance
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]
    total_revenue = db.query(func.sum(Purchase.amount)).filter(Purchase.course_id.in_(course_ids)).scalar() or 0.0
    instructor_share = total_revenue * 0.8
    
    withdrawn = db.query(func.sum(WithdrawalRequest.amount)).filter(
        WithdrawalRequest.user_id == current_user.id,
        WithdrawalRequest.status.in_(["approved", "paid", "pending"])
    ).scalar() or 0.0
    
    available_balance = instructor_share - withdrawn
    
    if req.amount > available_balance:
        raise HTTPException(status_code=400, detail="Insufficient funds")
        
    payout_method = db.query(PayoutMethod).filter(PayoutMethod.user_id == current_user.id).first()
    if not payout_method:
        raise HTTPException(status_code=400, detail="No payout method configured")
        
    withdrawal = WithdrawalRequest(
        user_id=current_user.id,
        amount=req.amount,
        status="pending"
    )
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    return withdrawal

@router.get("/withdrawals", response_model=List[WithdrawalRequestSchema])
def get_withdrawals(db: Session = Depends(get_db), current_user: User = Depends(oauth2.check_role(["instructor"]))):
    return db.query(WithdrawalRequest).filter(WithdrawalRequest.user_id == current_user.id).all()
