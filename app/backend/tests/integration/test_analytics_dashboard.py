"""
Teacher dashboard integration tests (endpoints /analytics/*).

They exercise the `AnalyticsService` wired to the **real** `AnalyticsRepository`
over an ephemeral MongoDB. The value is running the aggregation pipelines for
real (`$group`, `$unwind`, `$dateToString`, `distinct`, ...) — something the unit
tests cannot validate, since they mock the repository.
"""

import pytest

from app.backend.repositories.analytics import AnalyticsRepository
from app.backend.services.analytics import AnalyticsService

from .factories import insert_chat, insert_message


@pytest.fixture
def service(db) -> AnalyticsService:
    return AnalyticsService(analytics_repository=AnalyticsRepository(db))


class TestOverview:
    async def test_aggregates_everything_when_no_filter(self, service, db):
        chat_a = await insert_chat(db, course="ed", user_id="u1")
        chat_b = await insert_chat(db, course="ed", user_id="u2")
        chat_c = await insert_chat(db, course="poo", user_id="u1")  # u1 repeated

        await insert_message(db, conversation_id=chat_a, role="user")
        await insert_message(db, conversation_id=chat_a, role="user")
        await insert_message(db, conversation_id=chat_a, role="assistant")  # ignored
        await insert_message(db, conversation_id=chat_b, role="user")
        await insert_message(db, conversation_id=chat_c, role="user")
        await insert_message(db, conversation_id=chat_c, role="user")
        await insert_message(db, conversation_id=chat_c, role="user")

        overview = await service.get_overview()

        assert overview.total_conversations == 3
        assert overview.active_students == 2  # u1, u2 (distinct)
        assert overview.total_messages == 6  # only role=user
        assert overview.avg_questions_per_conversation == 2.0  # (2+1+3)/3

    async def test_scopes_to_course_filter(self, service, db):
        chat_a = await insert_chat(db, course="ed", user_id="u1")
        chat_b = await insert_chat(db, course="ed", user_id="u2")
        chat_c = await insert_chat(db, course="poo", user_id="u3")

        await insert_message(db, conversation_id=chat_a, role="user")
        await insert_message(db, conversation_id=chat_a, role="user")
        await insert_message(db, conversation_id=chat_b, role="user")
        await insert_message(db, conversation_id=chat_c, role="user")  # out of scope

        overview = await service.get_overview(course_filter=["ed"])

        assert overview.total_conversations == 2
        assert overview.active_students == 2
        assert overview.total_messages == 3  # 2 + 1, poo excluded
        assert overview.avg_questions_per_conversation == 1.5  # (2+1)/2

    async def test_empty_filter_returns_zeros(self, service, db):
        chat = await insert_chat(db, course="ed", user_id="u1")
        await insert_message(db, conversation_id=chat, role="user")

        overview = await service.get_overview(course_filter=[])

        assert overview.total_conversations == 0
        assert overview.active_students == 0
        assert overview.total_messages == 0
        assert overview.avg_questions_per_conversation == 0.0


class TestActivity:
    async def test_window_excludes_messages_outside_range(self, service, db):
        chat = await insert_chat(db, course="ed", user_id="u1")
        await insert_message(db, conversation_id=chat, role="user", days_ago=2)
        await insert_message(db, conversation_id=chat, role="user", days_ago=40)
        await insert_message(db, conversation_id=chat, role="user", days_ago=200)
        await insert_message(db, conversation_id=chat, role="assistant", days_ago=1)  # ignored

        week = await service.get_activity("7d")
        quarter = await service.get_activity("90d")

        assert sum(p.questions for p in week.data) == 1  # only the one from 2 days ago
        assert sum(p.questions for p in quarter.data) == 2  # 2 days + 40 days

    async def test_fills_missing_days_with_zero(self, service, db):
        chat = await insert_chat(db, course="ed", user_id="u1")
        await insert_message(db, conversation_id=chat, role="user", days_ago=2)

        week = await service.get_activity("7d")

        assert len(week.data) == 7  # continuous series, no gaps
        assert sum(p.questions for p in week.data) == 1

    async def test_groups_questions_into_per_day_buckets(self, service, db):
        chat = await insert_chat(db, course="ed", user_id="u1")
        await insert_message(db, conversation_id=chat, role="user", days_ago=3)
        await insert_message(db, conversation_id=chat, role="user", days_ago=3)  # same day
        await insert_message(db, conversation_id=chat, role="user", days_ago=1)  # another day

        week = await service.get_activity("7d")
        nonzero = [p for p in week.data if p.questions > 0]

        assert len(nonzero) == 2  # two distinct day buckets ($dateToString)
        assert {p.questions for p in nonzero} == {1, 2}  # 2 on day -3, 1 on day -1
        assert len({p.date for p in nonzero}) == 2  # buckets have distinct dates

    async def test_course_activity_is_scoped(self, service, db):
        ed = await insert_chat(db, course="ed", user_id="u1")
        poo = await insert_chat(db, course="poo", user_id="u2")
        await insert_message(db, conversation_id=ed, role="user", days_ago=1)
        await insert_message(db, conversation_id=poo, role="user", days_ago=1)

        activity = await service.get_course_activity("ed", "7d")

        assert sum(p.questions for p in activity.data) == 1

    async def test_global_activity_with_filter_counts_only_scoped(self, service, db):
        ed = await insert_chat(db, course="ed", user_id="u1")
        poo = await insert_chat(db, course="poo", user_id="u2")
        await insert_message(db, conversation_id=ed, role="user", days_ago=1)
        await insert_message(db, conversation_id=poo, role="user", days_ago=1)

        activity = await service.get_activity("7d", course_filter=["ed"])

        assert sum(p.questions for p in activity.data) == 1

    async def test_global_activity_with_filter_without_conversations_is_empty(self, service, db):
        await insert_chat(db, course="poo", user_id="u1")  # nothing in 'ed'

        activity = await service.get_activity("7d", course_filter=["ed"])

        assert sum(p.questions for p in activity.data) == 0


