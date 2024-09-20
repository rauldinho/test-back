import pytest
from unittest.mock import patch
from app import app, db
import os


@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    app.config['TESTING'] = True
    # Use in-memory database for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_env_variables_and_data_endpoint(client):
    """Test that environment variables are loaded and the /data endpoint responds correctly."""

    # Check if environment variables are loaded
    assert os.getenv(
        'SQLALCHEMY_DATABASE_URI') is not None, "SQLALCHEMY_DATABASE_URI not loaded"
    assert os.getenv(
        'PAGERDUTY_API_KEY') is not None, "PAGERDUTY_API_KEY not loaded"

    # Mock the database response for the /data endpoint
    with patch('app.Service.query') as mock_service_query, \
            patch('app.Incident.query') as mock_incident_query:

        # Create a mock service with incidents
        mock_service = patch('models.Service', id="1", name="Test Service")
        mock_incident = patch('models.Incident', id="1",
                              title="Test Incident", status="open")

        # Mock the service with most incidents
        mock_service_query.join.return_value.group_by.return_value.order_by.return_value.first.return_value = (
            mock_service, 10)
        mock_incident_query.filter_by.return_value.all.return_value = [
            mock_incident]

        # Test the /data endpoint
        response = client.get('/data')
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["service_id"] == "1"
        assert json_data["service_name"] == "Test Service"
        assert json_data["total_incidents"] == 10
        assert json_data["incident_status_breakdown"]["open"][0]["incident_title"] == "Test Incident"
