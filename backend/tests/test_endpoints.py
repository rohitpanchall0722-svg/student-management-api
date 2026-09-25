import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from backend.app.core.rate_limiter import rate_limit

from backend.app.core.secuirty import hash_password
from backend.app.database.database import Base, get_db
from backend.app.models.users import AdminDetails, StudentDetails
from backend.app.routers.admin import router as admin_router
from backend.app.routers.users import router as user_router


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)
    next_student_registration_id = 22072000
    next_admin_id = 1001

    @event.listens_for(StudentDetails, "before_insert")
    def assign_student_registration_id(mapper, connection, student):
        nonlocal next_student_registration_id
        if student.registration_id is None:
            student.registration_id = next_student_registration_id
            next_student_registration_id += 1

    @event.listens_for(AdminDetails, "before_insert")
    def assign_admin_id(mapper, connection, admin):
        nonlocal next_admin_id
        if admin.admin_id is None:
            admin.admin_id = next_admin_id
            next_admin_id += 1

    Base.metadata.create_all(engine)
    db = TestingSessionLocal()
    db.add(
        AdminDetails(
            admin_id=1000,
            admin_name="Test Admin",
            email="admin@example.com",
            hashed_pass=hash_password("secret"),
            role="admin",
        )
    )
    db.commit()
    db.close()

    test_app = FastAPI()
    test_app.include_router(user_router)
    test_app.include_router(admin_router)

    @test_app.get("/")
    def home():
        return {"message": "this is the start of student management api"}

    def override_get_db():
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    event.remove(StudentDetails, "before_insert", assign_student_registration_id)
    event.remove(AdminDetails, "before_insert", assign_admin_id)
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_all_api_endpoints(client):
    root_response = client.get("/")
    assert root_response.status_code == 200
    assert root_response.json()["message"] == "this is the start of student management api"

    student_registration = client.post(
        "/students/registration",
        json={
            "student_name": "Test Student",
            "email": "student@example.com",
            "password": "secret",
        },
    )
    assert student_registration.status_code == 201
    student = student_registration.json()
    assert student["registration_id"] == 22072000

    student_login = client.post(
        "/students/student_login",
        data={"username": str(student["registration_id"]), "password": "secret"},
    )
    assert student_login.status_code == 200
    student_tokens = student_login.json()
    assert student_tokens["token_type"] == "bearer"

    student_me = client.get(
        "/students/me",
        headers={"Authorization": f"Bearer {student_tokens['access_token']}"},
    )
    assert student_me.status_code == 200
    assert student_me.json()["message"] == "welcome to student management system"

    student_logout = client.post(
        "/students/logout",
        params={"refresh_token": student_tokens["refresh_token"]},
    )
    assert student_logout.status_code == 200
    assert student_logout.json()["message"] == "logout successfully"

    admin_login = client.post(
        "/admin/login",
        json={"admin_id": 1000, "password": "secret"},
    )
    assert admin_login.status_code == 200
    admin_tokens = admin_login.json()
    assert admin_tokens["token_type"] == "bearer"

    admin_registration = client.post(
        "/admin/registration",
        json={
            "admin_name": "Second Admin",
            "email": "second-admin@example.com",
            "password": "secret",
        },
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert admin_registration.status_code == 201
    assert admin_registration.json()["admin_id"] == 1001
    assert admin_registration.json()["role"] == "admin"

    admin_logout = client.post(
        "/admin/logout",
        params={"refresh_token": admin_tokens["refresh_token"]},
    )
    assert admin_logout.status_code == 200
    assert admin_logout.json()["message"] == "logout successfully"


def test_student_refresh_token_flow(client):
    registration = client.post(
        "/students/registration",
        json={
            "student_name": "Refresh Student",
            "email": "refresh-student@example.com",
            "password": "secret",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/students/student_login",
        data={"username": str(registration.json()["registration_id"]), "password": "secret"},
    )
    assert login.status_code == 200
    refresh_token = login.json()["refresh_token"]

    refreshed = client.post(
        "/students/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["token_type"] == "bearer"
    assert refreshed.json()["access_token"]
    assert refreshed.json()["refresh_token"] != refresh_token


def test_rate_limit_uses_forwarded_client_ip(monkeypatch):
    calls = {}

    class FakeRedis:
        def incr(self, key):
            calls["incr_key"] = key
            return 1

        def expire(self, key, ttl):
            calls["expire_key"] = key
            calls["expire_ttl"] = ttl

    monkeypatch.setattr("backend.app.core.rate_limiter.redis_client", FakeRedis())

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/students/student_login",
            "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.1")],
            "client": ("127.0.0.1", 12345),
        }
    )

    rate_limit(request=request, key_prefix="student_login", limit=5, window=60)

    assert calls["incr_key"] == "student_login:203.0.113.10"
    assert calls["expire_key"] == "student_login:203.0.113.10"
    assert calls["expire_ttl"] == 60
