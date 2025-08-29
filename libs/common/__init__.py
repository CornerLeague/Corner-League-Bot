# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""Common utilities and shared components for the sports media platform."""

__version__ = "1.0.0"

from .database import get_db
from .questionnaire_models import Sport, Team, UserSportPreference, UserTeamPreference

__all__ = [
    "__version__",
    "get_db",
    "Sport",
    "Team",
    "UserSportPreference",
    "UserTeamPreference",
]

