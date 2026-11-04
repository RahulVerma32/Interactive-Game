from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel


class StoryOptionsSchema(BaseModel):
    id: Optional[int] = None
    number: Optional[int] = None
    text: str
    node_id: Optional[int] = None


class StoryNodeBase(BaseModel):
    content: str
    is_ending: bool = False
    is_winning_ending: bool = False


class CompleteStoryNodeResponse(StoryNodeBase):
    id: int
    chapter_number: Optional[int] = None
    chapter_title: Optional[str] = None
    options: List[StoryOptionsSchema] = []

    class Config:
        from_attributes = True


class StoryBase(BaseModel):
    title: str

    class Config:
        from_attributes = True


class CreateStoryRequest(BaseModel):
    theme: str


class CompleteStoryResponse(StoryBase):
    id: int
    created_at: datetime
    root_node: CompleteStoryNodeResponse
    all_nodes: Dict[int, CompleteStoryNodeResponse]
    current_node_id: Optional[int] = None
    progress_version: int = 0
    hearts: int = 3

    class Config:
        from_attributes = True


class StorySummary(StoryBase):
    id: int
    created_at: datetime


class ChoiceRequest(BaseModel):
    node_id: int
    option_number: int
    version: int


class ProgressRequest(BaseModel):
    version: int
