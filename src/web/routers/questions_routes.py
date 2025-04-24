# Handle passing user token after validating password hash, password resets,
# etc.

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/questions",
    tags=["users", "questions"],
)

QUESTIONS = [
    {
        "id": 1,
        "questionText": "Do you like to play games?",
    },
    {
        "id": 2,
        "questionText": "What is your full legal name?",
    },
    {
        "id": 3,
        "questionText": "What are the front numbers of your credit card?",
    },
    {
        "id": 4,
        "questionText": "What are the back numbers of your credit card?",
    },
]



class QuestionDto(BaseModel):
    id: int
    questionText: str

@router.get("/")
async def get_questions() -> list[QuestionDto]:
    return QUESTIONS
