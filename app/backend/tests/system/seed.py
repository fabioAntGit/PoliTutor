"""Seed for the system (E2E) tests.

Runs inside the backend image against the ephemeral MongoDB defined in
docker-compose.test.yml. Inserts a teacher (dashboard/analytics) and a student
(memories). Clears the collections first, so it must not run against a real
database.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pwdlib import PasswordHash
from pymongo import AsyncMongoClient

from app.backend.core.config import MONGO_DB, MONGO_URI

TEACHER_USERNAME = "prof.teste"
TEACHER_PASSWORD = "Teste1234!"
TEACHER_EMAIL = "prof.teste@ipp.pt"

STUDENT_USERNAME = "aluno.teste"
STUDENT_PASSWORD = "Teste1234!"
STUDENT_EMAIL = "aluno.teste@ipp.pt"

ADMIN_USERNAME = "admin.teste"
ADMIN_PASSWORD = "Teste1234!"
ADMIN_EMAIL = "admin.teste@ipp.pt"

COURSE_CODE = "ed"
COURSE_NAME = "Estruturas de Dados"

SECOND_COURSE_CODE = "ia"
SECOND_COURSE_NAME = "Inteligência Artificial"

_password_hash = PasswordHash.recommended()


async def seed() -> None:
    client = AsyncMongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    db = client[MONGO_DB]

    for name in ("users", "courses", "chats", "messages", "user_memory"):
        await db[name].delete_many({})

    now = datetime.now(timezone.utc)
    teacher_id = ObjectId()
    student_id = ObjectId()
    admin_id = ObjectId()

    await db["courses"].insert_many(
        [
            {
                "code": COURSE_CODE,
                "name": COURSE_NAME,
                "description": "E2E test course.",
                "is_active": True,
                "created_at": now,
            },
            {
                "code": SECOND_COURSE_CODE,
                "name": SECOND_COURSE_NAME,
                "description": "E2E course nobody is enrolled in.",
                "is_active": True,
                "created_at": now,
            },
        ]
    )

    await db["users"].insert_many(
        [
            {
                "_id": teacher_id,
                "email": TEACHER_EMAIL,
                "username": TEACHER_USERNAME,
                "role": "teacher",
                "hashed_password": _password_hash.hash(TEACHER_PASSWORD),
                "full_name": "Professor de Teste",
                "courses": [COURSE_CODE],
                "must_change_password": False,
                "created_at": now,
                "updated_at": now,
            },
            {
                "_id": student_id,
                "email": STUDENT_EMAIL,
                "username": STUDENT_USERNAME,
                "role": "student",
                "hashed_password": _password_hash.hash(STUDENT_PASSWORD),
                "full_name": "Aluno de Teste",
                "courses": [COURSE_CODE],
                "must_change_password": False,
                "created_at": now,
                "updated_at": now,
            },
            {
                "_id": admin_id,
                "email": ADMIN_EMAIL,
                "username": ADMIN_USERNAME,
                "role": "admin",
                "hashed_password": _password_hash.hash(ADMIN_PASSWORD),
                "full_name": "Admin de Teste",
                "courses": [],
                "must_change_password": False,
                "created_at": now,
                "updated_at": now,
            },
        ]
    )

    chat_concepts = [
        ["Listas Ligadas", "Recursão"],
        ["Listas Ligadas", "Recursão"],
        ["Listas Ligadas", "Complexidade"],
    ]
    main_source = "Capitulo-1-Listas.pdf"
    secondary_source = "Capitulo-2-Arvores.pdf"

    chat_docs = []
    message_docs = []
    for day_offset in range(3):
        created = now - timedelta(days=day_offset)
        chat_id = ObjectId()
        chat_docs.append(
            {
                "_id": chat_id,
                "course": COURSE_CODE,
                "user_id": str(student_id),
                "summary": json.dumps({"concept_tags": chat_concepts[day_offset]}),
                "created_at": created,
                "updated_at": created,
            }
        )
        for i in range(2):
            for role in ("user", "assistant"):
                sources = []
                if role == "assistant":
                    sources = [{"filename": main_source, "pages": [1, 2]}]
                    if i == 0:
                        sources.append({"filename": secondary_source, "pages": [3]})
                message_docs.append(
                    {
                        "conversation_id": str(chat_id),
                        "role": role,
                        "content": f"{role} message {day_offset}-{i}",
                        "sources": sources,
                        "is_reported": False,
                        "created_at": created,
                    }
                )

    await db["chats"].insert_many(chat_docs)
    await db["messages"].insert_many(message_docs)

    await db["user_memory"].insert_many(
        [
            {
                "_id": str(ObjectId()),
                "user_id": str(student_id),
                "course": COURSE_CODE,
                "type": "difficulty",
                "topic": "Listas ligadas",
                "content": "Tem dificuldade em inserir no meio de uma lista ligada.",
                "importance": 8.0,
                "last_seen_at": now,
                "created_at": now,
            },
            {
                "_id": str(ObjectId()),
                "user_id": str(student_id),
                "course": COURSE_CODE,
                "type": "preference",
                "topic": "Exemplos",
                "content": "Prefere explicações com exemplos de código.",
                "importance": 5.0,
                "last_seen_at": now,
                "created_at": now,
            },
            {
                "_id": str(ObjectId()),
                "user_id": str(student_id),
                "course": COURSE_CODE,
                "type": "preference",
                "topic": "Descartavel",
                "content": "Memoria descartavel para o teste de remocao.",
                "importance": 3.0,
                "last_seen_at": now,
                "created_at": now,
            },
        ]
    )

    print(f"Seed done: {len(chat_docs)} chats, {len(message_docs)} messages.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(seed())