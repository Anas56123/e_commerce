# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from database import get_db
# from modules.user import User
# from modules.course import Lecture, LectureAttachment
# from modules.interaction import LectureProgress, LectureNote, Enrollment
# from schemas.interaction import LectureNote as LectureNoteSchema, LectureNoteBase
# from schemas.course import LectureAttachment as LectureAttachmentSchema, LectureAttachmentCreate
# import oauth2
# import time
# import hashlib

# router = APIRouter(
#     prefix="/api/v1/player",
#     tags=['Video Player']
# )

# @router.get("/stream/{lecture_id}")
# def get_stream_url(lecture_id: int, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
#     lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
#     if not lecture:
#         raise HTTPException(status_code=404, detail="Lecture not found")
#         
#     enrollment = db.query(Enrollment).filter(Enrollment.user_id == current_user.id, Enrollment.course_id == lecture.course_id).first()
#     if not enrollment and current_user.role != "instructor":
#         raise HTTPException(status_code=403, detail="Not enrolled in this course")

#     # Serve signed HLS streaming URL (or fallback to dummy URL with signed query param)
#     content_url = lecture.content_url or "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8"
#     
#     expiry = int(time.time()) + 3600 # 1 hour expiry
#     secret = "hls_signing_secret_key"
#     signature = hashlib.sha256(f"{content_url}{expiry}{secret}".encode()).hexdigest()
#     
#     signed_url = f"{content_url}?expires={expiry}&signature={signature}"
#     
#     return {"url": signed_url}

# @router.post("/progress/{lecture_id}")
# def update_progress(
#     lecture_id: int, 
#     playback_position: float, 
#     completed: bool = False, 
#     db: Session = Depends(get_db), 
#     current_user: User = Depends(oauth2.get_current_user)
# ):
#     lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
#     if not lecture:
#         raise HTTPException(status_code=404, detail="Lecture not found")
#         
#     progress = db.query(LectureProgress).filter(
#         LectureProgress.user_id == current_user.id, 
#         LectureProgress.lecture_id == lecture_id
#     ).first()
#     
#     if not progress:
#         progress = LectureProgress(
#             user_id=current_user.id, 
#             lecture_id=lecture_id, 
#             playback_position=playback_position, 
#             completed=completed
#         )
#         db.add(progress)
#     else:
#         progress.playback_position = playback_position
#         if completed:
#             progress.completed = True
#             
#     db.commit()
#     db.refresh(progress)
#     return {
#         "message": "Progress updated", 
#         "playback_position": progress.playback_position, 
#         "completed": progress.completed
#     }

# @router.get("/notes/{lecture_id}", response_model=List[LectureNoteSchema])
# def get_notes(lecture_id: int, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
#     notes = db.query(LectureNote).filter(
#         LectureNote.user_id == current_user.id, 
#         LectureNote.lecture_id == lecture_id
#     ).order_by(LectureNote.timestamp.asc()).all()
#     return notes

# @router.post("/notes/{lecture_id}", response_model=LectureNoteSchema)
# def add_note(
#     lecture_id: int, 
#     note: LectureNoteBase, 
#     db: Session = Depends(get_db), 
#     current_user: User = Depends(oauth2.get_current_user)
# ):
#     new_note = LectureNote(
#         user_id=current_user.id,
#         lecture_id=lecture_id,
#         content=note.content,
#         timestamp=note.timestamp
#     )
#     db.add(new_note)
#     db.commit()
#     db.refresh(new_note)
#     return new_note

# @router.get("/attachments/{lecture_id}", response_model=List[LectureAttachmentSchema])
# def get_attachments(
#     lecture_id: int, 
#     db: Session = Depends(get_db), 
#     current_user: User = Depends(oauth2.get_current_user)
# ):
#     lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
#     if not lecture:
#         raise HTTPException(status_code=404, detail="Lecture not found")
#         
#     attachments = db.query(LectureAttachment).filter(LectureAttachment.lecture_id == lecture_id).all()
#     return attachments

# @router.post("/attachments/{lecture_id}", response_model=LectureAttachmentSchema)
# def add_attachment(
#     lecture_id: int, 
#     attachment: LectureAttachmentCreate, 
#     db: Session = Depends(get_db), 
#     current_user: User = Depends(oauth2.check_role(["instructor"]))
# ):
#     new_attachment = LectureAttachment(
#         lecture_id=lecture_id,
#         file_name=attachment.file_name,
#         file_url=attachment.file_url
#     )
#     db.add(new_attachment)
#     db.commit()
#     db.refresh(new_attachment)
#     return new_attachment
