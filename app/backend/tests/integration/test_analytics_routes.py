import pytest_asyncio
from bson import ObjectId

from .factories import insert_chat, insert_course, insert_user

OVERVIEW = "/api/v1/analytics/overview"
UNKNOWN_ID = "000000000000000000000000"

U1 = str(ObjectId())
U2 = str(ObjectId())
U3 = str(ObjectId())


@pytest_asyncio.fixture
async def ed_id(db):
    """The 'ed' course, returning its ObjectId."""
    return await insert_course(db, code="ed")


@pytest_asyncio.fixture
async def ed_teacher_header(db, auth_header, ed_id):
    """A teacher enrolled in the 'ed' course, returning its auth header."""
    tid = await insert_user(db, username="prof", role="teacher", courses=[ed_id])
    return auth_header(role="teacher", id=tid)


class TestAuthGuards:
    async def test_requires_authentication(self, api_client):
        resp = await api_client.get(OVERVIEW)
        assert resp.status_code == 401

    async def test_student_is_forbidden(self, api_client, auth_header):
        resp = await api_client.get(OVERVIEW, headers=auth_header(role="student"))
        assert resp.status_code == 403


class TestCourseScoping:
    async def test_teacher_overview_is_scoped_to_own_courses(self, api_client, ed_teacher_header, ed_id, db):
        poo_id = await insert_course(db, code="poo")
        await insert_chat(db, course_id=ed_id, user_id=U1)
        await insert_chat(db, course_id=ed_id, user_id=U2)
        await insert_chat(db, course_id=poo_id, user_id=U3)  # outside the teacher's scope

        resp = await api_client.get(OVERVIEW, headers=ed_teacher_header)

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_conversations"] == 2
        assert body["active_students"] == 2

    async def test_admin_overview_sees_all_courses(self, api_client, auth_header, db):
        ed_id = await insert_course(db, code="ed")
        poo_id = await insert_course(db, code="poo")
        await insert_chat(db, course_id=ed_id, user_id=U1)
        await insert_chat(db, course_id=ed_id, user_id=U2)
        await insert_chat(db, course_id=poo_id, user_id=U3)

        resp = await api_client.get(OVERVIEW, headers=auth_header(role="admin"))

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_conversations"] == 3
        assert body["active_students"] == 3

    async def test_teacher_forbidden_on_course_outside_scope(self, api_client, ed_teacher_header, db):
        poo_id = await insert_course(db, code="poo")

        resp = await api_client.get(
            f"/api/v1/analytics/courses/{poo_id}/overview",
            headers=ed_teacher_header,
        )

        assert resp.status_code == 403

    async def test_unknown_course_returns_404(self, api_client, ed_teacher_header):
        resp = await api_client.get(
            f"/api/v1/analytics/courses/{UNKNOWN_ID}/overview",
            headers=ed_teacher_header,
        )

        assert resp.status_code == 404


class TestRequestValidation:
    async def test_invalid_activity_range_returns_422(self, api_client, ed_teacher_header):
        resp = await api_client.get(
            "/api/v1/analytics/activity",
            params={"range": "5d"},  # not one of 7d/30d/90d
            headers=ed_teacher_header,
        )

        assert resp.status_code == 422


class TestEndpointWiring:
    """Smoke tests: each remaining endpoint routes, authorizes and serializes its response_model."""

    async def test_global_activity(self, api_client, ed_teacher_header):
        resp = await api_client.get(
            "/api/v1/analytics/activity",
            params={"range": "7d"},
            headers=ed_teacher_header,
        )

        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_course_overview(self, api_client, ed_teacher_header, ed_id, db):
        await insert_chat(db, course_id=ed_id, user_id=U1)

        resp = await api_client.get(
            f"/api/v1/analytics/courses/{ed_id}/overview",
            headers=ed_teacher_header,
        )

        assert resp.status_code == 200
        assert resp.json()["total_conversations"] == 1

    async def test_course_activity(self, api_client, ed_teacher_header, ed_id):
        resp = await api_client.get(
            f"/api/v1/analytics/courses/{ed_id}/activity",
            headers=ed_teacher_header,
        )

        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_course_topics(self, api_client, ed_teacher_header, ed_id):
        resp = await api_client.get(
            f"/api/v1/analytics/courses/{ed_id}/topics",
            headers=ed_teacher_header,
        )

        assert resp.status_code == 200
        assert resp.json() == {"topics": []}

    async def test_course_sources(self, api_client, ed_teacher_header, ed_id):
        resp = await api_client.get(
            f"/api/v1/analytics/courses/{ed_id}/sources",
            headers=ed_teacher_header,
        )

        assert resp.status_code == 200
        assert resp.json() == {"sources": []}
