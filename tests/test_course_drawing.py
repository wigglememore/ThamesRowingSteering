import unittest

import matplotlib

matplotlib.use("Agg")

from course_data import Buoy, Course, GPSTrace, TrackMetadata, TrackPoint
from course_drawing import create_course_figure


class CourseDrawingTests(unittest.TestCase):
    def test_filter_widgets_control_tracks_and_buoy_labels(self):
        course = Course(
            port_limit=[(-0.001, 51.0), (-0.001, 51.001)],
            starboard_limit=[(0.001, 51.001), (0.001, 51.0)],
            buoys=[Buoy("Test buoy", (0.0, 51.0005))],
        )
        points = [
            TrackPoint((0.0, 51.0002), None),
            TrackPoint((0.0, 51.0008), None),
        ]
        tracks = [
            GPSTrace(
                "2022/HORR_8+_Alex",
                TrackMetadata("2022", "8+", "Alex", "HORR"),
                points,
            ),
            GPSTrace(
                "2024/Fours_Head_4x_Mia",
                TrackMetadata("2024", "4x", "Mia", "Fours Head"),
                points,
            ),
        ]

        figure, axes, table_axes, controls = create_course_figure(course, tracks)

        lines_by_name = {line.get_label(): line for line in axes.lines}
        self.assertTrue(lines_by_name["2022/HORR_8+_Alex"].get_visible())
        self.assertTrue(lines_by_name["2024/Fours_Head_4x_Mia"].get_visible())
        self.assertFalse(axes.texts[0].get_visible())

        controls["Year"].set_active(0)
        self.assertFalse(lines_by_name["2022/HORR_8+_Alex"].get_visible())
        self.assertTrue(lines_by_name["2024/Fours_Head_4x_Mia"].get_visible())

        controls["Year"].set_active(0)
        controls["Race"].set_active(0)
        self.assertFalse(lines_by_name["2022/HORR_8+_Alex"].get_visible())
        self.assertTrue(lines_by_name["2024/Fours_Head_4x_Mia"].get_visible())

        controls["Buoy labels"].set_active(0)
        self.assertTrue(axes.texts[0].get_visible())
        table = table_axes.tables[0]
        self.assertEqual(table[(0, 0)].get_text().get_text(), "Year")
        self.assertEqual(table[(0, 4)].get_text().get_text(), "Mean\nDeviation\n(m)")
        self.assertEqual(table[(1, 0)].get_text().get_text(), "2022")
        self.assertEqual(table[(2, 1)].get_text().get_text(), "Fours Head")
        self.assertEqual(table[(1, 8)].get_text().get_text(), "0.0")
        figure.clear()


if __name__ == "__main__":
    unittest.main()
