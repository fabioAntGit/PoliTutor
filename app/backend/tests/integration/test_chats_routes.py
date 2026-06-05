from .factories import insert_chat, insert_course, insert_user

CREATE = "/api/v1/chat"
LIST = "/api/v1/chats"
UNKNOWN_ID = "000000000000000000000000"


async def test_create_chat_requires_authentication(api_client):
    resp = await api_client.post(CREATE, json={"course_code": "ed"})
    assert resp.status_code == 401


async def test_create_chat_teacher_is_forbidden(api_client, auth_header):
    resp = await api_client.post(
        CREATE, json={"course_code": "ed"}, headers=auth_header(role="teacher")
    )
    assert resp.status_code == 403


async def test_create_chat_student_creates_a_chat(api_client, db, auth_header):
    uid = await insert_user(db, username="aluno", role="student", courses=["ed"])
    await insert_course(db, code="ed")

    resp = await api_client.post(
        CREATE, json={"course_code": "ed"}, headers=auth_header(role="student", id=uid)
    )

    assert resp.status_code == 201
    assert resp.json()["conversation_id"]


async def test_create_chat_course_not_in_user_courses_is_forbidden(api_client, db, auth_header):
    uid = await insert_user(db, username="aluno", role="student", courses=[])
    await insert_course(db, code="ed")

    resp = await api_client.post(
        CREATE, json={"course_code": "ed"}, headers=auth_header(role="student", id=uid)
    )

    assert resp.status_code == 403


async def test_create_chat_unknown_course_returns_404(api_client, db, auth_header):
    uid = await insert_user(db, username="aluno", role="student", courses=["ed"])

    resp = await api_client.post(
        CREATE, json={"course_code": "ed"}, headers=auth_header(role="student", id=uid)
    )

    assert resp.status_code == 404


async def test_list_chats_requires_authentication(api_client):
    resp = await api_client.get(LIST)
    assert resp.status_code == 401


async def test_list_chats_returns_only_callers_chats(api_client, db, auth_header):
    await insert_course(db, code="ed")
    await insert_chat(db, course="ed", user_id="stud-1")
    await insert_chat(db, course="ed", user_id="stud-1")
    await insert_chat(db, course="ed", user_id="someone-else")

    resp = await api_client.get(LIST, headers=auth_header(role="student", id="stud-1"))

    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_chat_requires_authentication(api_client):
    resp = await api_client.get(f"{CREATE}/{UNKNOWN_ID}")
    assert resp.status_code == 401


async def test_get_chat_returns_own_chat(api_client, db, auth_header):
    await insert_course(db, code="ed", name="Estruturas de Dados")
    chat_id = await insert_chat(db, course="ed", user_id="stud-1")

    resp = await api_client.get(
        f"{CREATE}/{chat_id}", headers=auth_header(role="student", id="stud-1")
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_id"] == chat_id
    assert body["course_code"] == "ed"
    assert body["messages"] == []


async def test_get_chat_cannot_access_another_users_chat(api_client, db, auth_header):
    await insert_course(db, code="ed")
    chat_id = await insert_chat(db, course="ed", user_id="someone-else")

    resp = await api_client.get(
        f"{CREATE}/{chat_id}", headers=auth_header(role="student", id="stud-1")
    )

    assert resp.status_code == 403


async def test_get_chat_unknown_returns_404(api_client, auth_header):
    resp = await api_client.get(
        f"{CREATE}/{UNKNOWN_ID}", headers=auth_header(role="student", id="stud-1")
    )

    assert resp.status_code == 404
