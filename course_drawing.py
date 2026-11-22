"""Matplotlib drawing functions for the fairway, buoys, and GPS traces."""

from typing import Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from course_analysis import (
    LocalProjection,
    build_centerline,
    build_fairway_polygon,
    make_projection,
)
from course_data import Course, TrackPoint


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
    for name, boundary in (
        ("Port limit", course.port_limit),
        ("Starboard limit", course.starboard_limit),
    ):
        points = [projection.project(point) for point in boundary]
        ax.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            color="#28718d",
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
    show_names: bool = False,
) -> None:
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
        if show_names:
            ax.annotate(
                buoy.name,
                (x, y),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=7,
                zorder=6,
            )


def draw_track(
    ax: Axes,
    track: Sequence[TrackPoint],
    name: str,
    projection: LocalProjection,
) -> None:
    points = [projection.project(point.coordinate) for point in track]
    ax.plot(
        [point[0] for point in points],
        [point[1] for point in points],
        linewidth=1.2,
        alpha=0.85,
        label=name,
        zorder=4,
    )


def create_course_figure(
    course: Course,
    tracks: Sequence[Tuple[str, Sequence[TrackPoint]]] = (),
    title: str = "Thames Head of the River Race - fairway",
    show_buoy_names: bool = False,
) -> Tuple[Figure, Axes]:
    coordinates = list(course.port_limit) + list(course.starboard_limit)
    coordinates.extend(buoy.coordinate for buoy in course.buoys)
    for _, track in tracks:
        coordinates.extend(point.coordinate for point in track)
    projection = make_projection(coordinates)

    figure, ax = plt.subplots(figsize=(11, 8))
    draw_fairway(ax, course, projection)
    draw_buoys(ax, course, projection, show_buoy_names)
    for name, track in tracks:
        draw_track(ax, track, name, projection)

    ax.set_title(title)
    ax.set_xlabel("East / west (m)")
    ax.set_ylabel("North / south (m)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    figure.tight_layout()
    return figure, ax
