import unittest
from datetime import datetime, timedelta, timezone

from course_analysis import (
    build_centerline,
    calculate_steering_metrics,
    make_projection,
)
from course_data import TrackPoint


class CourseAnalysisTests(unittest.TestCase):
    def test_centerline_aligns_oppositely_ordered_boundaries(self):
        port = [(-0.001, 51.0), (-0.001, 51.001)]
        starboard = [(0.001, 51.001), (0.001, 51.0)]

        centerline = build_centerline(port, starboard, sample_count=3)

        self.assertEqual(len(centerline), 3)
        self.assertAlmostEqual(centerline[0][0], 0.0, places=8)
        self.assertAlmostEqual(centerline[-1][0], 0.0, places=8)
        self.assertAlmostEqual(centerline[1][1], 51.0005, places=7)

    def test_metrics_split_time_at_channel_boundary_crossing(self):
        polygon = [
            (0.0, 0.0),
            (0.001, 0.0),
            (0.001, 0.001),
            (0.0, 0.001),
        ]
        centerline = [(0.0005, 0.0), (0.0005, 0.001)]
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        track = [
            TrackPoint((0.0005, 0.0005), start),
            TrackPoint((0.0015, 0.0005), start + timedelta(seconds=10)),
        ]

        metrics = calculate_steering_metrics(track, centerline, polygon)

        self.assertAlmostEqual(metrics.recorded_duration_seconds, 10.0)
        self.assertAlmostEqual(metrics.time_outside_channel_seconds, 5.0, places=3)
        self.assertAlmostEqual(metrics.time_outside_channel_percent, 50.0, places=2)
        self.assertGreater(metrics.mean_centerline_deviation_m, 0.0)

    def test_projection_round_trip(self):
        coordinate = (-0.25, 51.48)
        projection = make_projection([coordinate])

        restored = projection.unproject(projection.project(coordinate))

        self.assertAlmostEqual(restored[0], coordinate[0], places=10)
        self.assertAlmostEqual(restored[1], coordinate[1], places=10)


if __name__ == "__main__":
    unittest.main()
