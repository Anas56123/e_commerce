from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from modules.course import Category, Course, Lecture
from modules.user import User
from modules.interaction import Coupon
import datetime

def seed():
    db = SessionLocal()
    
    # Create categories
    categories = [
        Category(name="Development", slug="development"),
        Category(name="Design", slug="design"),
        Category(name="Business", slug="business"),
        Category(name="Marketing", slug="marketing")
    ]
    for cat in categories:
        if not db.query(Category).filter(Category.slug == cat.slug).first():
            db.add(cat)
    db.commit()
    
    # Create a dummy instructor if none exists
    instructor = db.query(User).filter(User.role == "instructor").first()
    if not instructor:
        instructor = User(username="pro_teacher", email="teacher@example.com", hashed_password="hashed_password", role="instructor")
        db.add(instructor)
        db.commit()
        db.refresh(instructor)
    
    # Create courses
    dev_cat = db.query(Category).filter(Category.slug == "development").first()
    design_cat = db.query(Category).filter(Category.slug == "design").first()
    
    courses = [
        Course(
            title="Mastering FastAPI", 
            description="Learn how to build high-performance APIs with Python and FastAPI.", 
            price=49.99, 
            category_id=dev_cat.id, 
            instructor_id=instructor.id,
            thumbnail="https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&q=80&w=1000"
        ),
        Course(
            title="UI/UX Design Masterclass", 
            description="Master the art of creating beautiful and functional user interfaces.", 
            price=59.99, 
            category_id=design_cat.id, 
            instructor_id=instructor.id,
            thumbnail="https://images.unsplash.com/photo-1561070791-2526d30994b5?auto=format&fit=crop&q=80&w=1000"
        ),
        Course(
            title="Advanced React Patterns", 
            description="Deep dive into React hooks, performance, and scalable architecture.", 
            price=79.99, 
            category_id=dev_cat.id, 
            instructor_id=instructor.id,
            thumbnail="https://images.unsplash.com/photo-1633356122544-f134324a6cee?auto=format&fit=crop&q=80&w=1000"
        )
    ]
    
    for c in courses:
        if not db.query(Course).filter(Course.title == c.title).first():
            db.add(c)
            db.commit()
            db.refresh(c)
            
            # Add some lectures
            for i in range(1, 4):
                lecture = Lecture(
                    title=f"Lesson {i}: Getting Started with {c.title}",
                    content_url=f"https://example.com/lecture/{i}",
                    order=i,
                    course_id=c.id
                )
                db.add(lecture)
    
    # Create a coupon
    if not db.query(Coupon).filter(Coupon.code == "SAVE20").first():
        coupon = Coupon(
            code="SAVE20",
            discount_percent=20.0,
            expiry_date=datetime.datetime.utcnow() + datetime.timedelta(days=30)
        )
        db.add(coupon)
    
    db.commit()
    db.close()
    print("Database seeded!")

if __name__ == "__main__":
    seed()
