from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class StoryOptionLLM(BaseModel):
    text: str = Field(min_length=1, description="the text of the option shown to the user")
    nextNode: StoryNodeLLM = Field(description="the next node content and its options")


class StoryNodeLLM(BaseModel):
    content: str = Field(min_length=1, description="The main content of the story node")
    isEnding: bool = Field(description="Whether this node is an ending node")
    isWinningEnding: bool = Field(description="Whether this node is a winning ending node")
    options: list[StoryOptionLLM] = Field(default_factory=list, description="The options for this node")

    @model_validator(mode="after")
    def validate_choices(self):
        if self.isEnding and self.options:
            raise ValueError("Ending nodes cannot have choices")
        if not self.isEnding and not 2 <= len(self.options) <= 3:
            raise ValueError("Non-ending nodes must have 2 or 3 choices")
        if self.isWinningEnding and not self.isEnding:
            raise ValueError("Only endings can be winning endings")
        return self


class StoryLLMResponse(BaseModel):
    title: str = Field(min_length=1, description="The title of the story")
    rootNode: StoryNodeLLM = Field(description="The root node of the story")

    @model_validator(mode="after")
    def validate_endings(self):
        endings = []

        def visit(node: StoryNodeLLM):
            if node.isEnding:
                endings.append(node.isWinningEnding)
            for option in node.options:
                visit(option.nextNode)

        visit(self.rootNode)
        if True not in endings or False not in endings:
            raise ValueError("Story must have both winning and losing endings")
        return self


StoryOptionLLM.model_rebuild()
