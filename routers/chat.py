from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from database import get_db, SessionLocal
from modules.messaging import Message
from modules.user import User
from schemas.messaging import Message as MessageSchema
from oauth2 import get_current_user, verify_access_token
import json

router = APIRouter(
    prefix="/api/v1/chat",
    tags=['Chat']
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, receiver_id: int):
        websocket = self.active_connections.get(receiver_id)
        if websocket:
            await websocket.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    db = SessionLocal()
    try:
        try:
            token_data = verify_access_token(token)
            user = db.query(User).filter(User.id == token_data.id).first()
        except HTTPException:
            user = None

        if not user:
            await websocket.close(code=1008)
            return
            
        await manager.connect(websocket, user.id)
        
        try:
            while True:
                data = await websocket.receive_text()
                payload = json.loads(data)
                receiver_id = payload.get("receiver_id")
                content = payload.get("content")
                
                if receiver_id and content:
                    new_msg = Message(
                        sender_id=user.id,
                        receiver_id=receiver_id,
                        content=content
                    )
                    db.add(new_msg)
                    db.commit()
                    db.refresh(new_msg)
                    
                    message_data = json.dumps({
                        "sender_id": user.id,
                        "content": content,
                        "timestamp": str(new_msg.timestamp)
                    })
                    await manager.send_personal_message(message_data, receiver_id)
        except WebSocketDisconnect:
            manager.disconnect(user.id)
    finally:
        db.close()

@router.get("/history/{contact_id}", response_model=List[MessageSchema])
def get_chat_history(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(Message).filter(
        (Message.sender_id == current_user.id) & (Message.receiver_id == contact_id) |
        (Message.sender_id == contact_id) & (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()
    return messages
