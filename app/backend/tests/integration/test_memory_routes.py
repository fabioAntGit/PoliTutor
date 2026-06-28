import pytest

from .factories import insert_memory

CALLER = "user-1"
LIST = "/api/v1/memory"


class TestListMemories:
    async def test_requires_authentication(self, api_client):
        resp = await api_client.get(LIST, params={"course": "ed"})
        assert resp.status_code == 401

    async def test_missing_course_param_returns_422(self, api_client, auth_header):
        resp = await api_client.get(LIST, headers=auth_header())
        assert resp.status_code == 422

    async def test_returns_only_callers_memories_for_course(self, api_client, auth_header, db):
        await insert_memory(db, mem_id="m1", user_id=CALLER, course="ed")
        await insert_memory(db, mem_id="m2", user_id=CALLER, course="ed")
        await insert_memory(db, mem_id="m3", user_id=CALLER, course="poo")  # other course
        await insert_memory(db, mem_id="m4", user_id="someone-else", course="ed")  # other user

        resp = await api_client.get(LIST, params={"course": "ed"}, headers=auth_header())

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert {m["id"] for m in body["memories"]} == {"m1", "m2"}

    async def test_returns_empty_when_no_memories(self, api_client, auth_header):
        resp = await api_client.get(LIST, params={"course": "ed"}, headers=auth_header())

        assert resp.status_code == 200
        assert resp.json() == {"memories": [], "total": 0}


class TestDeleteMemory:
    async def test_requires_authentication(self, api_client):
        resp = await api_client.delete(f"{LIST}/m1")
        assert resp.status_code == 401

    async def test_deletes_own_memory(self, api_client, auth_header, db):
        await insert_memory(db, mem_id="m1", user_id=CALLER, course="ed")

        resp = await api_client.delete(f"{LIST}/m1", headers=auth_header())
        assert resp.status_code == 204

        listing = await api_client.get(LIST, params={"course": "ed"}, headers=auth_header())
        assert listing.json()["total"] == 0

    async def test_cannot_delete_another_users_memory(self, api_client, auth_header, db):
        await insert_memory(db, mem_id="m1", user_id="someone-else", course="ed")

        resp = await api_client.delete(f"{LIST}/m1", headers=auth_header())

        assert resp.status_code == 404
        assert await db["user_memory"].find_one({"_id": "m1"}) is not None

    async def test_unknown_memory_returns_404(self, api_client, auth_header):
        resp = await api_client.delete(f"{LIST}/does-not-exist", headers=auth_header())
        assert resp.status_code == 404
