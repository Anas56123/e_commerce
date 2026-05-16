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
    
    category = relationship("Category", back_populates="courses")
    lectures = relationship("Lecture", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course")

class Lecture(Base):
    __tablename__ = "lectures"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content_url = Column(String) # URL to video or text content
    order = Column(Integer)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="lectures")
    progress = relationship("LectureProgress", back_populates="lecture")
