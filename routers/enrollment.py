from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from modules.course import Course as CourseModel, Lecture as LectureModel
from modules.interaction import Enrollment as EnrollmentModel, LectureProgress as ProgressModel
from modules.user import User as UserModel
from schemas.interaction import Enrollment, LectureProgress
from oauth2 import get_current_user
from typing import List

router = APIRouter(
    prefix="/api/v1/enrollments",
    tags=["Enrollments"]
)

@router.post("/{course_id}", response_model=Enrollment)
def enroll_in_course(
    course_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Check if already enrolled
    existing = db.query(EnrollmentModel).filter(
        EnrollmentModel.user_id == current_user.id,
        EnrollmentModel.course_id == course_id
    ).first()
    if existing:
        return existing
    
    # Check if course exists
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_enrollment = EnrollmentModel(user_id=current_user.id, course_id=course_id)
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

@router.get("/my-courses", response_model=List[Enrollment])
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return db.query(EnrollmentModel).filter(EnrollmentModel.user_id == current_user.id).all()

@router.post("/progress/{lecture_id}")
def mark_lecture_complete(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Check if lecture exists
    lecture = db.query(LectureModel).filter(LectureModel.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    # Check if enrolled in the course
    enrollment = db.query(EnrollmentModel).filter(
        EnrollmentModel.user_id == current_user.id,
        EnrollmentModel.course_id == lecture.course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    
    # Update or create progress
    progress = db.query(ProgressModel).filter(
        ProgressModel.user_id == current_user.id,
        ProgressModel.lecture_id == lecture_id
    ).first()
    
    if not progress:
        progress = ProgressModel(user_id=current_user.id, lecture_id=lecture_id, completed=True)
        db.add(progress)
    else:
        progress.completed = True
    
    db.commit()
    
    # Update overall course progress
    total_lectures = db.query(LectureModel).filter(LectureModel.course_id == lecture.course_id).count()
    completed_lectures = db.query(ProgressModel).join(LectureModel).filter(
        ProgressModel.user_id == current_user.id,
        LectureModel.course_id == lecture.course_id,
        ProgressModel.completed == True
    ).count()
    
    if total_lectures > 0:
        enrollment.progress_percentage = (completed_lectures / total_lectures) * 100
        if enrollment.progress_percentage == 100:
            enrollment.completed = True
    
    db.commit()
    return {"message": "Progress updated", "progress_percentage": enrollment.progress_percentage}
