from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from modules.user import User
from modules.course import Course
from modules.interaction import CourseReview, Enrollment
from schemas.interaction import CourseReview as CourseReviewSchema, CourseReviewBase
import oauth2

router = APIRouter(
    prefix="/api/v1/reviews",
    tags=['Course Reviews']
)

@router.get("/{course_id}", response_model=List[CourseReviewSchema])
def get_reviews(course_id: int, db: Session = Depends(get_db)):
    reviews = db.query(CourseReview).filter(CourseReview.course_id == course_id).all()
    return reviews

@router.post("/{course_id}", response_model=CourseReviewSchema)
def add_review(course_id: int, review: CourseReviewBase, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    enrollment = db.query(Enrollment).filter(Enrollment.user_id == current_user.id, Enrollment.course_id == course_id).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="You must be enrolled in the course to leave a review")
        
    existing_review = db.query(CourseReview).filter(CourseReview.user_id == current_user.id, CourseReview.course_id == course_id).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this course")
        
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
    new_review = CourseReview(
        user_id=current_user.id,
        course_id=course_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review
