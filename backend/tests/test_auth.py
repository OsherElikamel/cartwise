def test_register_login_and_me(client):
    res = client.post("/api/auth/register", json={"name": "Osher", "email": "Osher@Example.com", "password": "cartwise123"})
    assert res.status_code == 201
    assert res.json()["user"]["email"] == "osher@example.com"

    token = client.post("/api/auth/login", json={"email": "osher@example.com", "password": "cartwise123"}).json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert "password_hash" not in me.json()


def test_registration_signs_the_user_in_within_the_same_response(client):
    res = client.post("/api/auth/register", json={"name": "Osher", "email": "o@example.com", "password": "cartwise123"})
    token = res.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "o@example.com"


def test_duplicate_email_is_rejected_with_a_code(client):
    body = {"name": "Osher", "email": "osher@example.com", "password": "cartwise123"}
    client.post("/api/auth/register", json=body)
    res = client.post("/api/auth/register", json=body)
    assert res.status_code == 409
    assert res.json()["code"] == "email_taken"


def test_rate_limit_says_how_long_to_wait(client):
    limiter = client.app.state.limiter
    limiter.enabled = True
    try:
        body = {"email": "nobody@example.com", "password": "wrong-pass1"}
        statuses = [client.post("/api/auth/login", json=body).status_code for _ in range(11)]
        assert statuses[:10] == [401] * 10
        res = client.post("/api/auth/login", json=body)
        assert res.status_code == 429
        assert res.json()["code"] == "rate_limited"
        assert res.json()["retry_after"] == 60
        assert res.headers["Retry-After"] == "60"
    finally:
        limiter.enabled = False
        limiter.reset()


def test_weak_password_is_rejected_by_the_backend(client):
    res = client.post("/api/auth/register", json={"name": "Osher", "email": "o@example.com", "password": "abcdefgh"})
    assert res.status_code == 422


def test_wrong_password_returns_401(client):
    client.post("/api/auth/register", json={"name": "Osher", "email": "o@example.com", "password": "cartwise123"})
    res = client.post("/api/auth/login", json={"email": "o@example.com", "password": "wrong-pass1"})
    assert res.status_code == 401
    assert res.json()["code"] == "invalid_credentials"


def test_me_requires_a_valid_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401
