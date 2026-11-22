import unittest
from pathlib import Path

from course_data import load_course


class CourseDataTests(unittest.TestCase):
    def test_port_limit_is_north_of_starboard_for_downstream_race_direction(self):
        repository_root = Path(__file__).resolve().parents[1]
        course = load_course(
            repository_root / "Resources" / "fairwaylimits.kml",
            repository_root / "Resources" / "buoys.kml",
        )

        port_point = min(course.port_limit, key=lambda point: abs(point[0] + 0.25))
        starboard_point = min(
            course.starboard_limit, key=lambda point: abs(point[0] + 0.25)
        )

        self.assertGreater(port_point[1], starboard_point[1])


if __name__ == "__main__":
    unittest.main()
