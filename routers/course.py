from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from modules.course import Course as CourseModel, Category as CategoryModel, Lecture as LectureModel
from modules.user import User as UserModel
from schemas.course import Course, CourseCreate, CourseListItem, Category, CategoryCreate
from oauth2 import get_current_user

router = APIRouter(
    prefix="/api/v1/courses",
    tags=["Courses"]
)

@router.get("/", response_model=List[CourseListItem])
def get_courses(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    query = db.query(CourseModel)
    
    if search:
        query = query.filter(CourseModel.title.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(CourseModel.category_id == category_id)
    if min_price is not None:
        query = query.filter(CourseModel.price >= min_price)
    if max_price is not None:
        query = query.filter(CourseModel.price <= max_price)
        
    return query.offset(skip).limit(limit).all()

@router.get("/categories", response_model=List[Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(CategoryModel).all()

@router.get("/{course_id}", response_model=Course)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/", response_model=Course)
def create_course(
    course: CourseCreate, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create courses")
    
    db_course = CourseModel(**course.dict(), instructor_id=current_user.id)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course
