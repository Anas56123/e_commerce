from sqlalchemy import Column, Integer, ForeignKey, Boolean, String, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrolled_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed = Column(Boolean, default=False)
    progress_percentage = Column(Float, default=0.0)

    course = relationship("Course", back_populates="enrollments")

class LectureProgress(Base):
    __tablename__ = "lecture_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lecture_id = Column(Integer, ForeignKey("lectures.id"))
    completed = Column(Boolean, default=False)
    playback_position = Column(Float, default=0.0)

    lecture = relationship("Lecture", back_populates="progress")

class LectureNote(Base):
    __tablename__ = "lecture_notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lecture_id = Column(Integer, ForeignKey("lectures.id"))
    content = Column(String)
    timestamp = Column(Float, default=0.0) # Timestamp in the video where the note was taken
    created_at = Column(DateTime, default=datetime.datetime.utcnow)



class CourseReview(Base):
    __tablename__ = "course_reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    rating = Column(Integer) # 1 to 5
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    discount_percent = Column(Float)
    expiry_date = Column(DateTime)
    is_active = Column(Boolean, default=True)

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    amount = Column(Float)
    purchased_at = Column(DateTime, default=datetime.datetime.utcnow)
