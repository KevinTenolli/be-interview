from typing import List, Optional, Tuple
from sqlmodel import select, Session
from app.models import Location, Organisation

def create_organisation(name: str, session: Session) -> Organisation:
    organisation = Organisation(name=name)
    session.add(organisation)
    session.commit()
    session.refresh(organisation)
    return organisation

def get_organisations(session: Session) -> List[Organisation]:
    return session.exec(select(Organisation)).all()

def get_organisation_by_id(organisation_id: int, session: Session) -> Optional[Organisation]:
    return session.get(Organisation, organisation_id)

def create_location(
    organisation_id: int,
    location_name: str,
    longitude: float,
    latitude: float,
    session: Session
) -> Location:
    location = Location(
        organisation_id=organisation_id,
        location_name=location_name,
        longitude=longitude,
        latitude=latitude
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location

def get_locations_by_organisation_id(
    organisation_id: int,
    bounding_box: Optional[Tuple[float, float, float, float]],
    session: Session
) -> List[dict]:
    query = select(Location.location_name, Location.longitude, Location.latitude).where(Location.organisation_id == organisation_id)

    if bounding_box:
        min_lat, min_lon, max_lat, max_lon = bounding_box
        query = query.where(
            Location.latitude >= min_lat,
            Location.latitude <= max_lat,
            Location.longitude >= min_lon,
            Location.longitude <= max_lon
        )

    locations = session.exec(query).all()
    return [
        {
            "location_name": location.location_name,
            "location_longitude": location.longitude,
            "location_latitude": location.latitude
        }
        for location in locations
    ]