# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""Questionnaire related SQLAlchemy models.

These models store available sports and teams as well as user
preferences. They are separated from the main ``database`` module to
keep concerns modular while still sharing the same SQLAlchemy ``Base``.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pydantic import BaseModel

from .database import Base


class SportRankingRequest(BaseModel):
    """Request model for updating sport rankings."""

    sport_rankings: list[str]



class TeamPreferenceRequest(BaseModel):
    """Request model for a single team preference."""

    team_id: str
    interest_level: int


class FavoriteTeamsRequest(BaseModel):
    """Request model for saving favorite teams."""

    team_selections: list[TeamPreferenceRequest]


class UserQuestionnaireStatus(BaseModel):
    """Simple questionnaire status representation used in tests."""

    user_id: str
    is_completed: bool
    current_step: int


class Sport(Base):
    """Represents a sport that users can select."""

    __tablename__ = "sports"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    has_teams = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    teams = relationship("Team", back_populates="sport")


class Team(Base):
    """Represents a team within a specific sport."""

    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    sport_id = Column(UUID(as_uuid=True), ForeignKey("sports.id"), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    league = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sport = relationship("Sport", back_populates="teams")
    preferences = relationship("UserTeamPreference", back_populates="team")


class UserSportPreference(Base):
    """User's interest level in a sport."""

    __tablename__ = "user_sport_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(String(255), nullable=False, index=True)
    sport_id = Column(UUID(as_uuid=True), ForeignKey("sports.id"), nullable=False, index=True)
    interest_level = Column(Integer, nullable=False)
    preference_order = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sport = relationship("Sport")


class UserTeamPreference(Base):
    """User's interest level in a team."""

    __tablename__ = "user_team_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(String(255), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True)
    interest_level = Column(Integer, nullable=False)
    preference_order = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    team = relationship("Team", back_populates="preferences")


__all__ = [
    "Sport",
    "Team",
    "UserSportPreference",
    "UserTeamPreference",
    "SportRankingRequest",
    "FavoriteTeamsRequest",
    "UserQuestionnaireStatus",
]
