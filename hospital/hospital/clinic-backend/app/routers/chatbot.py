from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatQuery(BaseModel):
    query: str

@router.post("/query")
async def chatbot_query(body: ChatQuery, current_user: User = Depends(get_current_user)):
    """مساعد طبي — متاح لكل المستخدمين المسجلين (مريض، طبيب، أدمن)"""
    return {
        "message": f"أهلاً {current_user.full_name}، استلمنا سؤالك: '{body.query}'. هذه الخاصية قيد التطوير وستعمل بالذكاء الاصطناعي قريباً."
    }
