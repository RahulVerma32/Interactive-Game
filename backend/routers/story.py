import uuid
from datetime import datetime
import logging
from openai import APITimeoutError, APIConnectionError, InternalServerError, RateLimitError, AuthenticationError
from google.genai import errors as genai_errors
from google.genai._gaos.lib import compat_errors as interaction_errors
from pydantic import ValidationError
from langchain_core.exceptions import OutputParserException
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from db.database import get_db, SessionLocal
from models.story import Story, StoryNode, Chapter, ChapterNode, StoryOption, Playthrough, ChoiceHistory, WrongOption, PlaythroughHearts
from models.job import StoryJob
from schemas.story import (
    CompleteStoryResponse, CompleteStoryNodeResponse, CreateStoryRequest, StorySummary, ChoiceRequest, ProgressRequest
)
from schemas.job import StoryJobResponse
from core.story_generator import StoryGenerator
from core.config import settings
from core.auth import current_user

router = APIRouter(
    prefix="/stories",
    tags=["stories"]
)
logger = logging.getLogger(__name__)


def generation_error_message(error: Exception) -> str:
    if isinstance(error, (interaction_errors.APIConnectionError, interaction_errors.APITimeoutError)):
        return "The AI model did not respond in time. Try again later."
    if isinstance(error, (genai_errors.APIError, interaction_errors.APIError)):
        status = getattr(error, "status_code", None) or getattr(error, "code", None)
        if status in (401, 403):
            return "The Gemini API key was rejected. Check GEMINI_API_KEY."
        if status == 429:
            return "The AI model rate limit was reached. Try again later."
        if status is not None and status >= 500:
            return "The AI model is temporarily busy. Try again later."
        return "The Gemini request failed. Check the model name and API key."
    if isinstance(error, AuthenticationError):
        return "The Gemini API key was rejected. Check GEMINI_API_KEY."
    if isinstance(error, RateLimitError):
        return "The AI model rate limit was reached. Try again later."
    if isinstance(error, (APITimeoutError, APIConnectionError)):
        return "The AI model did not respond in time. Try again later."
    if isinstance(error, InternalServerError):
        return "The AI model is temporarily busy. Try again later."
    if isinstance(error, (OutputParserException, ValidationError, ValueError)):
        return "The AI returned an invalid story. Try again."
    return "Story generation failed. Please try again."

