from .factories import insert_user

LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
CHANGE_PASSWORD = "/api/v1/auth/change-password"


async def test_login_valid_credentials_return_a_token(api_client, db):
    await insert_user(db, username="aluno", password="secret123", role="student")

    resp = await api_client.post(LOGIN, data={"username": "aluno", "password": "secret123"})

    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_wrong_password_returns_401(api_client, db):
    await insert_user(db, username="aluno", password="secret123", role="student")

    resp = await api_client.post(LOGIN, data={"username": "aluno", "password": "wrong-password"})

    assert resp.status_code == 401


async def test_login_unknown_user_returns_401(api_client):
    resp = await api_client.post(LOGIN, data={"username": "ninguem", "password": "secret123"})

    assert resp.status_code == 401


async def test_login_missing_password_field_returns_422(api_client):
    resp = await api_client.post(LOGIN, data={"username": "aluno"})

    assert resp.status_code == 422


async def test_logout_succeeds_and_blacklists_the_token(api_client, db, make_token):
    await insert_user(db, username="aluno", role="student")
    token = make_token(role="student", username="aluno", id="stud-1")

    resp = await api_client.post(LOGOUT, json={"access_token": token})
    assert resp.status_code == 200

    protected = await api_client.get(
        "/api/v1/chats", headers={"Authorization": f"Bearer {token}"}
    )
    assert protected.status_code == 401


async def test_logout_with_invalid_token_still_succeeds(api_client):
    resp = await api_client.post(LOGOUT, json={"access_token": "not-a-real-token"})

    assert resp.status_code == 200


async def test_change_password_requires_authentication(api_client):
    resp = await api_client.post(
        CHANGE_PASSWORD,
        json={"current_password": "oldpass12", "new_password": "newpass12"},
    )

    assert resp.status_code == 401


async def test_change_password_changes_and_returns_a_fresh_token(api_client, db, auth_header):
    await insert_user(
        db,
        username="aluno",
        password="oldpass12",
        role="student",
        must_change_password=True,
    )
    header = auth_header(role="student", username="aluno", must_change_password=True)

    resp = await api_client.post(
        CHANGE_PASSWORD,
        json={"current_password": "oldpass12", "new_password": "newpass12"},
        headers=header,
    )

    assert resp.status_code == 200
    assert resp.json()["access_token"]
    login = await api_client.post(LOGIN, data={"username": "aluno", "password": "newpass12"})
    assert login.status_code == 200


async def test_change_password_wrong_current_returns_400(api_client, db, auth_header):
    await insert_user(db, username="aluno", password="oldpass12", role="student")
    header = auth_header(role="student", username="aluno")

    resp = await api_client.post(
        CHANGE_PASSWORD,
        json={"current_password": "wrong-current", "new_password": "newpass12"},
        headers=header,
    )

    assert resp.status_code == 400


async def test_change_password_too_short_new_password_returns_400(api_client, db, auth_header):
    await insert_user(db, username="aluno", password="oldpass12", role="student")
    header = auth_header(role="student", username="aluno")

    resp = await api_client.post(
        CHANGE_PASSWORD,
        json={"current_password": "oldpass12", "new_password": "short"},
        headers=header,
    )

    assert resp.status_code == 400
