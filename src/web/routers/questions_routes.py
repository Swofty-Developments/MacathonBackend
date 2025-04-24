# Handle passing user token after validating password hash, password resets,
# etc.
import random

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/questions",
    tags=["users", "questions"],
)

# Changing the order of these questions will also change the order of the
# question IDs... so don't change their order.
QUESTIONS = [
    "What course are you studying?",
    "What's your favourite TV Show?",
    "Do you play any sports?",
    "Do you play any video games?",
    "What's your type?",
    "What's your spice tolerance?",
    "What's your best pickup line?",
    "What's your biggest ick?",
    "What's a green flag you look for?",
    "What's a red flag you avoid?",
    "What's your love language?",
    "What's your number 1 artist?",
    "What's your favourite cuisine?",
    "What's your favourite way to spend a day off?",
    "What's your favourite unit at Monash?",
]

questions_with_id = [
    {
        "id": i,
        "questionText": question,
    }
    for i, question in enumerate(QUESTIONS)
]


class QuestionDto(BaseModel):
    id: int
    questionText: str


@router.get("/")
async def get_questions() -> list[QuestionDto]:
    return random.sample(questions_with_id, 3)
