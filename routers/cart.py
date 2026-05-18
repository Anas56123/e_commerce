from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from modules.course import Course as CourseModel
from modules.interaction import CartItem as CartItemModel, WishlistItem as WishlistItemModel, Coupon as CouponModel, Enrollment as EnrollmentModel, Purchase as PurchaseModel
from modules.user import User as UserModel
from schemas.interaction import CartItem, WishlistItem, Enrollment, Purchase
from oauth2 import get_current_user
from typing import List, Optional

router = APIRouter(
    prefix="/api/v1/cart",
    tags=["Shopping Cart"]
)

@router.get("/", response_model=List[CartItem])
def get_cart(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return db.query(CartItemModel).filter(CartItemModel.user_id == current_user.id).all()

@router.post("/add/{course_id}")
def add_to_cart(course_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    existing = db.query(CartItemModel).filter(
        CartItemModel.user_id == current_user.id,
        CartItemModel.course_id == course_id
    ).first()
    if existing:
        return {"message": "Already in cart"}
    
    new_item = CartItemModel(user_id=current_user.id, course_id=course_id)
    db.add(new_item)
    db.commit()
    return {"message": "Added to cart"}

@router.delete("/remove/{course_id}")
def remove_from_cart(course_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    item = db.query(CartItemModel).filter(
        CartItemModel.user_id == current_user.id,
        CartItemModel.course_id == course_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    db.delete(item)
    db.commit()
    return {"message": "Removed from cart"}

@router.post("/wishlist/{course_id}")
def move_to_wishlist(course_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    cart_item = db.query(CartItemModel).filter(
        CartItemModel.user_id == current_user.id,
        CartItemModel.course_id == course_id
    ).first()
    if cart_item:
        db.delete(cart_item)
    
    existing = db.query(WishlistItemModel).filter(
        WishlistItemModel.user_id == current_user.id,
        WishlistItemModel.course_id == course_id
    ).first()
    if not existing:
        new_wish = WishlistItemModel(user_id=current_user.id, course_id=course_id)
        db.add(new_wish)
    
    db.commit()
    return {"message": "Moved to wishlist"}

@router.get("/wishlist", response_model=List[WishlistItem])
def get_wishlist(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return db.query(WishlistItemModel).filter(WishlistItemModel.user_id == current_user.id).all()

@router.get("/purchases", response_model=List[Purchase])
def get_purchases(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return db.query(PurchaseModel).filter(PurchaseModel.user_id == current_user.id).order_by(PurchaseModel.purchased_at.desc()).all()

@router.post("/checkout")
def checkout(coupon_code: Optional[str] = None, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    cart_items = db.query(CartItemModel).filter(CartItemModel.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    discount = 0.0
    if coupon_code:
        coupon = db.query(CouponModel).filter(CouponModel.code == coupon_code, CouponModel.is_active == True).first()
        if coupon:
            discount = coupon.discount_percent / 100.0

    enrollments = []
    for item in cart_items:
        course = db.query(CourseModel).filter(CourseModel.id == item.course_id).first()
        if not course:
            continue
            
        final_price = course.price * (1 - discount)
        
        existing_enrollment = db.query(EnrollmentModel).filter(
            EnrollmentModel.user_id == current_user.id,
            EnrollmentModel.course_id == item.course_id
        ).first()
        
        if not existing_enrollment:
            new_enrollment = EnrollmentModel(user_id=current_user.id, course_id=item.course_id)
            db.add(new_enrollment)
            enrollments.append(new_enrollment)
            
            new_purchase = PurchaseModel(
                user_id=current_user.id,
                course_id=item.course_id,
                amount=final_price
            )
            db.add(new_purchase)
        
        db.delete(item)
    
    db.commit()
    return {"message": "Checkout successful", "enrolled_count": len(enrollments)}
