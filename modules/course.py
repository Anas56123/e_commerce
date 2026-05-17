from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    courses = relationship("Course", back_populates="category")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    thumbnail = Column(String, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    status = Column(String, default="draft")
    difficulty = Column(String, nullable=True)
    requirements = Column(Text, nullable=True)
    learning_objectives = Column(Text, nullable=True)

    category = relationship("Category", back_populates="courses")
    lectures = relationship("Lecture", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course")
    sections = relationship("Section", back_populates="course", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    order = Column(Integer)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="sections")
    lectures = relationship("Lecture", back_populates="section", cascade="all, delete-orphan")

class Lecture(Base):
    __tablename__ = "lectures"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content_url = Column(String, nullable=True) # URL to video or text content
    order = Column(Integer)
    course_id = Column(Integer, ForeignKey("courses.id"))
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    
    # New fields for advanced curriculum builder
    # video_status = Column(String, default="pending") # pending, processing, ready, failed
    # captions_url = Column(String, nullable=True)

    course = relationship("Course", back_populates="lectures")
    section = relationship("Section", back_populates="lectures")
    progress = relationship("LectureProgress", back_populates="lecture")
    # attachments = relationship("LectureAttachment", back_populates="lecture", cascade="all, delete-orphan")

# class LectureAttachment(Base):
#     __tablename__ = "lecture_attachments"
#     id = Column(Integer, primary_key=True, index=True)
#     lecture_id = Column(Integer, ForeignKey("lectures.id"))
#     file_name = Column(String)
#     file_url = Column(String)
#     
#     lecture = relationship("Lecture", back_populates="attachments")