class TestCourses:
    async def test_returns_distinct_sorted(self, service, db):
        await insert_chat(db, course="poo", user_id="u1")
        await insert_chat(db, course="ed", user_id="u2")
        await insert_chat(db, course="ed", user_id="u3")
        await insert_chat(db, course="alg", user_id="u4")

        courses = await service.get_courses()

        assert courses.data == ["alg", "ed", "poo"]

    async def test_respects_filter(self, service, db):
        await insert_chat(db, course="ed", user_id="u1")
        await insert_chat(db, course="poo", user_id="u2")
        await insert_chat(db, course="alg", user_id="u3")

        courses = await service.get_courses(course_filter=["ed", "poo"])

        assert courses.data == ["ed", "poo"]

    async def test_empty_filter_returns_empty(self, service, db):
        await insert_chat(db, course="ed", user_id="u1")

        courses = await service.get_courses(course_filter=[])

        assert courses.data == []

    async def test_scoped_conversation_ids_helper(self, db):
        repo = AnalyticsRepository(db)
        await insert_chat(db, course="ed", user_id="u1")

        assert await repo._scoped_conversation_ids(None) is None  # no filter
        assert await repo._scoped_conversation_ids([]) == []  # empty filter
        assert len(await repo._scoped_conversation_ids(["ed"])) == 1


class TestCourseOverview:
    async def test_only_counts_target_course(self, service, db):
        ed_a = await insert_chat(db, course="ed", user_id="u1")
        ed_b = await insert_chat(db, course="ed", user_id="u2")
        poo = await insert_chat(db, course="poo", user_id="u1")

        await insert_message(db, conversation_id=ed_a, role="user")
        await insert_message(db, conversation_id=ed_a, role="user")
        await insert_message(db, conversation_id=ed_b, role="user")
        await insert_message(db, conversation_id=poo, role="user")  # other course

        overview = await service.get_course_overview("ed")

        assert overview.course == "ed"
        assert overview.total_conversations == 2
        assert overview.active_students == 2
        assert overview.total_messages == 3
        assert overview.avg_questions_per_conversation == 1.5

    async def test_course_without_data_returns_zeros(self, service, db):
        # No chats/messages at all, must not divide by zero on the average.
        overview = await service.get_course_overview("ed")

        assert overview.total_conversations == 0
        assert overview.active_students == 0
        assert overview.total_messages == 0
        assert overview.avg_questions_per_conversation == 0.0


class TestCourseTopics:
    async def test_counts_and_normalizes_concepts(self, service, db):
        await insert_chat(db, course="ed", user_id="u1", summary='{"concept_tags": ["Recursão", "Listas"]}')
        await insert_chat(db, course="ed", user_id="u2", summary='```json\n{"concept_tags": ["recursão"]}\n```')
        await insert_chat(db, course="ed", user_id="u3", summary='{"concepts_covered": ["Listas"]}')  # fallback
        await insert_chat(db, course="ed", user_id="u4", summary="this is not json")  # ignored
        await insert_chat(db, course="poo", user_id="u5", summary='{"concept_tags": ["Herança"]}')  # other course

        result = await service.get_course_topics("ed")
        counts = {t.topic: t.count for t in result.topics}

        assert result.course == "ed"
        assert counts == {"recursão": 2, "listas": 2}

    async def test_no_summaries_yields_empty(self, service, db):
        await insert_chat(db, course="ed", user_id="u1")  # no summary

        result = await service.get_course_topics("ed")

        assert result.topics == []

    async def test_ignores_non_string_summary(self, service, db):
        # A non-string summary slips past the existence filter but must be skipped.
        await db["chats"].insert_one({"course": "ed", "user_id": "u1", "summary": 123})
        await insert_chat(db, course="ed", user_id="u2", summary='{"concept_tags": ["loops"]}')

        result = await service.get_course_topics("ed")

        assert {t.topic for t in result.topics} == {"loops"}

    async def test_caps_at_top_15_ordered_by_count(self, service, db):
        # 16 distinct concepts with strictly decreasing frequency (t0 x16 ... t15 x1).
        import json

        tags = [f"t{i}" for i in range(16) for _ in range(16 - i)]
        await insert_chat(db, course="ed", user_id="u1", summary=json.dumps({"concept_tags": tags}))

        result = await service.get_course_topics("ed")
        counts = [t.count for t in result.topics]

        assert len(result.topics) == 15  # capped, t15 (count 1) dropped
        assert result.topics[0].topic == "t0"
        assert result.topics[0].count == 16
        assert counts == sorted(counts, reverse=True)  # descending order
        assert "t15" not in {t.topic for t in result.topics}


class TestCourseSources:
    async def test_unwinds_and_ranks_by_references(self, service, db):
        chat = await insert_chat(db, course="ed", user_id="u1")
        await insert_message(
            db, conversation_id=chat, role="assistant",
            sources=[{"filename": "a.pdf", "pages": [1]}, {"filename": "b.pdf", "pages": [2]}],
        )
        await insert_message(
            db, conversation_id=chat, role="assistant",
            sources=[{"filename": "a.pdf", "pages": [3]}],
        )
        # user message with sources must not count
        await insert_message(
            db, conversation_id=chat, role="user",
            sources=[{"filename": "a.pdf", "pages": [9]}],
        )

        result = await service.get_course_sources("ed")
        ranked = [(s.filename, s.references) for s in result.sources]

        assert result.course == "ed"
        assert ranked == [("a.pdf", 2), ("b.pdf", 1)]