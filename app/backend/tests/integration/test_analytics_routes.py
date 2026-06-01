"""
Route-level integration tests for the teacher dashboard (/api/v1/analytics/*).

These drive the real FastAPI app over HTTP, so they cover what the
service/repository tests cannot: routing, the auth guards and the role-based
course scoping (`require_teacher_or_admin`, `analytics_scope`). The DB and Redis
are pointed at the ephemeral test database.
"""

import pytest

from .factories import insert_chat, insert_course

OVERVIEW = "/api/v1/analytics/overview"


class TestAuthGuards:
    async def test_requires_authentication(self, api_client):
        resp = await api_client.get(OVERVIEW)
        assert resp.status_code == 401

    async def test_student_is_forbidden(self, api_client, auth_header):
        resp = await api_client.get(OVERVIEW, headers=auth_header(role="student"))
        assert resp.status_code == 403


class TestCourseScoping:
    async def test_teacher_overview_is_scoped_to_own_courses(self, api_client, auth_header, db):
        await insert_course(db, code="ed")
        await insert_course(db, code="poo")
        await insert_chat(db, course="ed", user_id="u1")
        await insert_chat(db, course="ed", user_id="u2")
        await insert_chat(db, course="poo", user_id="u3")  # outside the teacher's scope

        resp = await api_client.get(OVERVIEW, headers=auth_header(role="teacher", courses=["ed"]))

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_conversations"] == 2
        assert body["active_students"] == 2

    async def test_admin_overview_sees_all_courses(self, api_client, auth_header, db):
        await insert_course(db, code="ed")
        await insert_course(db, code="poo")
        await insert_chat(db, course="ed", user_id="u1")
        await insert_chat(db, course="ed", user_id="u2")
        await insert_chat(db, course="poo", user_id="u3")

        resp = await api_client.get(OVERVIEW, headers=auth_header(role="admin"))

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_conversations"] == 3
        assert body["active_students"] == 3

    async def test_teacher_forbidden_on_course_outside_scope(self, api_client, auth_header, db):
        await insert_course(db, code="ed")
        await insert_course(db, code="poo")

        resp = await api_client.get(
            "/api/v1/analytics/courses/poo/overview",
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 403

    async def test_unknown_course_returns_404(self, api_client, auth_header, db):
        await insert_course(db, code="ed")

        resp = await api_client.get(
            "/api/v1/analytics/courses/xyz/overview",
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 404


class TestRequestValidation:
    async def test_invalid_activity_range_returns_422(self, api_client, auth_header, db):
        await insert_course(db, code="ed")

        resp = await api_client.get(
            "/api/v1/analytics/activity",
            params={"range": "5d"},  # not one of 7d/30d/90d
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 422


class TestEndpointWiring:
    """Smoke tests: each remaining endpoint routes, authorizes and serializes its response_model."""

    async def test_global_activity(self, api_client, auth_header, db):
        await insert_course(db, code="ed")

        resp = await api_client.get(
            "/api/v1/analytics/activity",
            params={"range": "7d"},
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_course_overview(self, api_client, auth_header, db):
        await insert_course(db, code="ed")
        await insert_chat(db, course="ed", user_id="u1")

        resp = await api_client.get(
            "/api/v1/analytics/courses/ed/overview",
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 200
        assert resp.json()["course"] == "ed"

    async def test_courses_list(self, api_client, auth_header, db):
        await insert_course(db, code="ed")
        await insert_chat(db, course="ed", user_id="u1")

        resp = await api_client.get(
            "/api/v1/analytics/courses",
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 200
        assert resp.json() == {"data": ["ed"]}

    async def test_course_activity(self, api_client, auth_header, db):
        await insert_course(db, code="ed")

        resp = await api_client.get(
            "/api/v1/analytics/courses/ed/activity",
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_course_topics(self, api_client, auth_header, db):
        await insert_course(db, code="ed")

        resp = await api_client.get(
            "/api/v1/analytics/courses/ed/topics",
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 200
        assert resp.json() == {"course": "ed", "topics": []}

    async def test_course_sources(self, api_client, auth_header, db):
        await insert_course(db, code="ed")

        resp = await api_client.get(
            "/api/v1/analytics/courses/ed/sources",
            headers=auth_header(role="teacher", courses=["ed"]),
        )

        assert resp.status_code == 200
        assert resp.json() == {"course": "ed", "sources": []}