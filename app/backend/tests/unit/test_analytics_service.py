from unittest.mock import AsyncMock

import pytest

from app.backend.repositories.interfaces.analytics_repository import IAnalyticsRepository
from app.backend.services.analytics import AnalyticsService


@pytest.fixture
def repo():
    return AsyncMock(spec=IAnalyticsRepository)


@pytest.fixture
def service(repo):
    return AnalyticsService(repo)


async def test_get_overview_maps_repo_values(service, repo):
    repo.get_total_conversations.return_value = 10
    repo.get_active_students.return_value = 4
    repo.get_total_messages.return_value = 50
    repo.get_avg_questions_per_conversation.return_value = 5.0

    result = await service.get_overview()

    assert result["total_conversations"] == 10
    assert result["active_students"] == 4
    assert result["total_messages"] == 50
    assert result["avg_questions_per_conversation"] == 5.0


async def test_get_courses_wraps_repo_list(service, repo):
    repo.get_courses.return_value = ["Math", "Physics"]
    result = await service.get_courses()
    assert result == ["Math", "Physics"]


async def test_get_courses_empty_list(service, repo):
    repo.get_courses.return_value = []
    result = await service.get_courses()
    assert result == []


@pytest.mark.parametrize("range_param,expected_days", [("7d", 7), ("30d", 30), ("90d", 90)])
async def test_get_activity_translates_range_to_days(service, repo, range_param, expected_days):
    repo.get_activity.return_value = []
    result = await service.get_activity(range_param)
    repo.get_activity.assert_awaited_once_with(expected_days, course_filter=None)
    assert len(result) == expected_days


@pytest.mark.parametrize("range_param,expected_days", [("7d", 7), ("30d", 30), ("90d", 90)])
async def test_get_course_activity_translates_range_to_days(service, repo, range_param, expected_days):
    repo.get_course_activity.return_value = []
    result = await service.get_course_activity("Math", range_param)
    repo.get_course_activity.assert_awaited_once_with("Math", expected_days)
    assert len(result) == expected_days


async def test_get_course_overview_returns_repo_data(service, repo):
    repo.get_course_overview.return_value = {
        "total_conversations": 3,
        "active_students": 2,
        "total_messages": 9,
        "avg_questions_per_conversation": 3.0,
    }
    result = await service.get_course_overview("Math")
    assert result == {
        "total_conversations": 3,
        "active_students": 2,
        "total_messages": 9,
        "avg_questions_per_conversation": 3.0,
    }


async def test_get_course_topics_counts_and_normalizes(service, repo):
    repo.get_course_concepts.return_value = ["Loops", "loops ", " LOOPS", "Arrays"]
    result = await service.get_course_topics("Prog")
    topics = {t["topic"]: t["count"] for t in result}
    assert topics["loops"] == 3
    assert topics["arrays"] == 1


async def test_get_course_topics_empty_concepts(service, repo):
    repo.get_course_concepts.return_value = []
    result = await service.get_course_topics("Prog")
    assert result == []


async def test_get_course_topics_caps_at_15(service, repo):
    repo.get_course_concepts.return_value = [f"concept-{i}" for i in range(20)]
    result = await service.get_course_topics("Prog")
    assert len(result) == 15


async def test_get_course_sources_maps_items(service, repo):
    repo.get_course_sources.return_value = [
        {"filename": "slides.pdf", "references": 4},
        {"filename": "notes.md", "references": 1},
    ]
    result = await service.get_course_sources("Math")
    assert result[0]["filename"] == "slides.pdf"
    assert result[0]["references"] == 4


async def test_get_course_topics_ordered_by_count_desc(service, repo):
    repo.get_course_concepts.return_value = (
        ["arrays"] * 2 + ["loops"] * 5 + ["recursion"] * 3
    )
    result = await service.get_course_topics("Prog")
    counts = [t["count"] for t in result]
    topics = [t["topic"] for t in result]
    assert counts == [5, 3, 2]
    assert topics == ["loops", "recursion", "arrays"]


async def test_get_course_topics_caps_picks_top_by_count(service, repo):
    # 20 conceitos com contagens distintas; só os 15 mais frequentes devem aparecer
    concepts = []
    for i in range(20):
        concepts.extend([f"c{i}"] * (i + 1))  # c0=1, c1=2, ..., c19=20
    repo.get_course_concepts.return_value = concepts
    result = await service.get_course_topics("Prog")
    assert len(result) == 15
    # o mais frequente é c19, o menos frequente incluído deve ser c5 (contagem 6)
    assert result[0]["topic"] == "c19"
    assert result[0]["count"] == 20
    assert result[-1]["count"] == 6
    # os 5 menos frequentes (c0..c4) não devem aparecer
    topic_names = {t["topic"] for t in result}
    for excluded in ("c0", "c1", "c2", "c3", "c4"):
        assert excluded not in topic_names


async def test_get_course_topics_filters_falsy_concepts(service, repo):
    repo.get_course_concepts.return_value = ["Loops", "", None, "Arrays"]
    result = await service.get_course_topics("Prog")
    topics = {t["topic"] for t in result}
    assert topics == {"loops", "arrays"}


async def test_get_course_sources_empty_list(service, repo):
    repo.get_course_sources.return_value = []
    result = await service.get_course_sources("Math")
    assert result == []


async def test_get_activity_passes_repo_data_through_helper(service, repo):
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    repo.get_activity.return_value = [{"date": today, "questions": 7}]
    result = await service.get_activity("7d")
    assert result[-1]["date"] == today
    assert result[-1]["questions"] == 7


async def test_get_course_activity_passes_repo_data_through_helper(service, repo):
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    repo.get_course_activity.return_value = [{"date": today, "questions": 3}]
    result = await service.get_course_activity("Math", "7d")
    assert result[-1]["date"] == today
    assert result[-1]["questions"] == 3
