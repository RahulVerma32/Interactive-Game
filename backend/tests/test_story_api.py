import unittest
from unittest.mock import patch, MagicMock
import json
import httpx

from fastapi import HTTPException, BackgroundTasks, Response
from pydantic import ValidationError
from google.genai._gaos.lib import compat_errors as interaction_errors
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.models import StoryLLMResponse, GeneratedChapter
from core.config import settings
from core.story_generator import StoryGenerator
from db.database import Base, database_url
from models.job import StoryJob
from models.story import Story, StoryNode, Chapter, ChapterNode, StoryOption, Playthrough, ChoiceHistory
from schemas.story import CreateStoryRequest


def valid_story():
    return {
        "title": "Test adventure",
        "chapters": [{"title": f"Chapter {chapter}", "nodes": [
            {"content": f"Scene number {number} opens the next challenge.",
             "choices": ["Take the path", "Ask for help", "Look for clues"], "wrong_choice": 3}
            for number in range(10)]} for chapter in range(3)]
    }


def valid_chapter(number=0):
    return GeneratedChapter(story_title="Test adventure", **valid_story()["chapters"][number])


class StoryValidationTests(unittest.TestCase):
    def test_three_chapters_and_ten_nodes_required(self):
        StoryLLMResponse.model_validate(valid_story())
        invalid = valid_story()
        invalid["chapters"][0]["nodes"].pop()
        with self.assertRaises(ValidationError):
            StoryLLMResponse.model_validate(invalid)
        invalid = valid_story()
        invalid["chapters"].pop()
        with self.assertRaises(ValidationError):
            StoryLLMResponse.model_validate(invalid)

    def test_three_nonempty_choices_required(self):
        invalid = valid_story()
        invalid["chapters"][1]["nodes"][1]["choices"][0] = ""
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

    def test_history_only_includes_the_current_users_stories(self):
        from routers.story import list_stories

        with self.sessions() as db:
            db.add(Story(title="Another user's story", session_id="other"))
            db.commit()
            stories = list_stories("owner", db)
            self.assertEqual([story.title for story in stories], ["Private adventure"])
            self.assertEqual(list_stories("nobody", db), [])

    def test_hearts_persist_and_reset_at_chapter_checkpoint(self):
        from routers.story import get_complete_story, get_current_chapter, choose_option, restart_story
        from schemas.story import ChoiceRequest, ProgressRequest
        with self.sessions() as db, patch.object(settings, "GEMINI_API_KEY", "test-key"), patch.object(StoryGenerator, "_generate_gemini_chapter", return_value=valid_chapter()):
            story = StoryGenerator.generate_story(db, "owner", "test")
            loaded = get_complete_story(story.id, "owner", db)
            current, version = loaded.root_node.id, 0
            for expected in (2, 1):
                result = choose_option(story.id, ChoiceRequest(node_id=current, option_number=3, version=version), "owner", db)
                version = result["version"]
                self.assertEqual(result["hearts"], expected)
                self.assertEqual(get_complete_story(story.id, "owner", db).hearts, expected)
                self.assertEqual(result["current_node_id"], current)
            result = choose_option(story.id, ChoiceRequest(node_id=current, option_number=3, version=version), "owner", db)
            self.assertTrue(result["reset_to_checkpoint"])
            self.assertEqual((result["hearts"], result["current_node_id"]), (3, current))
            version = result["version"]
            for _ in range(5):
                result = choose_option(story.id, ChoiceRequest(node_id=current, option_number=1, version=version), "owner", db)
                current, version = result["current_node_id"], result["version"]
            chapter = get_current_chapter(story.id, "owner", db)
            self.assertEqual(chapter.all_nodes[current].chapter_number, 2)
            self.assertEqual(len(chapter.all_nodes), 10)
            self.assertNotIn(loaded.root_node.id, chapter.all_nodes)
            with self.assertRaises(HTTPException):
                get_current_chapter(story.id, "other", db)
            chapter_start = current
            result = choose_option(story.id, ChoiceRequest(node_id=current, option_number=1, version=version), "owner", db)
            current, version = result["current_node_id"], result["version"]
            for _ in range(3):
                result = choose_option(story.id, ChoiceRequest(node_id=current, option_number=3, version=version), "owner", db)
                current, version = result["current_node_id"], result["version"]
            self.assertTrue(result["reset_to_checkpoint"])
            self.assertEqual((current, result["hearts"]), (chapter_start, 3))
            result = choose_option(story.id, ChoiceRequest(node_id=current, option_number=1, version=version), "owner", db)
            version = result["version"]
            self.assertIsNotNone(db.get(Story, story.id))
            restart_story(story.id, ProgressRequest(version=version), "owner", db)
            self.assertEqual(get_complete_story(story.id, "owner", db).hearts, 3)

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

    def test_missing_model_key_rejects_job_before_database_write(self):
        from routers.story import create_story

        with self.sessions() as db, patch.object(settings, "GEMINI_API_KEY", None), patch.object(settings, "OPENROUTER_API_KEY", None):
            before = db.query(StoryJob).count()
            with self.assertRaises(HTTPException) as error:
                create_story(CreateStoryRequest(theme="test"), BackgroundTasks(), Response(), "owner", db)
            self.assertEqual(error.exception.status_code, 503)
            self.assertEqual(db.query(StoryJob).count(), before)

    def test_model_uses_openrouter_instead_of_retired_github_endpoint(self):
        with patch.object(settings, "GEMINI_API_KEY", None), patch.object(settings, "OPENROUTER_API_KEY", "test-key"):
            llm = StoryGenerator._get_llm()
        self.assertEqual(llm.model_name, settings.STORY_LLM_MODEL)
        self.assertEqual(llm.openai_api_base, "https://openrouter.ai/api/v1")

    def test_gemini_key_takes_priority(self):
        client = MagicMock()
        client.interactions.create.return_value.output_text = valid_chapter().model_dump_json()
        with patch.object(settings, "GEMINI_API_KEY", "test-key"), patch.object(settings, "OPENROUTER_API_KEY", "other-key"), patch("core.story_generator.genai.Client", return_value=client) as make_client:
            story = StoryGenerator._generate_gemini_chapter(settings.GEMINI_MODEL, "Theme: fantasy")
        self.assertEqual(story.story_title, "Test adventure")
        make_client.assert_called_once_with(api_key="test-key")
        request = client.interactions.create.call_args.kwargs
        self.assertEqual(request["model"], settings.GEMINI_MODEL)
        self.assertIn("Theme: fantasy", request["input"])
        self.assertEqual(request["response_format"]["mime_type"], "application/json")
        self.assertEqual(request["response_format"]["schema"], GeneratedChapter.model_json_schema())

    def test_empty_primary_response_falls_back_and_saves_story(self):
        with self.sessions() as db, patch.object(settings, "GEMINI_API_KEY", "test-key"), patch.object(settings, "GEMINI_MODEL", "gemini-3.8-flash"), patch.object(StoryGenerator, "_generate_gemini_chapter", side_effect=[ValueError("empty"), valid_chapter(0), valid_chapter(1), valid_chapter(2)]) as generate:
            story = StoryGenerator.generate_story(db, "owner", "test")
            self.assertEqual(story.title, "Test adventure")
            nodes = db.query(StoryNode).filter_by(story_id=story.id).all()
            self.assertEqual(len(nodes), 30)
            self.assertEqual(db.query(Chapter).filter_by(story_id=story.id).count(), 3)
            self.assertEqual(db.query(ChapterNode).count(), 30)
            self.assertEqual(db.query(StoryOption).count(), 87)
            from routers.story import get_complete_story, get_current_chapter, choose_option, restart_story
            from schemas.story import ChoiceRequest, ProgressRequest
            loaded = get_complete_story(story.id, "owner", db)
            root = loaded.root_node
            self.assertEqual(root.chapter_number, 1)
            self.assertEqual(len(root.options), 3)
            self.assertEqual(len(get_current_chapter(story.id, "owner", db).all_nodes), 10)
            self.assertEqual(generate.call_count, 4)
            self.assertIn('Chapter: 2 of 3', generate.call_args_list[2].args[1])
            self.assertIn('Previous chapters', generate.call_args_list[2].args[1])
            choice = ChoiceRequest(node_id=root.id, option_number=1, version=0)
            result = choose_option(story.id, choice, "owner", db)
            self.assertEqual(get_complete_story(story.id, "owner", db).current_node_id, result["current_node_id"])
            with self.assertRaises(HTTPException) as error:
                choose_option(story.id, choice, "owner", db)
            self.assertEqual(error.exception.status_code, 409)
            with self.assertRaises(HTTPException):
                get_complete_story(story.id, "other", db)
            self.assertEqual(db.query(ChoiceHistory).count(), 1)
            restart_story(story.id, ProgressRequest(version=1), "owner", db)
            self.assertEqual(get_complete_story(story.id, "owner", db).current_node_id, root.id)
            self.assertEqual(generate.call_args_list[1].args[0], "gemini-3.5-flash-lite")

    def test_story_makes_one_request_per_chapter_and_failure_saves_nothing(self):
        with self.sessions() as db, patch.object(settings, "GEMINI_API_KEY", "test-key"), patch.object(StoryGenerator, "_generate_gemini_chapter", side_effect=[valid_chapter(0), valid_chapter(1), valid_chapter(2)]) as generate:
            StoryGenerator.generate_story(db, "owner", "fantasy")
            self.assertEqual(generate.call_count, 3)
            self.assertIn("Chapter: 3 of 3", generate.call_args_list[2].args[1])
            self.assertIn("Chapter 1", generate.call_args_list[2].args[1])
            count = db.query(Story).count()
        with self.sessions() as db, patch.object(settings, "GEMINI_API_KEY", "test-key"), patch.object(StoryGenerator, "_generate_gemini_chapter", side_effect=[valid_chapter(0), ValueError("bad"), ValueError("bad")]):
            with self.assertRaises(ValueError):
                StoryGenerator.generate_story(db, "owner", "fantasy")
            self.assertEqual(db.query(Story).count(), count)

    def test_busy_gemini_model_retries_with_flash_lite(self):
        request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/interactions")
        busy = interaction_errors.InternalServerError(
            "Model is busy", response=httpx.Response(503, request=request), body={}
        )
        with self.sessions() as db, patch.object(settings, "GEMINI_API_KEY", "test-key"), patch.object(settings, "GEMINI_MODEL", "gemini-3.8-flash"), patch.object(StoryGenerator, "_generate_gemini_chapter", side_effect=[busy, valid_chapter(0), valid_chapter(1), valid_chapter(2)]) as generate:
            StoryGenerator.generate_story(db, "owner", "test")
        self.assertEqual(generate.call_count, 4)
        self.assertEqual(generate.call_args_list[1].args[0], "gemini-3.5-flash-lite")


class DatabaseMigrationTests(unittest.TestCase):
    def test_neon_url_enforces_ssl(self):
        url = database_url("postgres://user:pass@ep-example-pooler.eu.aws.neon.tech/neondb")
        self.assertEqual(url.drivername, "postgresql+psycopg2")
        self.assertEqual(url.query["sslmode"], "require")

    def test_copy_preserves_ids_and_refuses_existing_target(self):
        from scripts.migrate_sqlite_to_postgres import copy_records

        source = create_engine("sqlite://")
        target = create_engine("sqlite://")
        try:
            Base.metadata.create_all(source)
            with sessionmaker(bind=source)() as db:
                db.add(Story(id=42, title="Saved", session_id="owner"))
                db.add(StoryNode(id=77, story_id=42, content="End", is_root=True, is_ending=True, options=[]))
                db.commit()
            self.assertEqual(copy_records(source, target)["stories"], 1)
            with sessionmaker(bind=target)() as db:
                self.assertEqual(db.get(StoryNode, 77).story_id, 42)
            with self.assertRaises(ValueError):
                copy_records(source, target)
        finally:
            source.dispose()
            target.dispose()


if __name__ == "__main__":
    unittest.main()
