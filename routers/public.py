from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from modules.public import ContactMessage, JobListing, JobApplication
from schemas.public import ContactMessageCreate, JobListingSchema
import shutil
import os

router = APIRouter(
    prefix="/api/v1/public",
    tags=['Public Pages']
)

@router.get("/about")
def get_about_info():
    return {
        "title": "About Us",
        "description": "We are a leading e-commerce platform for online courses.",
        "mission": "Empowering learners worldwide.",
        "team": [
            {"name": "Alice", "role": "CEO"},
            {"name": "Bob", "role": "CTO"}
        ]
    }

@router.post("/contact")
def submit_contact_form(contact: ContactMessageCreate, db: Session = Depends(get_db)):
    new_msg = ContactMessage(
        name=contact.name,
        email=contact.email,
        subject=contact.subject,
        message=contact.message
    )
    db.add(new_msg)
    db.commit()
    return {"message": "Thank you for contacting us. We will get back to you shortly."}

@router.get("/careers", response_model=List[JobListingSchema])
def get_careers(db: Session = Depends(get_db)):
    return db.query(JobListing).filter(JobListing.is_active == True).all()

@router.post("/careers/{job_id}/apply")
def apply_for_job(
    job_id: int,
    applicant_name: str = Form(...),
    applicant_email: str = Form(...),
    cover_letter: Optional[str] = Form(None),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    job = db.query(JobListing).filter(JobListing.id == job_id, JobListing.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found or inactive")

    os.makedirs("static/uploads/resumes", exist_ok=True)
    file_location = f"static/uploads/resumes/{job_id}_{applicant_email}_{resume.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    application = JobApplication(
        job_id=job_id,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        resume_url=f"/{file_location}",
        cover_letter=cover_letter
    )
    db.add(application)
    db.commit()
    return {"message": "Application submitted successfully."}
