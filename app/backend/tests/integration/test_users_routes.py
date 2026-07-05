from .factories import insert_user

USERS = "/api/v1/users"


def _new_user_payload(**overrides) -> dict:
    payload = {
        "email": "novo@estg.ipp.pt",
        "password": "password123",
        "full_name": "Novo Aluno",
        "role": "student",
        "courses": [],
    }
    payload.update(overrides)
    return payload


async def test_create_user_requires_admin(api_client, auth_header):
    resp = await api_client.post(
        USERS, json=_new_user_payload(), headers=auth_header(role="teacher")
    )
    assert resp.status_code == 403


async def test_create_user_admin_creates_with_username_from_email(api_client, auth_header):
    resp = await api_client.post(
        USERS, json=_new_user_payload(), headers=auth_header(role="admin")
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "novo"
    assert body["email"] == "novo@estg.ipp.pt"


async def test_create_user_duplicate_email_returns_409(api_client, db, auth_header):
    await insert_user(db, username="novo", email="novo@estg.ipp.pt", role="student")

    resp = await api_client.post(
        USERS, json=_new_user_payload(), headers=auth_header(role="admin")
    )

    assert resp.status_code == 409


async def test_create_user_short_password_returns_422(api_client, auth_header):
    resp = await api_client.post(
        USERS,
        json=_new_user_payload(password="short"),
        headers=auth_header(role="admin"),
    )

    assert resp.status_code == 422


async def test_list_users_requires_admin(api_client, auth_header):
    resp = await api_client.get(USERS, headers=auth_header(role="student"))
    assert resp.status_code == 403


async def test_list_users_admin_lists_users(api_client, db, auth_header):
    await insert_user(db, username="ana", email="ana@estg.ipp.pt")
    await insert_user(db, username="rui", email="rui@estg.ipp.pt")

    resp = await api_client.get(USERS, headers=auth_header(role="admin"))

    assert resp.status_code == 200
    assert {u["username"] for u in resp.json()} == {"ana", "rui"}
