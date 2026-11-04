from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.database import Base


class Story(Base):
    __tablename__ = "stories"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    session_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    nodes = relationship("StoryNode", back_populates="story")


class StoryNode(Base):
    __tablename__ = "story_nodes"
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), index=True)
    content = Column(String)
    is_root = Column(Boolean, default=False)
    is_ending = Column(Boolean, default=False)
    is_winning_ending = Column(Boolean, default=False)
    options = Column(JSON, default=list)  # Legacy stories
    story = relationship("Story", back_populates="nodes")


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("story_id", "number"),)
    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)


class ChapterNode(Base):
    __tablename__ = "chapter_nodes"
    __table_args__ = (UniqueConstraint("chapter_id", "position"),)
    node_id = Column(Integer, ForeignKey("story_nodes.id"), primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)


class StoryOption(Base):
    __tablename__ = "story_options"
    __table_args__ = (UniqueConstraint("node_id", "number"), CheckConstraint("number BETWEEN 1 AND 3"))
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("story_nodes.id"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    next_node_id = Column(Integer, ForeignKey("story_nodes.id"), nullable=False)


class Playthrough(Base):
    __tablename__ = "playthroughs"
    __table_args__ = (UniqueConstraint("story_id", "session_id"),)
    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    current_node_id = Column(Integer, ForeignKey("story_nodes.id"), nullable=False)
    version = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChoiceHistory(Base):
    __tablename__ = "choice_history"
    id = Column(Integer, primary_key=True)
    playthrough_id = Column(Integer, ForeignKey("playthroughs.id"), nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("story_nodes.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("story_options.id"), nullable=True)
    option_number = Column(Integer, nullable=False)
    chosen_at = Column(DateTime(timezone=True), server_default=func.now())


class WrongOption(Base):
    __tablename__ = "wrong_options"
    option_id = Column(Integer, ForeignKey("story_options.id"), primary_key=True)


class PlaythroughHearts(Base):
    __tablename__ = "playthrough_hearts"
    __table_args__ = (CheckConstraint("hearts BETWEEN 1 AND 3"),)
    playthrough_id = Column(Integer, ForeignKey("playthroughs.id"), primary_key=True)
    hearts = Column(Integer, nullable=False, default=3)
