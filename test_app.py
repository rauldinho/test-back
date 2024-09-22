# test_app.py
import pytest
from app import app, db
from models import Service, Incident, Team, EscalationPolicy


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client


def test_index_view(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200


def test_download_csv(client):
    """Test CSV download for total services."""
    response = client.get('/download_csv/total_services')
    assert response.status_code == 200
    assert 'text/csv' in response.content_type
    content = response.get_data(as_text=True)
    assert 'total_services' in content
