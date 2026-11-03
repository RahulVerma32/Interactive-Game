import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.models import StoryLLMResponse
from db.database import Base
from models.job import StoryJob
from models.story import Story, StoryNode


def ending(win):
    return {"content": "An ending", "isEnding": True, "isWinningEnding": win, "options": []}


def valid_story():
    return {
        "title": "Test adventure",
        "rootNode": {
            "content": "Choose a path",
            "isEnding": False,
            "isWinningEnding": False,
            "options": [
                {"text": "Win", "nextNode": ending(True)},
                {"text": "Lose", "nextNode": ending(False)},
            ],
        },
    }


class StoryValidationTests(unittest.TestCase):
    def test_valid_tree_and_nested_choice_rules(self):
        StoryLLMResponse.model_validate(valid_story())
        invalid = valid_story()
        invalid["rootNode"]["options"][0]["nextNode"]["isEnding"] = False
        with self.assertRaises(ValidationError):
            StoryLLMResponse.model_validate(invalid)

    def test_both_endings_required(self):
        invalid = valid_story()
        invalid["rootNode"]["options"][1]["nextNode"]["isWinningEnding"] = True
        with self.assertRaises(ValidationError):
            StoryLLMResponse.model_validate(invalid)


class StoryAccessTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)

        with self.sessions() as db:
            story = Story(title="Private adventure", session_id="owner")
            db.add(story)
            db.flush()
            db.add(StoryNode(story_id=story.id, content="Start", is_root=True, is_ending=True, options=[]))
            db.add(StoryJob(job_id="job-1", session_id="owner", theme="test", status="completed", story_id=story.id))
            db.commit()
            self.story_id = story.id

    def tearDown(self):
        self.engine.dispose()

    def test_private_story_and_job(self):
        from routers.story import get_complete_story
        from routers.job import get_job_status

        with self.sessions() as db:
            with self.assertRaises(HTTPException):
                get_complete_story(self.story_id, None, db)
            with self.assertRaises(HTTPException):
                get_complete_story(self.story_id, "other", db)
            with self.assertRaises(HTTPException):
                get_job_status("job-1", "other", db)
            story = get_complete_story(self.story_id, "owner", db)
            self.assertNotIn("session_id", story.model_dump())
            self.assertEqual(get_job_status("job-1", "owner", db).job_id, "job-1")

    def test_generation_failure_is_safe(self):
        from routers.story import generate_story_task

        with self.sessions() as db:
            db.add(StoryJob(job_id="job-2", session_id="owner", theme="test", status="pending"))
            db.commit()
        with patch("routers.story.SessionLocal", self.sessions), patch(
            "routers.story.StoryGenerator.generate_story", side_effect=RuntimeError("secret API token")
        ):
            generate_story_task("job-2", "test", "owner")
        with self.sessions() as db:
            job = db.query(StoryJob).filter_by(job_id="job-2").one()
            self.assertEqual(job.status, "failed")
            self.assertNotIn("secret", job.error)


if __name__ == "__main__":
    unittest.main()
