from pydantic import BaseModel, Field, model_validator


class StorySceneLLM(BaseModel):
    content: str = Field(min_length=10)
    choices: list[str] = Field(min_length=3, max_length=3)
    wrong_choice: int = Field(ge=1, le=3)


class ChapterLLM(BaseModel):
    title: str = Field(min_length=1)
    nodes: list[StorySceneLLM] = Field(min_length=10, max_length=10)


class GeneratedChapter(BaseModel):
    story_title: str = Field(min_length=3)
    title: str = Field(min_length=1)
    nodes: list[StorySceneLLM] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def validate_choices(self):
        if any(len(choice.strip()) < 3 for node in self.nodes for choice in node.choices):
            raise ValueError("Choices must contain at least three characters")
        return self


class StoryLLMResponse(BaseModel):
    title: str = Field(min_length=3)
    chapters: list[ChapterLLM] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_choices(self):
        if any(len(choice.strip()) < 3 for chapter in self.chapters for node in chapter.nodes for choice in node.choices):
            raise ValueError("Choices must contain at least three characters")
        return self
