# Handle passing user token after validating password hash, password resets,
# etc.
import asyncio
import random
import json
from typing import Annotated

import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

router = APIRouter(
    prefix="/questions",
    tags=["users", "questions"],
)

GROQ_MCQ_QUERY = """
You need to generate four multiple choice answers for the question {question}.
The answer to the question is {answer}.
You are generating these questions for another person who has just met the person that this questionnaire is about, so you should ensure that the answers are something that the guessing person could guess.
The person's name is {name}. Change the questions to be about {name} instead of second person.
Generate three wrong answers and one correct answer.
You will need to return a json object with the following format for example:
```json
{{
    "question_text": "What is Jeremy's favourite video game?",
    "answer_texts": [
        {{
            "id": 0,
            "answer_text": "Fortnite"
        }},
        {{
            "id": 1,
            "answer_text": "Counter-Strike"
        }},
        {{
            "id": 2,
            "answer_text": "Call of Duty"
        }},
        {{
            "id": 3,
            "answer_text": "Valorant"
        }}
    ]
}}
```
Where id is 0-indexed.
You must put the correct answer at index {answer_index} and the wrong answers at the other indexes.
You may make the three other wrong answers similar to the correct answer to make it harder but it must be clear that they are wrong.
Do note include ``` code blocks in the response.
Do note say ANYTHING ELSE in the response either, must only be the json content.
"""

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


def hash_string_to_int(_string: str) -> int:
    """
    Hash a string to an integer using SHA-256.
    """
    return int(hashlib.sha256(_string.encode()).hexdigest(), 16)

def get_unique_answer_seq(id_1: str, id_2: str) -> list[int]:
    """
    Generate a sequence 3 unique numbers from 0 to 3.
    The sequence will be used to generate the answer options for the MCQ.

    Will be consistent for the same two users.

    args:
        id_1: The UUID of the first user.
        id_2: The UUID of the first user.
    """
    seed = hash_string_to_int(id_1 + id_2) % 1000000
    random.seed(seed)

    seq = random.sample(range(4), 3)

    return seq

class UserQuestionnaireAnswer(BaseModel):
    id: int
    answerText: str

class UserQuestionnaireMCQ(BaseModel):
    id: int
    questionText: str
    options: list[UserQuestionnaireAnswer]

@router.get("/mcq/generate/{user_id}")
async def generate_mcq(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    user_id: str
) -> list[UserQuestionnaireMCQ]:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    other_user = UserDto.model_validate(await user_collection.find_one({UserRef.ID: user_id}))
    
    if not user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    answer_seq = get_unique_answer_seq(user.id, other_user.id)

    groq_prompts = []
    question_ids = []
    for i, question in enumerate(other_user.questions):
        id = question.id
        question_text = QUESTIONS[id]
        answer_text = question.answer

        question_ids.append(id)
        groq_prompts.append(
            {
                "role": "user",
                "content": GROQ_MCQ_QUERY.format(
                    question=question_text,
                    answer=answer_text,
                    answer_index=answer_seq[i],
                    name=other_user.name,
                ),
            }
        )

    tasks = [config.groq.chat.completions.create(
        messages=[prompt],
        model="gemma2-9b-it",
    ) for prompt in groq_prompts]
    responses = await asyncio.gather(*tasks)

    questions_answers = []
    for id, groq_response in zip(question_ids, responses):
        if not groq_response.choices[0]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate MCQ from Groq.",
            )
        
        try:
            options = json.loads(groq_response.choices[0].message.content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse MCQ from Groq.",
            ) from e

        question_text = options["question_text"]

        questions_answers.append(
            UserQuestionnaireMCQ(
                id=id,
                questionText=question_text,
                options=[
                    UserQuestionnaireAnswer(
                        id=option["id"],
                        answerText=option["answer_text"],
                    )
                    for option in options["answer_texts"]
                ],
            )
        )

    return questions_answers


@router.post("/mcq/validate/{user_id}")
async def validate_mcq(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    user_id: str,
    answers: list[int],
) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    other_user = UserDto.model_validate(await user_collection.find_one({UserRef.ID: user_id}))
    
    if not user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    correct_answer_seq = get_unique_answer_seq(user.id, other_user.id)

    correct_count = 0
    for answer, correct_answer in zip(answers, correct_answer_seq):
        if answer == correct_answer:
            correct_count += 1
    
    user.points += correct_count
    await user_collection.update_one(
        {UserRef.ID: user.id},
        {"$set": {UserRef.POINTS: user.points}},
    )

    return {"correct_count": correct_count}
