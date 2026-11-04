from sqlalchemy.orm import Session
from google import genai
from google.genai import errors as genai_errors
from google.genai._gaos.lib import compat_errors as interaction_errors
from pydantic import ValidationError

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import SystemMessage, HumanMessage
import logging

from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode, Chapter, ChapterNode, StoryOption, WrongOption
from core.models import StoryLLMResponse, GeneratedChapter
from core.config import settings

logger = logging.getLogger(__name__)

class StoryGenerator:

    @classmethod
    def _get_llm(cls):
        if settings.OPENROUTER_API_KEY:
            return ChatOpenAI(
                model=settings.STORY_LLM_MODEL,
                api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                timeout=60,
                max_retries=2,
            )
        raise RuntimeError("Set OPENROUTER_API_KEY")

    @classmethod
    def _generate_gemini_chapter(cls, model: str, prompt: str) -> GeneratedChapter:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        interaction = client.interactions.create(
            model=model, input=prompt,
            response_format={"type": "text", "mime_type": "application/json",
                             "schema": GeneratedChapter.model_json_schema()},
        )
        if not interaction.output_text or interaction.output_text.strip().lower() == "null":
            raise ValueError("Model returned an empty chapter")
        return GeneratedChapter.model_validate_json(interaction.output_text)

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        generated = []
        for chapter_number in range(1, 4):
            previous = "\n\nPrevious chapters (for continuity):\n" + "\n".join(
                chapter.model_dump_json() for chapter in generated
            ) if generated else ""
            prompt = f"{STORY_PROMPT}\n\nTheme: {theme}\nChapter: {chapter_number} of 3{previous}"
            if settings.GEMINI_API_KEY:
                model_names = list(dict.fromkeys([settings.GEMINI_MODEL, "gemini-3.5-flash-lite"]))
                for index, model_name in enumerate(model_names):
                    try:
                        chapter = cls._generate_gemini_chapter(model_name, prompt)
                        break
                    except (genai_errors.APIError, interaction_errors.APIError, ValidationError, ValueError) as error:
                        if index == len(model_names) - 1:
                            raise
                        logger.warning("Story model %s failed (%s); retrying with %s", model_name, type(error).__name__, model_names[index + 1])
            else:
                parser = PydanticOutputParser(pydantic_object=GeneratedChapter)
                raw_response = cls._get_llm().invoke([SystemMessage(content=STORY_PROMPT), HumanMessage(content=prompt)])
                if not isinstance(raw_response.content, str) or raw_response.content.strip().lower() in ("", "null"):
                    raise OutputParserException("Model returned an empty chapter")
                chapter = parser.parse(raw_response.content)
            generated.append(chapter)
        story_structure = StoryLLMResponse(title=generated[0].story_title, chapters=[chapter.model_dump() for chapter in generated])

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        chapters = []
        all_nodes = []
        for chapter_index, chapter_data in enumerate(story_structure.chapters):
            chapter = Chapter(story_id=story_db.id, number=chapter_index + 1, title=chapter_data.title)
            db.add(chapter)
            db.flush()
            chapters.append(chapter)
            nodes = []
            for node_index, node_data in enumerate(chapter_data.nodes):
                is_final = chapter_index == 2 and node_index == 9
                node = StoryNode(story_id=story_db.id, content=node_data.content,
                                 is_root=chapter_index == 0 and node_index == 0,
                                 is_ending=is_final, is_winning_ending=is_final, options=[])
                db.add(node)
                db.flush()
                db.add(ChapterNode(node_id=node.id, chapter_id=chapter.id, position=node_index + 1))
                nodes.append(node)
            all_nodes.append(nodes)

        for chapter_index, chapter_data in enumerate(story_structure.chapters):
            nodes = all_nodes[chapter_index]
            for node_index, node_data in enumerate(chapter_data.nodes):
                if chapter_index == 2 and node_index == 9:
                    continue
                if node_index == 0:
                    targets = [1, 2, 3]
                elif node_index in (1, 2, 3):
                    targets = [4, 5, 6]
                elif node_index in (4, 5, 6):
                    targets = [7, 8, 7]
                elif node_index in (7, 8):
                    targets = [9, 9, 9]
                else:
                    targets = None
                for option_index, choice in enumerate(node_data.choices):
                    target = nodes[targets[option_index]] if targets is not None else all_nodes[chapter_index + 1][0]
                    option = StoryOption(node_id=nodes[node_index].id, number=option_index + 1,
                                         text=choice, next_node_id=target.id)
                    db.add(option)
                    db.flush()
                    if option_index + 1 == node_data.wrong_choice:
                        db.add(WrongOption(option_id=option.id))
        db.commit()
        return story_db
