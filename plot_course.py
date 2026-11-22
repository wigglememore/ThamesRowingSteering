"""Show the fairway, navigation buoys, and every available GPS track."""

from pathlib import Path

import matplotlib.pyplot as plt

from course_analysis import (
    build_centerline,
    build_fairway_polygon,
    calculate_steering_metrics,
)
from course_data import GPSTrace, load_course, load_gpx, parse_track_metadata
from course_drawing import create_course_figure


def main() -> None:
    repository_root = Path(__file__).resolve().parent
    course = load_course(
        repository_root / "Resources" / "fairwaylimits.kml",
        repository_root / "Resources" / "buoys.kml",
    )
    tracks = []
    gps_directory = repository_root / "GPS_traces"
    for path in sorted(gps_directory.rglob("*.gpx")):
        name = path.relative_to(gps_directory).with_suffix("").as_posix()
        tracks.append(
            GPSTrace(
                name=name,
                metadata=parse_track_metadata(path, gps_directory),
                points=load_gpx(path),
            )
        )

    centerline = build_centerline(course.port_limit, course.starboard_limit)
    fairway_polygon = build_fairway_polygon(course.port_limit, course.starboard_limit)
    metrics_by_track = {}
    for track in tracks:
        metrics_by_track[track.name] = calculate_steering_metrics(
            track.points, centerline, fairway_polygon
        )

    create_course_figure(course, tracks, metrics_by_track=metrics_by_track)
    plt.show()


if __name__ == "__main__":
    main()
