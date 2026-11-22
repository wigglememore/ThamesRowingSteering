"""Load the course boundaries, buoys, and GPS tracks from KML and GPX files."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import xml.etree.ElementTree as ET


Coordinate = Tuple[float, float]
KML_NAMESPACE = "{http://www.opengis.net/kml/2.2}"
GPX_NAMESPACE = "{http://www.topografix.com/GPX/1/1}"


@dataclass(frozen=True)
class Buoy:
    name: str
    coordinate: Coordinate


@dataclass(frozen=True)
class Course:
    port_limit: List[Coordinate]
    starboard_limit: List[Coordinate]
    buoys: List[Buoy]


@dataclass(frozen=True)
class TrackPoint:
    coordinate: Coordinate
    timestamp: Optional[datetime]


def _parse_coordinates(text: Optional[str]) -> List[Coordinate]:
    if not text:
        return []
    coordinates = []
    for item in text.split():
        values = item.split(",")
        if len(values) < 2:
            raise ValueError("Invalid KML coordinate: {!r}".format(item))
        coordinates.append((float(values[0]), float(values[1])))
    return coordinates


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+0000" if value.endswith("Z") else value
    for format_string in (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            return datetime.strptime(normalized, format_string)
        except ValueError:
            pass
    raise ValueError("Invalid GPX timestamp: {!r}".format(value))


def load_course(fairway_path: Path, buoys_path: Path) -> Course:
    """Read the port/starboard LineStrings and named buoy Points from KML."""
    root = ET.parse(str(fairway_path)).getroot()
    port_limit = []
    starboard_limit = []

    for placemark in root.iter(KML_NAMESPACE + "Placemark"):
        name = placemark.findtext(KML_NAMESPACE + "name", default="").strip().lower()
        coordinates = placemark.find(KML_NAMESPACE + "LineString/" + KML_NAMESPACE + "coordinates")
        if coordinates is None:
            continue
        line = _parse_coordinates(coordinates.text)
        if "port" in name:
            port_limit = line
        elif "starboard" in name:
            starboard_limit = line

    if len(port_limit) < 2 or len(starboard_limit) < 2:
        raise ValueError("Fairway KML must contain port and starboard limit LineStrings")

    root = ET.parse(str(buoys_path)).getroot()
    buoys = []
    for placemark in root.iter(KML_NAMESPACE + "Placemark"):
        name = placemark.findtext(KML_NAMESPACE + "name", default="").strip()
        coordinates = placemark.find(KML_NAMESPACE + "Point/" + KML_NAMESPACE + "coordinates")
        if coordinates is None:
            continue
        points = _parse_coordinates(coordinates.text)
        if points:
            buoys.append(Buoy(name=name or "Unnamed buoy", coordinate=points[0]))

    return Course(port_limit, starboard_limit, buoys)


def load_gpx(path: Path) -> List[TrackPoint]:
    """Read all track points in a GPX file, retaining optional UTC timestamps."""
    root = ET.parse(str(path)).getroot()
    points = []
    for element in root.iter(GPX_NAMESPACE + "trkpt"):
        latitude = element.get("lat")
        longitude = element.get("lon")
        if latitude is None or longitude is None:
            raise ValueError("GPX track point is missing latitude or longitude")

        time_text = element.findtext(GPX_NAMESPACE + "time")
        timestamp = None
        if time_text:
            timestamp = _parse_timestamp(time_text)
        points.append(TrackPoint((float(longitude), float(latitude)), timestamp))

    if not points:
        raise ValueError("GPX file contains no track points: {}".format(path))
    return points
