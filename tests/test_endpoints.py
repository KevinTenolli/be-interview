from pathlib import Path
from typing import Generator
from unittest.mock import patch
from uuid import uuid4
from fastapi import status
import alembic.command
import alembic.config
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.db import get_database_session
from app.main import app
from app.models import Organisation

_ALEMBIC_INI_PATH = Path(__file__).parent.parent / "alembic.ini"

@pytest.fixture()
def test_client() -> TestClient:
    return TestClient(app)

@pytest.fixture(autouse=True)
def apply_alembic_migrations() -> Generator[None, None, None]:
    # Creates test database per test function
    test_db_file_name = f"test_{uuid4()}.db"
    database_path = Path(test_db_file_name)
    try:
        test_db_url = f"sqlite:///{test_db_file_name}"
        alembic_cfg = alembic.config.Config(_ALEMBIC_INI_PATH)
        alembic_cfg.attributes["sqlalchemy_url"] = test_db_url
        alembic.command.upgrade(alembic_cfg, "head")
        test_engine = create_engine(test_db_url, echo=True)
        with patch("app.db.get_engine") as mock_engine:
            mock_engine.return_value = test_engine
            yield
    finally:
        database_path.unlink(missing_ok=True)


def test_organisation_endpoints(test_client: TestClient) -> None:
    list_of_organisation_names_to_create = ["organisation_a", "organisation_b", "organisation_c"]

    # Validate that organisations do not exist in database
    with get_database_session() as database_session:
        organisations_before = database_session.query(Organisation).all()
        database_session.expunge_all()
    assert len(organisations_before) == 0

    # Create organisations
    for organisation_name in list_of_organisation_names_to_create:
        response = test_client.post("/api/organisations/create", json={"name": organisation_name})
        assert response.status_code == status.HTTP_200_OK

    # Validate that organisations exist in database
    with get_database_session() as database_session:
        organisations_after = database_session.query(Organisation).all()
        database_session.expunge_all()
    created_organisation_names = set(organisation.name for organisation in organisations_after)
    assert created_organisation_names == set(list_of_organisation_names_to_create)

    # Validate that created organisations can be retried via API
    response = test_client.get("/api/organisations")
    organisations = set(organisation["name"] for organisation in response.json())
    assert set(organisations) == created_organisation_names


def test_get_single_organisation(test_client: TestClient) -> None:
    response = test_client.post("/api/organisations/create", json={"name": "Test Organisation"})
    assert response.status_code == status.HTTP_200_OK
    organisation_id = response.json()["id"]

    # Fetch the created organisation by ID
    response = test_client.get(f"/api/organisations/{organisation_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Test Organisation"

    # Test with a non-existing organisation ID
    response = test_client.get("/api/organisations/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_and_get_locations(test_client: TestClient) -> None:
    # Create an organisation to associate locations with
    response = test_client.post("/api/organisations/create", json={"name": "Test Organisation for Locations"})
    assert response.status_code == status.HTTP_200_OK
    organisation_id = response.json()["id"]

    # Create locations associated with the organisation
    location_data = [
        {"organisation_id": organisation_id, "location_name": "Location 1", "longitude": 10, "latitude": 20},
        {"organisation_id": organisation_id, "location_name": "Location 2", "longitude": 15, "latitude": 25}
    ]
    for location in location_data:
        response = test_client.post("/api/organisations/create/locations", json=location)
        assert response.status_code == status.HTTP_200_OK

    # Retrieve all locations for the organisation
    response = test_client.get(f"/api/organisations/{organisation_id}/locations")
    assert response.status_code == status.HTTP_200_OK
    retrieved_locations = response.json()
    assert len(retrieved_locations) == 2
    assert {loc["location_name"] for loc in retrieved_locations} == {"Location 1", "Location 2"}


def test_get_locations_with_bounding_box(test_client: TestClient) -> None:
    # Create an organisation to associate locations with
    response = test_client.post("/api/organisations/create", json={"name": "Organisation with Bounding Box"})
    assert response.status_code == status.HTTP_200_OK
    organisation_id = response.json()["id"]

    # Create locations associated with the organisation
    location_data = [
        {"organisation_id": organisation_id, "location_name": "Location A", "longitude": 10, "latitude": 20},
        {"organisation_id": organisation_id, "location_name": "Location B", "longitude": 15, "latitude": 25},
        {"organisation_id": organisation_id, "location_name": "Location C", "longitude": 30, "latitude": 35}
    ]
    for location in location_data:
        response = test_client.post("/api/organisations/create/locations", json=location)
        assert response.status_code == status.HTTP_200_OK

    # Retrieve locations within the bounding box
    bounding_box_params = {'bounding_box': (10,10,25,25)}
    response = test_client.get(f"/api/organisations/{organisation_id}/locations", params=bounding_box_params)
    assert response.status_code == status.HTTP_200_OK

    # Validate that only Location A and Location B are returned
    retrieved_locations = response.json()
    location_names = {loc["location_name"] for loc in retrieved_locations}
    assert location_names == {"Location A", "Location B"}