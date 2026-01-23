from fastapi.testclient import TestClient
from web_app import app
from unittest.mock import patch

client = TestClient(app)


@patch("web_app.SessionLocal")
def test_api_upload(mock_db):
    # Mock DB
    mock_session = mock_db.return_value
    mock_session.add.return_value = None
    mock_session.commit.return_value = None

    # Test upload without API key
    response = client.post("/api/upload")
    assert response.status_code == 401

    # Test with invalid key
    response = client.post("/api/upload", headers={"X-API-Key": "invalid"})
    assert response.status_code == 401

    # Note: Full test requires mocking API key validation and file processing
