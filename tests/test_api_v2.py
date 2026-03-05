import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app, get_db
from backend.core.database import Base
from backend.core.all_models import User, APIKey, Invoice
import jwt
import json
from unittest.mock import patch, MagicMock

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Add a test user
    from backend.app.main import pwd_context
    hashed_pw = pwd_context.hash("testpassword")
    user = User(username="testuser", hashed_password=hashed_pw)
    db.add(user)
    # Add a test API key
    api_key = APIKey(key="test-api-key", client_name="TestClient")
    db.add(api_key)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_login_success():
    response = client.post("/login?username=testuser&password=testpassword")
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post("/login?username=testuser&password=wrongpassword")
    assert response.status_code == 401

def test_api_upload_unauthorized():
    response = client.post("/api/upload")
    assert response.status_code == 401

@patch("backend.app.main.process_file_task.delay")
def test_api_upload_success(mock_delay):
    mock_delay.return_value.id = "test-task-id"
    
    # Create a dummy file
    file_content = b"fake invoice content"
    files = {"file": ("invoice.pdf", file_content, "application/pdf")}
    headers = {"X-API-Key": "test-api-key"}
    
    response = client.post("/api/upload", files=files, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["task_id"] == "test-task-id"

def test_api_get_results():
    db = TestingSessionLocal()
    invoice = Invoice(proveedor="Test Provider", total=100.0, fecha="2024-01-01")
    db.add(invoice)
    db.commit()
    
    headers = {"X-API-Key": "test-api-key"}
    response = client.get("/api/results", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1
    assert response.json()["data"][0]["proveedor"] == "Test Provider"

@patch("backend.app.main.redis_client")
def test_dashboard_access(mock_redis):
    # Mock redis to return None (cache miss)
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    
    # Get token
    login_res = client.post("/login?username=testuser&password=testpassword")
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/dashboard", headers=headers)
    assert response.status_code == 200
    assert "Dashboard" in response.text
