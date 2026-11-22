"""Matplotlib drawing functions and interactive filters for the course plot."""

from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from matplotlib.widgets import CheckButtons

from course_analysis import (
    LocalProjection,
    SteeringMetrics,
    build_centerline,
    build_fairway_polygon,
    calculate_steering_metrics,
    make_projection,
)
from course_data import BOAT_CLASSES, RACES, Course, GPSTrace


def draw_fairway(ax: Axes, course: Course, projection: LocalProjection) -> None:
    polygon = build_fairway_polygon(course.port_limit, course.starboard_limit, projection)
    polygon_xy = [projection.project(point) for point in polygon]
    ax.fill(
        [point[0] for point in polygon_xy],
        [point[1] for point in polygon_xy],
        color="#9bd3e8",
        alpha=0.35,
        label="Fairway",
        zorder=1,
    )
    for name, boundary, color in (
        ("Port limit", course.port_limit, "green"),
        ("Starboard limit", course.starboard_limit, "red"),
    ):
        points = [projection.project(point) for point in boundary]
        ax.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            color=color,
            linewidth=1.2,
            label=name,
            zorder=2,
        )

    centerline = build_centerline(course.port_limit, course.starboard_limit, projection)
    points = [projection.project(point) for point in centerline]
    ax.plot(
        [point[0] for point in points],
        [point[1] for point in points],
        color="#1e3a5f",
        linestyle="--",
        linewidth=1.4,
        label="Fairway centreline",
        zorder=3,
    )


def draw_buoys(
    ax: Axes,
    course: Course,
    projection: LocalProjection,
) -> List[Annotation]:
    labels = []
    for index, buoy in enumerate(course.buoys):
        x, y = projection.project(buoy.coordinate)
        ax.scatter(
            x,
            y,
            marker="o",
            s=24,
            color="#e08b26",
            edgecolor="white",
            linewidth=0.5,
            label="Navigation buoy" if index == 0 else "_nolegend_",
            zorder=5,
        )
        labels.append(
            ax.annotate(
                buoy.name,
                (x, y),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=7,
                visible=False,
                zorder=6,
            )
        )
    return labels


def draw_track(
    ax: Axes,
    track: GPSTrace,
    projection: LocalProjection,
) -> Line2D:
    points = [projection.project(point.coordinate) for point in track.points]
    return ax.plot(
        [point[0] for point in points],
        [point[1] for point in points],
        linewidth=1.2,
        alpha=0.85,
        label=track.name,
        zorder=4,
    )[0]


def _ordered_values(values: Sequence[str], preferred_order: Sequence[str] = ()) -> List[str]:
    unique_values = set(values)
    ordered = [value for value in preferred_order if value in unique_values]
    ordered.extend(sorted(unique_values.difference(ordered)))
    return ordered


