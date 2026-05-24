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

class LectureAttachmentBase(BaseModel):
    file_name: str
    file_url: str

class LectureAttachmentCreate(LectureAttachmentBase):
    lecture_id: int

class LectureAttachment(LectureAttachmentBase):
    id: int
    lecture_id: int
    class Config:
        from_attributes = True



class Lecture(LectureBase):
    id: int
    course_id: int
    section_id: Optional[int] = None
    video_status: str = "pending"
    captions_url: Optional[str] = None
    attachments: List[LectureAttachment] = []
    class Config:
        from_attributes = True

class SectionBase(BaseModel):
    title: str
    order: int

class SectionCreate(SectionBase):
    course_id: int

class Section(SectionBase):
    id: int
    course_id: int
    lectures: List[Lecture] = []
    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    title: str
    description: str
    price: float
    thumbnail: Optional[str] = None
    category_id: int
    status: Optional[str] = "draft"
    difficulty: Optional[str] = None
    requirements: Optional[str] = None
    learning_objectives: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    instructor_id: int
    category: Category
    lectures: List[Lecture] = []
    sections: List[Section] = []
    class Config:
        from_attributes = True

class CourseListItem(BaseModel):
    id: int
    title: str
    price: float
    thumbnail: Optional[str] = None
    category: Category
    status: str
    difficulty: Optional[str] = None
    class Config:
        from_attributes = True
