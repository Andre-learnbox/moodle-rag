from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class Home(BaseModel):
    title: str = "MOODLE RAG CHAT API"
    description: str = "API for the MOODLE RAG CHAT project"
    docs_url: str = "/docs"

class Health(BaseModel):
    status: str

@router.get("/", response_model=Home)
def index():
    return Home()

@router.get("/health", response_model=Health)
def health():
    return Health(status="ok")

# Add /query endpoint
class Query(BaseModel):
    message: str
    course_id: Optional[str] = None
    usercontext: Optional[str] = "Dashboard"

@router.post("/query", response_model=dict)
def query(input: Query):
    """
    Handles user queries for Moodle RAG CHAT.
    """
    if not input.message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Example response, replace with your business logic
    response = {
        "message": input.message,
        "course_id": input.course_id,
        "usercontext": input.usercontext,
        "response": "This is a simulated response"
    }
    return response
