"""Plot the fairway and optionally overlay GPS tracks from the command line."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from course_analysis import build_centerline, build_fairway_polygon, calculate_steering_metrics
from course_data import load_course, load_gpx
from course_drawing import create_course_figure


def main() -> None:
    repository_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--track",
        action="append",
        default=[],
        help="GPX file to overlay (may be provided more than once)",
    )
    parser.add_argument("--save", type=Path, help="save the figure to this image path instead of displaying it")
    parser.add_argument(
        "--label-buoys",
        action="store_true",
        help="show buoy names (labels may overlap in the tighter bends)",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="print steering metrics for each supplied GPS track",
    )
    arguments = parser.parse_args()

    course = load_course(
        repository_root / "Resources" / "fairwaylimits.kml",
        repository_root / "Resources" / "buoys.kml",
    )
    tracks = []
    for track_path in arguments.track:
        path = Path(track_path)
        track = load_gpx(path)
        tracks.append((path.stem, track))

    figure, _ = create_course_figure(course, tracks, show_buoy_names=arguments.label_buoys)
    if arguments.analyze:
        centerline = build_centerline(course.port_limit, course.starboard_limit)
        fairway_polygon = build_fairway_polygon(course.port_limit, course.starboard_limit)
        for name, track in tracks:
            metrics = calculate_steering_metrics(track, centerline, fairway_polygon)
            print(
                "{}: mean centreline deviation {:.1f} m; max {:.1f} m; "
                "outside {:.1f} s ({:.1f}% of recorded time)".format(
                    name,
                    metrics.mean_centerline_deviation_m,
                    metrics.max_centerline_deviation_m,
                    metrics.time_outside_channel_seconds,
                    metrics.time_outside_channel_percent,
                )
            )

    if arguments.save:
        figure.savefig(arguments.save, dpi=180, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
