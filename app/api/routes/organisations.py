from typing import Optional, Tuple

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlmodel import select, Session

from app.db import get_db
from app.models import Location, Organisation, CreateOrganisation, CreateLocation

from app.infrastructure import organisations_repository

router = APIRouter()

@router.post("/create", response_model=Organisation)
def create_organisation(create_organisation: CreateOrganisation, session: Session = Depends(get_db)) -> Organisation:
    """Create an organisation."""
    organisation = organisations_repository.create_organisation(create_organisation.name, session)
    return organisation


@router.get("/", response_model=list[Organisation])
def get_organisations(session: Session = Depends(get_db)) -> list[Organisation]:
    """
    Get all organisations.
    """
    organisations = organisations_repository.get_organisations(session)
    return organisations



@router.get("/{organisation_id}", response_model=Organisation)
def get_organisation(organisation_id: int, session: Session = Depends(get_db)) -> Organisation:
    """
    Get an organisation by id.
    """
    organisation = organisations_repository.get_organisation_by_id(organisation_id, session)
    if organisation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")
    return organisation


@router.post("/create/locations")
def create_location(create_location: CreateLocation, session: Session = Depends(get_db)) -> Location:
    location = organisations_repository.create_location(
        organisation_id=create_location.organisation_id,
        location_name=create_location.location_name,
        longitude=create_location.longitude,
        latitude=create_location.latitude,
        session=session
    )
    return location

@router.get("/{organisation_id}/locations")
def get_organisation_locations(organisation_id: int,bounding_box: Optional[Tuple[int, int, int, int]] = Query(None, description="min_lat, min_lon, max_lat, max_lon"), session: Session = Depends(get_db)):
    result = organisations_repository.get_locations_by_organisation_id(organisation_id, bounding_box, session)
    return result
