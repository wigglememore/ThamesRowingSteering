"""Geographic helpers and steering metrics for course and GPS coordinates."""

from dataclasses import dataclass
from math import cos, hypot, pi, radians
from typing import Iterable, List, Sequence, Tuple

from course_data import Coordinate, TrackPoint


EARTH_RADIUS_M = 6371008.8


@dataclass(frozen=True)
class LocalProjection:
    """Equirectangular projection suitable for this compact river course."""

    origin: Coordinate

    def project(self, coordinate: Coordinate) -> Coordinate:
        longitude, latitude = coordinate
        origin_longitude, origin_latitude = self.origin
        return (
            EARTH_RADIUS_M * radians(longitude - origin_longitude) * cos(radians(origin_latitude)),
            EARTH_RADIUS_M * radians(latitude - origin_latitude),
        )

    def unproject(self, point: Coordinate) -> Coordinate:
        origin_longitude, origin_latitude = self.origin
        return (
            origin_longitude
            + point[0] / (EARTH_RADIUS_M * cos(radians(origin_latitude))) * 180.0 / pi,
            origin_latitude + point[1] / EARTH_RADIUS_M * 180.0 / pi,
        )


def make_projection(coordinates: Iterable[Coordinate]) -> LocalProjection:
    coordinates = list(coordinates)
    if not coordinates:
        raise ValueError("At least one coordinate is required to create a projection")
    return LocalProjection(
        (
            sum(point[0] for point in coordinates) / len(coordinates),
            sum(point[1] for point in coordinates) / len(coordinates),
        )
    )


def _distance(first: Coordinate, second: Coordinate) -> float:
    return hypot(first[0] - second[0], first[1] - second[1])


def align_boundaries(
    port_limit: Sequence[Coordinate],
    starboard_limit: Sequence[Coordinate],
    projection: LocalProjection,
) -> Tuple[List[Coordinate], List[Coordinate]]:
    """Orient the boundary lines so their corresponding ends are adjacent."""
    port = list(port_limit)
    starboard = list(starboard_limit)
    if len(port) < 2 or len(starboard) < 2:
        raise ValueError("Both fairway boundaries must contain at least two points")

    port_start = projection.project(port[0])
    port_end = projection.project(port[-1])
    same_direction = (
        _distance(port_start, projection.project(starboard[0]))
        + _distance(port_end, projection.project(starboard[-1]))
    )
    reverse_direction = (
        _distance(port_start, projection.project(starboard[-1]))
        + _distance(port_end, projection.project(starboard[0]))
    )
    if reverse_direction < same_direction:
        starboard.reverse()
    return port, starboard


def _interpolate_line(line: Sequence[Coordinate], sample_count: int,
                      projection: LocalProjection) -> List[Coordinate]:
    projected = [projection.project(point) for point in line]
    distances = [0.0]
    for first, second in zip(projected, projected[1:]):
        distances.append(distances[-1] + _distance(first, second))
    total_length = distances[-1]
    if total_length == 0:
        raise ValueError("Fairway boundary has zero length")

    result = []
    segment_index = 0
    for index in range(sample_count):
        target = total_length * index / (sample_count - 1)
        while segment_index < len(distances) - 2 and distances[segment_index + 1] < target:
            segment_index += 1
        segment_length = distances[segment_index + 1] - distances[segment_index]
        fraction = (target - distances[segment_index]) / segment_length if segment_length else 0.0
        first = projected[segment_index]
        second = projected[segment_index + 1]
        result.append(
            projection.unproject(
                (
                    first[0] + fraction * (second[0] - first[0]),
                    first[1] + fraction * (second[1] - first[1]),
                )
            )
        )
    return result


def build_centerline(
    port_limit: Sequence[Coordinate],
    starboard_limit: Sequence[Coordinate],
    projection: LocalProjection = None,
    sample_count: int = None,
) -> List[Coordinate]:
    """Return the midpoint between boundaries sampled by along-river distance."""
    if projection is None:
        projection = make_projection(list(port_limit) + list(starboard_limit))
    port, starboard = align_boundaries(port_limit, starboard_limit, projection)
    if sample_count is None:
        sample_count = max(len(port), len(starboard))
    if sample_count < 2:
        raise ValueError("Centerline sample count must be at least two")

    port_samples = _interpolate_line(port, sample_count, projection)
    starboard_samples = _interpolate_line(starboard, sample_count, projection)
    return [
        projection.unproject(
            (
                (projection.project(port_point)[0] + projection.project(starboard_point)[0]) / 2.0,
                (projection.project(port_point)[1] + projection.project(starboard_point)[1]) / 2.0,
            )
        )
        for port_point, starboard_point in zip(port_samples, starboard_samples)
    ]


def build_fairway_polygon(
    port_limit: Sequence[Coordinate],
    starboard_limit: Sequence[Coordinate],
    projection: LocalProjection = None,
) -> List[Coordinate]:
    if projection is None:
        projection = make_projection(list(port_limit) + list(starboard_limit))
    port, starboard = align_boundaries(port_limit, starboard_limit, projection)
    return port + list(reversed(starboard))


