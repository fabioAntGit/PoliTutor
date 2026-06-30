from .factories import insert_course, insert_user

COURSES = "/api/v1/courses"


async def test_create_course_requires_admin(api_client, auth_header):
    resp = await api_client.post(
        COURSES,
        json={"code": "ed", "name": "Estruturas de Dados"},
        headers=auth_header(role="student"),
    )
    assert resp.status_code == 403


async def test_create_course_admin_creates_course(api_client, auth_header):
    resp = await api_client.post(
        COURSES,
        json={"code": "ed", "name": "Estruturas de Dados"},
        headers=auth_header(role="admin"),
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "ed"
    assert body["is_active"] is True


async def test_create_course_duplicate_code_returns_409(api_client, db, auth_header):
    await insert_course(db, code="ed", name="Estruturas de Dados")

    resp = await api_client.post(
        COURSES,
        json={"code": "ed", "name": "Outro Nome"},
        headers=auth_header(role="admin"),
    )

    assert resp.status_code == 409


async def test_list_courses_lists_only_active(api_client, db, auth_header):
    ed_id = await insert_course(db, code="ed", is_active=True)
    await insert_course(db, code="old", is_active=False)
    uid = await insert_user(db, username="aluno", role="student", courses=[ed_id])

    resp = await api_client.get(COURSES, headers=auth_header(role="student", id=uid))

    assert resp.status_code == 200
    assert {c["code"] for c in resp.json()} == {"ed"}


async def test_delete_course_admin_deletes(api_client, db, auth_header):
    ed_id = await insert_course(db, code="ed")

    resp = await api_client.delete(f"{COURSES}/{ed_id}", headers=auth_header(role="admin"))

    assert resp.status_code == 204
    assert await db["courses"].find_one({"code": "ed"}) is None


async def test_delete_course_cannot_delete_with_associated_users_returns_409(api_client, db, auth_header):
    ed_id = await insert_course(db, code="ed")
    await insert_user(db, username="aluno", role="student", courses=[ed_id])

    resp = await api_client.delete(f"{COURSES}/{ed_id}", headers=auth_header(role="admin"))

    assert resp.status_code == 409
    assert await db["courses"].find_one({"code": "ed"}) is not None
