"""Show the fairway, navigation buoys, and every available GPS track."""

from pathlib import Path

import matplotlib.pyplot as plt

from course_data import load_course, load_gpx
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
        tracks.append((name, load_gpx(path)))

    create_course_figure(course, tracks, show_buoy_names=True)
    plt.show()


if __name__ == "__main__":
    main()
