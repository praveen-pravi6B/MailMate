from pydantic import BaseModel, Field
from typing import Optional

class CalendarTask(BaseModel):
    create: bool = Field(default=False, description="Whether to create a calendar task")
    title: Optional[str] = Field(None, description="Title of the task")
    date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Due time in HH:MM format")
    confidence: float = Field(0.0, description="Confidence score from 0.0 to 1.0")

class AIResponse(BaseModel):
    summary: str = Field(description="Short summary of the email")
    importance: str = Field(description="Importance level: low, medium, or high")
    action_required: bool = Field(description="Whether the user needs to take action")
    calendar: CalendarTask = Field(default_factory=CalendarTask, description="Calendar recommendation")
    email_url: Optional[str] = Field(None, description="Link to open the source email")
