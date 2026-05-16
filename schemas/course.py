from pydantic import BaseModel
from typing import List, Optional

class CategoryBase(BaseModel):
    name: str
    slug: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    class Config:
        from_attributes = True

class LectureBase(BaseModel):
    title: str
    content_url: str
    order: int

class LectureCreate(LectureBase):
    course_id: int

class Lecture(LectureBase):
    id: int
    course_id: int
    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    title: str
    description: str
    price: float
    thumbnail: Optional[str] = None
    category_id: int

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    instructor_id: int
    category: Category
    lectures: List[Lecture] = []
    class Config:
        from_attributes = True

class CourseListItem(BaseModel):
    id: int
    title: str
    price: float
    thumbnail: Optional[str] = None
    category: Category
    class Config:
        from_attributes = True
