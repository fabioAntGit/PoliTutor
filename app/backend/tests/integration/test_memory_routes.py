import pytest
from bson import ObjectId

from .factories import insert_memory

CALLER = str(ObjectId())
OTHER = str(ObjectId())
M1 = str(ObjectId())
M2 = str(ObjectId())
ED_ID = str(ObjectId())
POO_ID = str(ObjectId())
LIST = "/api/v1/memory"


class TestListMemories:
    async def test_requires_authentication(self, api_client):
        resp = await api_client.get(LIST, params={"course_id": ED_ID})
        assert resp.status_code == 401

    async def test_missing_course_param_returns_422(self, api_client, auth_header):
        resp = await api_client.get(LIST, headers=auth_header(id=CALLER))
        assert resp.status_code == 422

    async def test_returns_only_callers_memories_for_course(self, api_client, auth_header, db):
        await insert_memory(db, mem_id=M1, user_id=CALLER, course_id=ED_ID)
        await insert_memory(db, mem_id=M2, user_id=CALLER, course_id=ED_ID)
        await insert_memory(db, user_id=CALLER, course_id=POO_ID)  # other course
        await insert_memory(db, user_id=OTHER, course_id=ED_ID)  # other user

        resp = await api_client.get(LIST, params={"course_id": ED_ID}, headers=auth_header(id=CALLER))

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["memories"]) == 2
        assert {m["id"] for m in body["memories"]} == {M1, M2}
        assert all(
            set(m) == {"id", "type", "content", "last_seen_at"}
            for m in body["memories"]
        )

    async def test_returns_empty_when_no_memories(self, api_client, auth_header):
        resp = await api_client.get(LIST, params={"course_id": ED_ID}, headers=auth_header(id=CALLER))

        assert resp.status_code == 200
        assert resp.json() == {"memories": []}


class TestDeleteMemory:
    async def test_requires_authentication(self, api_client):
        resp = await api_client.delete(f"{LIST}/{M1}")
        assert resp.status_code == 401

    async def test_deletes_own_memory(self, api_client, auth_header, db):
        await insert_memory(db, mem_id=M1, user_id=CALLER, course_id=ED_ID)

        resp = await api_client.delete(f"{LIST}/{M1}", headers=auth_header(id=CALLER))
        assert resp.status_code == 204

        listing = await api_client.get(LIST, params={"course_id": ED_ID}, headers=auth_header(id=CALLER))
        assert listing.json()["memories"] == []

    async def test_cannot_delete_another_users_memory(self, api_client, auth_header, db):
        await insert_memory(db, mem_id=M1, user_id=OTHER, course_id=ED_ID)

        resp = await api_client.delete(f"{LIST}/{M1}", headers=auth_header(id=CALLER))

        assert resp.status_code == 404
        assert await db["user_memory"].find_one({"_id": ObjectId(M1)}) is not None

    async def test_unknown_memory_returns_404(self, api_client, auth_header):
        resp = await api_client.delete(f"{LIST}/{ObjectId()}", headers=auth_header(id=CALLER))
        assert resp.status_code == 404
