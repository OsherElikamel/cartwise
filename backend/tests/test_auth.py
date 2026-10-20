def test_register_login_and_me(client):
    res = client.post("/api/auth/register", json={"name": "Osher", "email": "Osher@Example.com", "password": "cartwise123"})
    assert res.status_code == 201
    assert res.json()["email"] == "osher@example.com"

    token = client.post("/api/auth/login", json={"email": "osher@example.com", "password": "cartwise123"}).json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert "password_hash" not in me.json()


def test_duplicate_email_is_rejected(client):
    body = {"name": "Osher", "email": "osher@example.com", "password": "cartwise123"}
    client.post("/api/auth/register", json=body)
    res = client.post("/api/auth/register", json=body)
    assert res.status_code == 409


def test_weak_password_is_rejected_by_the_backend(client):
    res = client.post("/api/auth/register", json={"name": "Osher", "email": "o@example.com", "password": "abcdefgh"})
    assert res.status_code == 422


def test_wrong_password_returns_401(client):
    client.post("/api/auth/register", json={"name": "Osher", "email": "o@example.com", "password": "cartwise123"})
    res = client.post("/api/auth/login", json={"email": "o@example.com", "password": "wrong-pass1"})
    assert res.status_code == 401


def test_me_requires_a_valid_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401
