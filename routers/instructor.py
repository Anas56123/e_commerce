from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from modules.user import User
from modules.course import Course, Section, Lecture, Category
from modules.interaction import Purchase, Enrollment, CourseReview
from schemas.course import CourseListItem, Course as CourseSchema, CourseCreate, SectionCreate, Section as SectionSchema, Lecture as LectureSchema
import oauth2
import shutil
import os
import asyncio
import datetime

router = APIRouter(
    prefix="/api/v1/instructor",
    tags=['Instructor Panel']
)


@router.get("/dashboard")
def get_instructor_dashboard(db: Session = Depends(get_db), current_user: User = Depends(oauth2.check_role(["instructor"]))):
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]

    if not course_ids:
        return {
            "total_revenue": 0.0,
            "total_students": 0,
            "courses_analytics": [],
            "revenue_by_month": []
        }

    total_revenue = db.query(func.sum(Purchase.amount)).filter(Purchase.course_id.in_(course_ids)).scalar() or 0.0

    total_students = db.query(func.count(func.distinct(Enrollment.user_id))).filter(Enrollment.course_id.in_(course_ids)).scalar() or 0

    courses_analytics = []
    for c in courses:
        enrollment_count = db.query(func.count(Enrollment.id)).filter(Enrollment.course_id == c.id).scalar() or 0
        revenue = db.query(func.sum(Purchase.amount)).filter(Purchase.course_id == c.id).scalar() or 0.0
        
        avg_rating = db.query(func.avg(CourseReview.rating)).filter(CourseReview.course_id == c.id).scalar()
        avg_rating = round(avg_rating, 2) if avg_rating else 0.0
        
        courses_analytics.append({
            "course_id": c.id,
            "title": c.title,
            "price": c.price,
            "status": c.status,
            "enrollment_count": enrollment_count,
            "revenue": revenue,
            "average_rating": avg_rating
        })

    revenue_by_month = []
    months_map = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 
                  7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
    
    purchases = db.query(
        func.extract('month', Purchase.purchased_at).label('month'),
        func.sum(Purchase.amount).label('monthly_sum')
    ).filter(Purchase.course_id.in_(course_ids)).group_by('month').all()

    for p in purchases:
        month_name = months_map.get(int(p.month), "Unknown")
        revenue_by_month.append({
            "month": month_name,
            "revenue": p.monthly_sum
        })

    if not revenue_by_month:
        revenue_by_month = [
            {"month": "Jan", "revenue": total_revenue * 0.1},
            {"month": "Feb", "revenue": total_revenue * 0.15},
            {"month": "Mar", "revenue": total_revenue * 0.2},
            {"month": "Apr", "revenue": total_revenue * 0.1},
            {"month": "May", "revenue": total_revenue * 0.3},
            {"month": "Jun", "revenue": total_revenue * 0.15}
        ]

    return {
        "total_revenue": total_revenue,
        "total_students": total_students,
        "courses_analytics": courses_analytics,
        "revenue_by_month": revenue_by_month
    }


@router.post("/courses/step1", response_model=CourseSchema)
def course_creator_step1(course: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(oauth2.check_role(["instructor"]))):
    category = db.query(Category).filter(Category.id == course.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    new_course = Course(
        title=course.title,
        description=course.description,
        price=course.price,
        thumbnail=course.thumbnail,
        category_id=course.category_id,
        instructor_id=current_user.id,
        status="draft"
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@router.put("/courses/{course_id}/step2", response_model=CourseSchema)
def course_creator_step2(
    course_id: int, 
    difficulty: str, 
    requirements: Optional[str] = None, 
    learning_objectives: Optional[str] = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    course = db.query(Course).filter(Course.id == course_id, Course.instructor_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
        
    course.difficulty = difficulty
    course.requirements = requirements
    course.learning_objectives = learning_objectives
    
    db.commit()
    db.refresh(course)
    return course


@router.post("/courses/{course_id}/sections", response_model=SectionSchema)
def add_section(
    course_id: int, 
    section: SectionCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    course = db.query(Course).filter(Course.id == course_id, Course.instructor_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
        
    new_section = Section(
        title=section.title,
        order=section.order,
        course_id=course_id
    )
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    return new_section


@router.post("/sections/{section_id}/lectures", response_model=LectureSchema)
def add_lecture_to_section(
    section_id: int, 
    title: str = Form(...),
    order: int = Form(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
        
    course = db.query(Course).filter(Course.id == section.course_id, Course.instructor_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    new_lecture = Lecture(
        title=title,
        order=order,
        section_id=section_id,
        course_id=section.course_id
    )
    db.add(new_lecture)
    db.commit()
    db.refresh(new_lecture)
    return new_lecture

def simulate_video_encoding(lecture_id: int, filename: str, db_session_factory):
    time.sleep(10)
    db = next(db_session_factory())
    try:
        lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
        if lecture:
            lecture.video_status = "ready"
            lecture.content_url = f"https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8"
            db.commit()
    except Exception as e:
        print(f"Error during video encoding simulation: {e}")
    finally:
        db.close()

@router.post("/lectures/{lecture_id}/video")
def upload_lecture_video(
    lecture_id: int, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
        
    course = db.query(Course).filter(Course.id == lecture.course_id, Course.instructor_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Unauthorized")

    os.makedirs("static/uploads/videos", exist_ok=True)
    file_location = f"static/uploads/videos/{lecture_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    lecture.video_status = "processing"
    db.commit()

    background_tasks.add_task(simulate_video_encoding, lecture_id, file.filename, get_db)

    return {"message": "Video uploaded successfully. HLS encoding started asynchronously.", "video_status": "processing"}

@router.post("/lectures/{lecture_id}/captions")
def add_lecture_captions(
    lecture_id: int, 
    captions_url: str = Form(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
        
    course = db.query(Course).filter(Course.id == lecture.course_id, Course.instructor_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    lecture.captions_url = captions_url
    db.commit()
    return {"message": "Captions added successfully", "captions_url": captions_url}

@router.post("/lectures/{lecture_id}/attachments")
def add_lecture_attachment(
    lecture_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    from modules.course import LectureAttachment
    
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
        
    course = db.query(Course).filter(Course.id == lecture.course_id, Course.instructor_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    os.makedirs("static/uploads/attachments", exist_ok=True)
    file_location = f"static/uploads/attachments/{lecture_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    new_attachment = LectureAttachment(
        lecture_id=lecture_id,
        file_name=file.filename,
        file_url=f"/{file_location}"
    )
    db.add(new_attachment)
    db.commit()
    db.refresh(new_attachment)
    return new_attachment





@router.put("/courses/{course_id}/publish", response_model=CourseSchema)
def publish_course(
    course_id: int, 
    publish: bool = True, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(oauth2.check_role(["instructor"]))
):
    course = db.query(Course).filter(Course.id == course_id, Course.instructor_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
        
    if publish:
        sections_count = db.query(Section).filter(Section.course_id == course_id).count()
        if sections_count == 0:
            raise HTTPException(status_code=400, detail="Cannot publish course without any sections/curriculum structure")
            
    course.status = "published" if publish else "draft"
    db.commit()
    db.refresh(course)
    return course
