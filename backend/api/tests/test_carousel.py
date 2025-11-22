import os
import shutil
import tempfile
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.database import Base
from app.routers.carousel import router as carousel_router
from app.utils import rabbitmq_producer


def setup_test_db():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Patch database module objects
    database.engine = engine
    database.SessionLocal = TestingSessionLocal
    # Create tables
    Base.metadata.create_all(bind=engine)


def test_add_and_list_and_limit(monkeypatch):
    # Patch rabbitmq producer to no-op
    monkeypatch.setattr(rabbitmq_producer, "connect", lambda: None)
    monkeypatch.setattr(rabbitmq_producer, "publish", lambda *a, **k: None)
    monkeypatch.setattr(rabbitmq_producer, "close", lambda: None)

    setup_test_db()

    # Temporary uploads dir
    tmpdir = tempfile.mkdtemp(prefix="test_uploads_")
    # ensure the app settings use this directory
    from app.config import settings
    settings.UPLOAD_DIR = tmpdir

    app = FastAPI()
    app.include_router(carousel_router)

    client = TestClient(app)

    # Helper to upload a dummy image
    def upload(index):
        files = {"file": (f"img{index}.jpg", b"JPEGDATA", "image/jpeg")}
        data = {"orden": str(index), "created_by": "tester"}
        resp = client.post("/api/admin/carrusel", data=data, files=files)
        return resp

    # Add up to 5 images
    for i in range(1, 6):
        resp = upload(i)
        assert resp.status_code == 201, resp.text
        assert resp.json()["message"] == "Imagen agregada al carrusel"

    # Sixth should fail with exact message
    resp6 = upload(6)
    assert resp6.status_code == 400
    assert resp6.json()["message"] == "El carrusel ya tiene el número máximo de imágenes."

    # List should return 5 items
    list_resp = client.get("/api/admin/carrusel")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list)
    assert len(data) == 5

    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)
