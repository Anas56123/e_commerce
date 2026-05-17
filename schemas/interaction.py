from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EnrollmentBase(BaseModel):
    course_id: int

class Enrollment(EnrollmentBase):
    id: int
    user_id: int
    enrolled_at: datetime
    completed: bool
    progress_percentage: float
    class Config:
        from_attributes = True

class LectureProgressBase(BaseModel):
    lecture_id: int
    completed: bool
    # playback_position: Optional[float] = 0.0

class LectureProgress(LectureProgressBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    course_id: int

class CartItem(CartItemBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class WishlistItemBase(BaseModel):
    course_id: int

class WishlistItem(WishlistItemBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class CouponBase(BaseModel):
    code: str
    discount_percent: float
    expiry_date: datetime

class Coupon(CouponBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

class PurchaseBase(BaseModel):
    course_id: int
    amount: float

class Purchase(PurchaseBase):
    id: int
    user_id: int
    purchased_at: datetime
    class Config:
        from_attributes = True

# class LectureNoteBase(BaseModel):
#     lecture_id: int
#     content: str
#     timestamp: float

# class LectureNote(LectureNoteBase):
#     id: int
#     user_id: int
#     created_at: datetime
#     class Config:
#         from_attributes = True

class CourseReviewBase(BaseModel):
    course_id: int
    rating: int
    comment: Optional[str] = None

class CourseReview(CourseReviewBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True
