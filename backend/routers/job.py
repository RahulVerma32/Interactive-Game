from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from models.job import StoryJob
from schemas.job import StoryJobResponse
from core.auth import current_user

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)


@router.get("/{job_id}", response_model=StoryJobResponse)
def get_job_status(job_id: str, session_id: str = Depends(current_user), db: Session = Depends(get_db)):
    if not session_id:
        raise HTTPException(status_code=404, detail="Job not found")
    job = db.query(StoryJob).filter(StoryJob.job_id == job_id, StoryJob.session_id == session_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
