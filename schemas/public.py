from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ContactMessageCreate(BaseModel):
    name: str
    email: str
    subject: str
    message: str

class JobListingSchema(BaseModel):
    id: int
    title: str
    department: str
    location: str
    description: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class JobApplicationCreate(BaseModel):
    applicant_name: str
    applicant_email: str
    cover_letter: Optional[str] = None
