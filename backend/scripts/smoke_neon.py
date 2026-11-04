"""Check that the running API serves migrated Neon data without leaking sessions."""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from db.database import SessionLocal, engine
from models.job import StoryJob
from models.story import Story


def main():
    if engine.dialect.name != "postgresql":
        raise RuntimeError("This check requires the Neon PostgreSQL connection")

    with SessionLocal() as db:
        story = db.query(Story).order_by(Story.id).first()
        if story is None:
            raise RuntimeError("No story in Neon to check")
        story_id, session_id = story.id, story.session_id
        job = db.query(StoryJob).filter(StoryJob.story_id == story_id).first()
        job_id = job.job_id if job else None

    base = "http://127.0.0.1:8000/api"
    story_url = f"{base}/stories/{story_id}/complete"
    with urlopen(Request(story_url, headers={"Cookie": f"session_id={session_id}"})) as response:
        story_data = json.load(response)
        assert response.status == 200
    assert story_data["id"] == story_id
    assert story_data["all_nodes"]
    assert "session_id" not in story_data
    print(f"story HTTP: 200; id: {story_id}; nodes: {len(story_data['all_nodes'])}")

    try:
        urlopen(story_url)
    except HTTPError as error:
        assert error.code == 404
        print("story without session HTTP: 404")
    else:
        raise AssertionError("Story was accessible without the owner session")

    if job_id:
        with urlopen(Request(f"{base}/jobs/{job_id}", headers={"Cookie": f"session_id={session_id}"})) as response:
            assert response.status == 200
            assert json.load(response)["job_id"] == job_id
        print("job HTTP: 200")


if __name__ == "__main__":
    main()
