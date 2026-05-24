from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
import datetime

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    subject = Column(String)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class JobListing(Base):
    __tablename__ = "job_listings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    department = Column(String)
    location = Column(String)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class JobApplication(Base):
    __tablename__ = "job_applications"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer)
    applicant_name = Column(String)
    applicant_email = Column(String)
    resume_url = Column(String)
    cover_letter = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
