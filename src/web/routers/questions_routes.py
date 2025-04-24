# Handle passing user token after validating password hash, password resets,
# etc.

import logging

from fastapi import APIRouter

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


@router.get("/")
async def get_questions() -> dict:
    return QUESTIONS
