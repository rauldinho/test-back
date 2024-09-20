import pytest
import asyncio
from app import app, db
from pagerduty_sync import fetch_and_store_data
from models import Service, Incident


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        asyncio.run(fetch_and_store_data())

    yield client


def test_data_endpoint(client):
    """Test the /data endpoint."""
    response = client.get('/data')
    json_data = response.get_json()
    print(json_data)

    assert response.status_code == 200
    assert json_data['service_name'] == 'CSG Infra provisioning'
    assert json_data['total_incidents'] == 8
