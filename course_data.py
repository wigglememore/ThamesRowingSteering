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


@dataclass(frozen=True)
class TrackMetadata:
    year: str
    boat_class: str
    steerer_name: str
    race: str = "Unknown"


@dataclass(frozen=True)
class GPSTrace:
    name: str
    metadata: TrackMetadata
    points: List[TrackPoint]


BOAT_CLASSES = ("1x", "2x", "2-", "4x", "4-", "4x+", "4+", "8+", "8x+")
RACES = ("HORR", "WEHORR", "Fours Head", "Scullers Head", "Vets Head")
RACE_TOKENS = {
    ("HORR",): "HORR",
    ("WEHORR",): "WEHORR",
    ("Fours", "Head"): "Fours Head",
    ("Scullers", "Head"): "Scullers Head",
    ("Vets", "Head"): "Vets Head",
}


def parse_track_metadata(path: Path, gps_directory: Path) -> TrackMetadata:
    """Infer year, boat class, and steerer from the trace folder and filename."""
    relative_path = path.relative_to(gps_directory)
    year = relative_path.parts[0] if relative_path.parts else "Unknown"
    if len(year) != 4 or not year.isdigit():
        year = "Unknown"

    filename_parts = path.stem.split("_")
    class_index = next(
        (index for index, part in enumerate(filename_parts) if part in BOAT_CLASSES),
        None,
    )
    boat_class = filename_parts[class_index] if class_index is not None else "Unknown"
    steerer_parts = filename_parts[class_index + 1:] if class_index is not None else []
    steerer_name = " ".join(steerer_parts) if steerer_parts else "Unknown"
    event_parts = filename_parts[:class_index] if class_index is not None else filename_parts
    race = "Unknown"
    for tokens, race_name in RACE_TOKENS.items():
        if any(
            tuple(event_parts[index:index + len(tokens)]) == tokens
            for index in range(len(event_parts) - len(tokens) + 1)
        ):
            race = race_name
            break
    return TrackMetadata(year, boat_class, steerer_name, race)


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
        # The source KML names are reversed for the race's downstream direction.
        if "port" in name:
            starboard_limit = line
        elif "starboard" in name:
            port_limit = line

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