def create_course_figure(
    course: Course,
    tracks: Sequence[GPSTrace] = (),
    title: str = "Thames Head of the River Race - fairway",
    metrics_by_track: Optional[Mapping[str, SteeringMetrics]] = None,
) -> Tuple[Figure, Axes, Axes, Dict[str, CheckButtons]]:
    coordinates = list(course.port_limit) + list(course.starboard_limit)
    coordinates.extend(buoy.coordinate for buoy in course.buoys)
    for track in tracks:
        coordinates.extend(point.coordinate for point in track.points)
    projection = make_projection(coordinates)

    tag_values = {
        "Year": _ordered_values([track.metadata.year for track in tracks]),
        "Race": _ordered_values([track.metadata.race for track in tracks], RACES),
        "Boat class": _ordered_values(
            [track.metadata.boat_class for track in tracks], BOAT_CLASSES
        ),
        "Steerer": _ordered_values([track.metadata.steerer_name for track in tracks]),
    }
    max_filter_options = max((len(values) for values in tag_values.values()), default=1)
    control_height = max(1.8, 0.3 * max_filter_options + 0.5)
    figure = plt.figure(figsize=(22, 14))
    grid = figure.add_gridspec(
        2,
        5,
        height_ratios=(5, control_height),
        hspace=0.32,
        wspace=0.28,
    )
    ax = figure.add_subplot(grid[0, :2])
    table_ax = figure.add_subplot(grid[0, 2:])
    draw_fairway(ax, course, projection)
    buoy_labels = draw_buoys(ax, course, projection)
    track_lines = [draw_track(ax, track, projection) for track in tracks]

    ax.set_title(title)
    ax.set_xlabel("East / west (m)")
    ax.set_ylabel("North / south (m)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linewidth=0.4, alpha=0.35)

    if metrics_by_track is None:
        centerline = build_centerline(course.port_limit, course.starboard_limit, projection)
        fairway_polygon = build_fairway_polygon(
            course.port_limit, course.starboard_limit, projection
        )
        metrics_by_track = {
            track.name: calculate_steering_metrics(
                track.points, centerline, fairway_polygon
            )
            for track in tracks
        }

    table_headers = (
        "Year",
        "Race",
        "Boat\nclass",
        "Steerer",
        "Mean\nDeviation\n(m)",
        "Max\nDeviation\n(m)",
        "Outside\nChannel\n(s)",
        "Outside\n(%)",
        "Recorded\n(s)",
    )
    table_rows = []
    for track in tracks:
        metrics = metrics_by_track[track.name]
        table_rows.append(
            (
                track.metadata.year,
                track.metadata.race,
                track.metadata.boat_class,
                track.metadata.steerer_name,
                "{:.1f}".format(metrics.mean_centerline_deviation_m),
                "{:.1f}".format(metrics.max_centerline_deviation_m),
                "{:.1f}".format(metrics.time_outside_channel_seconds),
                "{:.1f}".format(metrics.time_outside_channel_percent),
                "{:.1f}".format(metrics.recorded_duration_seconds),
            )
        )

    table_ax.set_title("GPS trace steering metrics", pad=12)
    table_ax.axis("off")
    table = table_ax.table(
        cellText=table_rows,
        colLabels=table_headers,
        colWidths=(0.06, 0.10, 0.075, 0.085, 0.105, 0.105, 0.105, 0.075, 0.09),
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(max(5.0, min(7.5, 72.0 / max(9, len(table_rows) + 1))))
    table.scale(1.0, 2.0)
    for (row, _column), cell in table.get_celld().items():
        if row == 0:
            cell.set_height(cell.get_height() * 1.5)
            cell.set_facecolor("#dce8f2")
            cell.set_text_props(weight="bold")
            cell.get_text().set_fontsize(7.0)
        elif row % 2 == 0:
            cell.set_facecolor("#f3f6f8")

    controls: Dict[str, CheckButtons] = {}
    control_groups = list(tag_values.items()) + [("Buoy labels", ["Show buoy names"])]
    for column, (group_name, values) in enumerate(control_groups):
        if group_name != "Buoy labels" and not values:
            continue
        widget_ax = figure.add_subplot(grid[1, column])
        active = [True] * len(values) if group_name != "Buoy labels" else [False]
        controls[group_name] = CheckButtons(widget_ax, values, active)
        widget_ax.set_title(group_name, fontsize=10, loc="left")

    def update_visibility(_label: str) -> None:
        selected = {
            group_name: {
                value
                for value, active in zip(values, controls[group_name].get_status())
                if active
            }
            for group_name, values in tag_values.items()
            if group_name in controls
        }
        for track, line in zip(tracks, track_lines):
            line.set_visible(
                all(
                    getattr(track.metadata, attribute) in selected[group_name]
                    for group_name, attribute in (
                        ("Year", "year"),
                        ("Race", "race"),
                        ("Boat class", "boat_class"),
                        ("Steerer", "steerer_name"),
                    )
                    if group_name in selected
                )
            )

        show_names = controls["Buoy labels"].get_status()[0]
        for label in buoy_labels:
            label.set_visible(show_names)
        figure.canvas.draw_idle()

    for widget in controls.values():
        widget.on_clicked(update_visibility)

    ax.legend(loc="best", fontsize=8)
    return figure, ax, table_ax, controls