def distance_to_polyline(
    coordinate: Coordinate,
    line: Sequence[Coordinate],
    projection: LocalProjection,
) -> float:
    if not line:
        raise ValueError("Line must contain at least one point")
    point = projection.project(coordinate)
    projected_line = [projection.project(item) for item in line]
    if len(projected_line) == 1:
        return _distance(point, projected_line[0])

    minimum = float("inf")
    for first, second in zip(projected_line, projected_line[1:]):
        dx = second[0] - first[0]
        dy = second[1] - first[1]
        length_squared = dx * dx + dy * dy
        fraction = 0.0
        if length_squared:
            fraction = max(
                0.0,
                min(1.0, ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / length_squared),
            )
        nearest = (first[0] + fraction * dx, first[1] + fraction * dy)
        minimum = min(minimum, _distance(point, nearest))
    return minimum


def _point_in_polygon(point: Coordinate, polygon: Sequence[Coordinate]) -> bool:
    inside = False
    previous = polygon[-1]
    for current in polygon:
        if _distance_to_segment(point, previous, current) < 1e-7:
            return True
        if (current[1] > point[1]) != (previous[1] > point[1]):
            crossing_x = (
                (previous[0] - current[0]) * (point[1] - current[1])
                / (previous[1] - current[1])
                + current[0]
            )
            if point[0] < crossing_x:
                inside = not inside
        previous = current
    return inside


def _distance_to_segment(point: Coordinate, first: Coordinate, second: Coordinate) -> float:
    dx = second[0] - first[0]
    dy = second[1] - first[1]
    length_squared = dx * dx + dy * dy
    fraction = 0.0
    if length_squared:
        fraction = max(
            0.0,
            min(1.0, ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / length_squared),
        )
    return _distance(point, (first[0] + fraction * dx, first[1] + fraction * dy))


def _segment_intersections(first: Coordinate, second: Coordinate,
                           edge_first: Coordinate, edge_second: Coordinate) -> List[float]:
    dx = second[0] - first[0]
    dy = second[1] - first[1]
    edge_dx = edge_second[0] - edge_first[0]
    edge_dy = edge_second[1] - edge_first[1]
    denominator = dx * edge_dy - dy * edge_dx
    if abs(denominator) < 1e-12:
        return []
    offset_x = edge_first[0] - first[0]
    offset_y = edge_first[1] - first[1]
    track_fraction = (offset_x * edge_dy - offset_y * edge_dx) / denominator
    edge_fraction = (offset_x * dy - offset_y * dx) / denominator
    if 0.0 < track_fraction < 1.0 and 0.0 <= edge_fraction <= 1.0:
        return [track_fraction]
    return []


def _outside_fraction(
    first: Coordinate, second: Coordinate, polygon: Sequence[Coordinate]
) -> float:
    cuts = [0.0, 1.0]
    for edge_first, edge_second in zip(polygon, polygon[1:] + polygon[:1]):
        cuts.extend(_segment_intersections(first, second, edge_first, edge_second))
    cuts = sorted(set(cuts))
    outside = 0.0
    for start, end in zip(cuts, cuts[1:]):
        middle = (start + end) / 2.0
        point = (
            first[0] + middle * (second[0] - first[0]),
            first[1] + middle * (second[1] - first[1]),
        )
        if not _point_in_polygon(point, polygon):
            outside += end - start
    return outside


@dataclass(frozen=True)
class SteeringMetrics:
    mean_centerline_deviation_m: float
    max_centerline_deviation_m: float
    time_outside_channel_seconds: float
    recorded_duration_seconds: float

    @property
    def time_outside_channel_percent(self) -> float:
        if not self.recorded_duration_seconds:
            return 0.0
        return 100.0 * self.time_outside_channel_seconds / self.recorded_duration_seconds


def calculate_steering_metrics(
    track: Sequence[TrackPoint],
    centerline: Sequence[Coordinate],
    fairway_polygon: Sequence[Coordinate],
) -> SteeringMetrics:
    """Calculate time-weighted centerline deviation and time outside the channel."""
    if not track:
        raise ValueError("Track must contain at least one point")
    if len(centerline) < 2:
        raise ValueError("Centerline must contain at least two points")
    if len(fairway_polygon) < 3:
        raise ValueError("Fairway polygon must contain at least three points")

    all_coordinates = [point.coordinate for point in track] + list(centerline) + list(fairway_polygon)
    projection = make_projection(all_coordinates)
    projected_polygon = [projection.project(point) for point in fairway_polygon]
    track_xy = [projection.project(point.coordinate) for point in track]
    deviations = [
        distance_to_polyline(point.coordinate, centerline, projection)
        for point in track
    ]

    weighted_deviation = 0.0
    weighted_duration = 0.0
    outside_seconds = 0.0
    for index in range(1, len(track)):
        start_time = track[index - 1].timestamp
        end_time = track[index].timestamp
        if start_time is None or end_time is None:
            continue
        duration = (end_time - start_time).total_seconds()
        if duration <= 0:
            continue
        weighted_deviation += (deviations[index - 1] + deviations[index]) * 0.5 * duration
        weighted_duration += duration
        outside_seconds += duration * _outside_fraction(
            track_xy[index - 1], track_xy[index], projected_polygon
        )

    mean_deviation = (
        weighted_deviation / weighted_duration
        if weighted_duration
        else sum(deviations) / len(deviations)
    )
    return SteeringMetrics(
        mean_centerline_deviation_m=mean_deviation,
        max_centerline_deviation_m=max(deviations),
        time_outside_channel_seconds=outside_seconds,
        recorded_duration_seconds=weighted_duration,
    )
