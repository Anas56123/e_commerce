from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from database import get_db
from modules.course import Course as CourseModel
from modules.interaction import CartItem as CartItemModel, WishlistItem as WishlistItemModel, Coupon as CouponModel, Enrollment as EnrollmentModel, Purchase as PurchaseModel
from modules.user import User as UserModel
from schemas.interaction import CartItem, WishlistItem, Enrollment, Purchase, Settings
from oauth2 import get_current_user
from typing import List, Optional
import stripe #type:ignore

settings = Settings()
stripe.api_key = settings.stripe_secret_key

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

    line_items = []
    course_ids = []
    
    for item in cart_items:
        course = db.query(CourseModel).filter(CourseModel.id == item.course_id).first()
        if not course:
            continue
            
        final_price = course.price * (1 - discount)
        course_ids.append(str(course.id))
        
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": course.title,
                },
                "unit_amount": int(final_price * 100),
            },
            "quantity": 1,
        })
        
    if not line_items:
        raise HTTPException(status_code=400, detail="No valid courses in cart")
        
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=settings.domain + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.domain + '/cancel',
            client_reference_id=str(current_user.id),
            metadata={
                "course_ids": ",".join(course_ids)
            }
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        user_id = int(session.get('client_reference_id'))
        metadata = session.get('metadata', {})
        course_ids_str = metadata.get('course_ids', '')
        if not course_ids_str:
            return {"status": "success"}
            
        course_ids = [int(cid) for cid in course_ids_str.split(',')]
        
        # Calculate amount per course for purchase record
        total_amount = session.get('amount_total', 0) / 100.0
        amount_per_course = total_amount / len(course_ids) if course_ids else 0
        
        for course_id in course_ids:
            # Check if already enrolled
            existing_enrollment = db.query(EnrollmentModel).filter(
                EnrollmentModel.user_id == user_id,
                EnrollmentModel.course_id == course_id
            ).first()
            
            if not existing_enrollment:
                new_enrollment = EnrollmentModel(user_id=user_id, course_id=course_id)
                db.add(new_enrollment)
                
                new_purchase = PurchaseModel(
                    user_id=user_id,
                    course_id=course_id,
                    amount=amount_per_course
                )
                db.add(new_purchase)
                
            # Remove from cart
            cart_item = db.query(CartItemModel).filter(
                CartItemModel.user_id == user_id,
                CartItemModel.course_id == course_id
            ).first()
            if cart_item:
                db.delete(cart_item)
                
        db.commit()

    return {"status": "success"}
