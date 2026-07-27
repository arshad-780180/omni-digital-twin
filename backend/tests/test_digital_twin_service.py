import pytest
from unittest.mock import AsyncMock, MagicMock
from services.digital_twin_service import DigitalTwinService


@pytest.mark.asyncio
async def test_digital_twin_service_get_context():
    """Test get_context retrieves all 5 core modules concurrently."""
    mock_db = MagicMock()

    # Mock profile
    mock_db.profiles.find_one = AsyncMock(return_value={"user_id": "user_123", "full_name": "Test User"})

    # Mock resume
    mock_cursor_res = MagicMock()
    mock_cursor_res.sort.return_value = mock_cursor_res
    mock_cursor_res.limit.return_value = mock_cursor_res
    mock_cursor_res.to_list = AsyncMock(return_value=[{"_id": "res_1", "user_id": "user_123"}])
    mock_db.resumes.find.return_value = mock_cursor_res

    # Mock github
    mock_cursor_gh = MagicMock()
    mock_cursor_gh.sort.return_value = mock_cursor_gh
    mock_cursor_gh.limit.return_value = mock_cursor_gh
    mock_cursor_gh.to_list = AsyncMock(return_value=[{"_id": "gh_1", "user_id": "user_123"}])
    mock_db.github_analysis.find.return_value = mock_cursor_gh

    # Mock career
    mock_cursor_car = MagicMock()
    mock_cursor_car.sort.return_value = mock_cursor_car
    mock_cursor_car.limit.return_value = mock_cursor_car
    mock_cursor_car.to_list = AsyncMock(return_value=[{"_id": "car_1", "user_id": "user_123"}])
    mock_db.career_analysis.find.return_value = mock_cursor_car

    # Mock ats
    mock_cursor_ats = MagicMock()
    mock_cursor_ats.sort.return_value = mock_cursor_ats
    mock_cursor_ats.limit.return_value = mock_cursor_ats
    mock_cursor_ats.to_list = AsyncMock(return_value=[{"_id": "ats_1", "user_id": "user_123"}])
    mock_db.ats_analysis.find.return_value = mock_cursor_ats

    context = await DigitalTwinService.get_context("user_123", mock_db)
    assert context["profile"]["full_name"] == "Test User"
    assert context["resume"]["_id"] == "res_1"
    assert context["github_analysis"]["_id"] == "gh_1"
    assert context["career_analysis"]["_id"] == "car_1"
    assert context["ats_analysis"]["_id"] == "ats_1"


@pytest.mark.asyncio
async def test_digital_twin_service_github_fallback():
    """Test get_github_analysis falls back to github_data if github_analysis is empty."""
    mock_db = MagicMock()
    mock_cursor_gh = MagicMock()
    mock_cursor_gh.sort.return_value = mock_cursor_gh
    mock_cursor_gh.limit.return_value = mock_cursor_gh
    mock_cursor_gh.to_list = AsyncMock(return_value=[])
    mock_db.github_analysis.find.return_value = mock_cursor_gh

    mock_db.github_data.find_one = AsyncMock(return_value={"user_id": "user_123", "fallback": True})

    res = await DigitalTwinService.get_github_analysis("user_123", mock_db)
    assert res is not None
    assert res["fallback"] is True
