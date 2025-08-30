"""Unit tests for questionnaire routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from apps.api.questionnaire_routes import (
    get_available_sports,
    get_teams_by_sport,
    get_user_preferences,
    save_team_preferences,
    update_sport_ranking,
)
from libs.common.questionnaire_models import (
    Sport,
    SportRankingRequest,
    Team,
    TeamPreferenceRequest,
    UserQuestionnaireStatus,
    UserSportPreference,
    UserTeamPreference,
)


class TestQuestionnaireRoutes:
    """Test cases for questionnaire API routes."""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager with session."""
        db_manager = MagicMock()
        mock_session = AsyncMock()
        db_manager.session.return_value.__aenter__.return_value = mock_session
        return db_manager, mock_session

    @pytest.fixture
    def sample_sports(self):
        """Sample sports data for testing."""
        return [
            Sport(id="1", name="Basketball", slug="basketball", is_active=True, has_teams=True, display_order=1),
            Sport(id="2", name="Football", slug="football", is_active=True, has_teams=True, display_order=2)
        ]

    @pytest.fixture
    def sample_teams(self):
        """Sample teams data for testing."""
        return [
            Team(id="1", name="Lakers", sport_id="1", slug="lakers", city="Los Angeles"),
            Team(id="2", name="Warriors", sport_id="1", slug="warriors", city="Golden State")
        ]

    async def test_get_available_sports_success(self, mock_db_manager, sample_sports):
        """Test successful retrieval of available sports."""
        _, mock_session = mock_db_manager

        # Mock the SQLAlchemy result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_sports
        mock_session.execute.return_value = mock_result

        # Execute
        result = await get_available_sports(mock_session)

        # Assert
        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0]["name"] == "Basketball"
        mock_session.execute.assert_called_once()

    async def test_get_available_sports_error(self, mock_db_manager):
        """Test error handling in get_available_sports."""
        db_manager, mock_session = mock_db_manager

        # Mock database error
        mock_session.execute.side_effect = Exception("Database error")

        # Execute and assert exception
        with pytest.raises(HTTPException) as exc_info:
            await get_available_sports(db_manager)

        assert exc_info.value.status_code == 500
        assert "Failed to get sports list" in str(exc_info.value.detail)

    async def test_get_teams_by_sport_success(self, mock_db_manager, sample_teams):
        """Test successful retrieval of teams by sport."""
        db_manager, mock_session = mock_db_manager
        sport_id = "1"

        # Mock sport lookup
        mock_sport = Sport(id="1", name="Basketball", slug="basketball", is_active=True, has_teams=True)
        mock_sport_result = MagicMock()
        mock_sport_result.scalar_one_or_none.return_value = mock_sport

        # Mock teams lookup
        mock_teams_result = MagicMock()
        mock_teams_result.scalars.return_value.all.return_value = sample_teams

        mock_session.execute.side_effect = [mock_sport_result, mock_teams_result]

        # Execute
        result = await get_teams_by_sport(sport_id, db_manager)

        # Assert
        assert len(result.teams) == 2
        assert result.sport_id == sport_id
        assert result.sport_name == "Basketball"
        assert result.total_count == 2

    async def test_get_teams_by_sport_not_found(self, mock_db_manager):
        """Test get_teams_by_sport with non-existent sport."""
        db_manager, mock_session = mock_db_manager

        # Mock sport not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute and assert exception
        with pytest.raises(HTTPException) as exc_info:
            await get_teams_by_sport("nonexistent", db_manager)

        assert exc_info.value.status_code == 404

    async def test_update_sport_ranking_success(self, mock_db_manager):
        """Test successful sport ranking update."""
        db_manager, mock_session = mock_db_manager

        # Mock request and user
        mock_request = MagicMock(spec=Request)
        mock_request.state.user = {"sub": "user123"}

        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)

        request_data = SportRankingRequest(sport_rankings=["1", "2"])

        # Mock database operations
        mock_session.execute.return_value = MagicMock()  # For delete operation
        mock_session.commit.return_value = None

        # Execute
        with patch("apps.api.questionnaire_routes.get_current_user_id", return_value="user123"):
            result = await update_sport_ranking(mock_request, request_data, db_manager, mock_credentials)

        # Assert
        assert result["message"] == "Sport rankings updated successfully"
        assert mock_session.commit.called

    async def test_save_team_preferences_success(self, mock_db_manager):
        """Test successful team preferences save."""
        db_manager, mock_session = mock_db_manager

        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.user_id = "user123"

        request_data = [
            TeamPreferenceRequest(team_id="1", interest_level=3),
            TeamPreferenceRequest(team_id="2", interest_level=3)
        ]

        # Mock database operations
        mock_session.execute.return_value = MagicMock()
        mock_session.commit.return_value = None

        # Execute
        result = await save_team_preferences(request_data, mock_credentials, mock_session)

        # Assert
        assert result.success is True
        assert mock_session.commit.called

    async def test_get_user_preferences_success(self, mock_db_manager):
        """Test successful retrieval of user preferences."""
        db_manager, mock_session = mock_db_manager
        user_id = "user123"

        # Mock request and credentials
        mock_request = MagicMock(spec=Request)
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)

        # Mock database query results
        mock_sport_prefs = [
            UserSportPreference(user_id=user_id, sport_id="1", preference_rank=1),
            UserSportPreference(user_id=user_id, sport_id="2", preference_rank=2)
        ]
        mock_team_prefs = [
            UserTeamPreference(user_id=user_id, team_id="1", sport_id="1"),
            UserTeamPreference(user_id=user_id, team_id="2", sport_id="1")
        ]
        mock_status = UserQuestionnaireStatus(
            user_id=user_id,
            is_completed=True,
            current_step=3
        )

        # Mock query results
        mock_sport_result = MagicMock()
        mock_sport_result.scalars.return_value.all.return_value = mock_sport_prefs

        mock_team_result = MagicMock()
        mock_team_result.scalars.return_value.all.return_value = mock_team_prefs

        mock_status_result = MagicMock()
        mock_status_result.scalar_one_or_none.return_value = mock_status

        mock_session.execute.side_effect = [mock_sport_result, mock_team_result, mock_status_result]

        # Execute
        with patch("apps.api.questionnaire_routes.get_current_user_id", return_value=user_id):
            result = await get_user_preferences(mock_request, db_manager, mock_credentials)

        # Assert
        assert len(result.sport_preferences) == 2
        assert len(result.team_preferences) == 2
        assert result.questionnaire_status.is_completed is True