@router.post("/create", response_model=StoryJobResponse)
def create_story(
        request: CreateStoryRequest,
        background_tasks: BackgroundTasks,
        response: Response,
        session_id: str = Depends(current_user),
        db: Session = Depends(get_db)
):
    if not (settings.GEMINI_API_KEY or settings.OPENROUTER_API_KEY):
        raise HTTPException(
            status_code=503,
            detail="Story generation is not configured. Set GEMINI_API_KEY in backend/.env.",
        )
    job_id = str(uuid.uuid4())

    job = StoryJob(
        job_id=job_id,
        session_id=session_id,
        theme=request.theme,
        status="pending"
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(
        generate_story_task,
        job_id=job_id,
        theme=request.theme,
        session_id=session_id
    )

    return job

def generate_story_task(job_id: str, theme: str, session_id: str):
    db = SessionLocal()

    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()

        if not job:
            return

        try:
            job.status = "processing"
            db.commit()

            story = StoryGenerator.generate_story(db, session_id, theme)

            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
        except Exception as error:
            db.rollback()
            logger.exception("Story generation failed for job %s", job_id)
            job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = generation_error_message(error)
            db.commit()
    finally:
        db.close()


@router.get("", response_model=list[StorySummary])
def list_stories(session_id: str = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Story).filter(Story.session_id == session_id).order_by(Story.created_at.desc(), Story.id.desc()).all()


@router.get("/{story_id}/complete", response_model=CompleteStoryResponse)
def get_complete_story(story_id: int, session_id: str = Depends(current_user), db: Session = Depends(get_db)):
    if not session_id:
        raise HTTPException(status_code=404, detail="Story not found")
    story = db.query(Story).filter(Story.id == story_id, Story.session_id == session_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    complete_story = build_complete_story_tree(db, story)
    progress = db.query(Playthrough).filter_by(story_id=story.id, session_id=session_id).first()
    complete_story.current_node_id = progress.current_node_id if progress else complete_story.root_node.id
    complete_story.progress_version = progress.version if progress else 0
    heart_state = db.get(PlaythroughHearts, progress.id) if progress else None
    complete_story.hearts = heart_state.hearts if heart_state else 3
    return complete_story



@router.get("/{story_id}/current", response_model=CompleteStoryResponse)
def get_current_chapter(story_id: int, session_id: str = Depends(current_user), db: Session = Depends(get_db)):
    story = owned_story(db, story_id, session_id)
    progress = db.query(Playthrough).filter_by(story_id=story.id, session_id=session_id).first()
    root = db.query(StoryNode).filter_by(story_id=story.id, is_root=True).first()
    if not root:
        raise HTTPException(status_code=500, detail="Story root node not found")
    current_id = progress.current_node_id if progress else root.id
    chapter_node = db.get(ChapterNode, current_id)
    if chapter_node is None:
        # Older stories have no chapter records.
        return get_complete_story(story_id, session_id, db)
    chapter = db.get(Chapter, chapter_node.chapter_id)
    if not chapter or chapter.story_id != story.id:
        raise HTTPException(status_code=500, detail="Invalid story progress")
    nodes = db.query(StoryNode).join(ChapterNode, StoryNode.id == ChapterNode.node_id).filter(
        ChapterNode.chapter_id == chapter.id, StoryNode.story_id == story.id).all()
    node_ids = [node.id for node in nodes]
    options = db.query(StoryOption).filter(StoryOption.node_id.in_(node_ids)).order_by(StoryOption.number).all()
    by_node = {}
    for option in options:
        by_node.setdefault(option.node_id, []).append({"id": option.id, "number": option.number,
                                                     "text": option.text, "node_id": option.next_node_id})
    node_dict = {node.id: CompleteStoryNodeResponse(id=node.id, content=node.content, is_ending=node.is_ending,
                 is_winning_ending=node.is_winning_ending, options=by_node.get(node.id, node.options or []),
                 chapter_number=chapter.number, chapter_title=chapter.title) for node in nodes}
    if current_id not in node_dict:
        raise HTTPException(status_code=500, detail="Invalid story progress")
    heart_state = db.get(PlaythroughHearts, progress.id) if progress else None
    return CompleteStoryResponse(id=story.id, title=story.title, created_at=story.created_at,
                                 root_node=node_dict[current_id], all_nodes=node_dict,
                                 current_node_id=current_id, progress_version=progress.version if progress else 0,
                                 hearts=heart_state.hearts if heart_state else 3)


def build_complete_story_tree(db: Session, story: Story) -> CompleteStoryResponse:
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()

    node_dict = {}
    options = db.query(StoryOption).join(StoryNode, StoryOption.node_id == StoryNode.id).filter(StoryNode.story_id == story.id).order_by(StoryOption.number).all()
    options_by_node = {}
    for option in options:
        options_by_node.setdefault(option.node_id, []).append({"id": option.id, "number": option.number, "text": option.text, "node_id": option.next_node_id})
    chapter_rows = db.query(ChapterNode, Chapter).join(Chapter, ChapterNode.chapter_id == Chapter.id).filter(Chapter.story_id == story.id).all()
    chapters_by_node = {entry.node_id: chapter for entry, chapter in chapter_rows}
    for node in nodes:
        node_response = CompleteStoryNodeResponse(
            id=node.id,
            content=node.content,
            is_ending=node.is_ending,
            is_winning_ending=node.is_winning_ending,
            options=options_by_node.get(node.id, node.options or []),
            chapter_number=chapters_by_node[node.id].number if node.id in chapters_by_node else None,
            chapter_title=chapters_by_node[node.id].title if node.id in chapters_by_node else None,
        )
        node_dict[node.id] = node_response

    root_node = next((node for node in nodes if node.is_root), None)
    if not root_node:
        raise HTTPException(status_code=500, detail="Story root node not found")

    return CompleteStoryResponse(
        id=story.id,
        title= story.title,
        created_at=story.created_at,
        root_node=node_dict[root_node.id],
        all_nodes=node_dict
    )


def owned_story(db, story_id, session_id):
    story = db.query(Story).filter_by(id=story_id, session_id=session_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


def advance_progress(db, story, session_id, node_id, version):
    progress = db.query(Playthrough).filter_by(story_id=story.id, session_id=session_id).first()
    if not progress:
        root = db.query(StoryNode).filter_by(story_id=story.id, is_root=True).first()
        if not root:
            raise HTTPException(status_code=500, detail="Story root node not found")
        if version != 0:
            raise HTTPException(status_code=409, detail="Progress changed. Reload the story.")
        progress = Playthrough(story_id=story.id, session_id=session_id, current_node_id=root.id, version=0)
        db.add(progress)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Progress changed. Reload the story.")
    result = db.execute(update(Playthrough).where(Playthrough.id == progress.id, Playthrough.version == version)
                        .values(current_node_id=node_id, version=version + 1))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Progress changed. Reload the story.")
    return progress.id


@router.post("/{story_id}/choice")
def choose_option(story_id: int, request: ChoiceRequest, session_id: str = Depends(current_user), db: Session = Depends(get_db)):
    story = owned_story(db, story_id, session_id)
    progress = db.query(Playthrough).filter_by(story_id=story.id, session_id=session_id).first()
    root = db.query(StoryNode).filter_by(story_id=story.id, is_root=True).first()
    current_id = progress.current_node_id if progress else root.id if root else None
    if current_id != request.node_id:
        raise HTTPException(status_code=409, detail="Progress changed. Reload the story.")
    node = db.query(StoryNode).filter_by(id=current_id, story_id=story.id).first()
    if not node or node.is_ending:
        raise HTTPException(status_code=400, detail="No choices are available.")
    option = db.query(StoryOption).filter_by(node_id=node.id, number=request.option_number).first()
    if option:
        target_id = option.next_node_id
    elif not db.query(StoryOption).filter_by(node_id=node.id).first() and 1 <= request.option_number <= len(node.options or []):
        target_id = node.options[request.option_number - 1].get("node_id")
    else:
        raise HTTPException(status_code=400, detail="Invalid choice.")
    if not db.query(StoryNode).filter_by(id=target_id, story_id=story.id).first():
        raise HTTPException(status_code=400, detail="Invalid choice destination.")
    wrong = bool(option and db.get(WrongOption, option.id))
    heart_state = db.get(PlaythroughHearts, progress.id) if progress else None
    hearts = heart_state.hearts if heart_state else 3
    reset_to_checkpoint = False
    if wrong:
        hearts -= 1
        target_id = node.id
        if hearts == 0:
            chapter_node = db.get(ChapterNode, node.id)
            checkpoint = (db.query(ChapterNode).filter_by(chapter_id=chapter_node.chapter_id, position=1).first()
                          if chapter_node else None)
            target_id = checkpoint.node_id if checkpoint else root.id
            hearts = 3
            reset_to_checkpoint = True
    progress_id = advance_progress(db, story, session_id, target_id, request.version)
    if heart_state:
        heart_state.hearts = hearts
    else:
        db.add(PlaythroughHearts(playthrough_id=progress_id, hearts=hearts))
    db.add(ChoiceHistory(playthrough_id=progress_id, node_id=node.id, option_id=option.id if option else None, option_number=request.option_number))
    db.commit()
    return {"current_node_id": target_id, "version": request.version + 1, "hearts": hearts,
            "wrong": wrong, "reset_to_checkpoint": reset_to_checkpoint}



def restart_progress(db, story, session_id, target_id, version):
    """Restart saved progress and restore hearts atomically."""
    progress_id = advance_progress(db, story, session_id, target_id, version)
    heart_state = db.get(PlaythroughHearts, progress_id)
    if heart_state:
        heart_state.hearts = 3
    else:
        db.add(PlaythroughHearts(playthrough_id=progress_id, hearts=3))
    db.commit()
    return {"current_node_id": target_id, "version": version + 1, "hearts": 3}


@router.post("/{story_id}/restart")
def restart_story(story_id: int, request: ProgressRequest, session_id: str = Depends(current_user), db: Session = Depends(get_db)):
    story = owned_story(db, story_id, session_id)
    root = db.query(StoryNode).filter_by(story_id=story.id, is_root=True).first()
    if not root:
        raise HTTPException(status_code=500, detail="Story root node not found")
    return restart_progress(db, story, session_id, root.id, request.version)
