# app/models/thread.py
from pydantic import BaseModel
from typing import List

class ThreadCreateRequest(BaseModel):
    household_id: str

class ThreadResponse(BaseModel):
    threadId: str
    participants: List[str]
    created_at: str
    updated_at: str

class ThreadListResponse(BaseModel):
    threads: List[ThreadResponse]
