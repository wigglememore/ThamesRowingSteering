import unittest
from pathlib import Path

from course_data import BOAT_CLASSES, parse_track_metadata


class TrackMetadataTests(unittest.TestCase):
    def test_extracts_year_boat_class_and_steerer(self):
        gps_directory = Path("GPS_traces")
        for boat_class in BOAT_CLASSES:
            with self.subTest(boat_class=boat_class):
                path = gps_directory / "2024" / ("Race_{}_Alex_Smith.gpx".format(boat_class))

                metadata = parse_track_metadata(path, gps_directory)

                self.assertEqual(metadata.year, "2024")
                self.assertEqual(metadata.boat_class, boat_class)
                self.assertEqual(metadata.steerer_name, "Alex Smith")
                self.assertEqual(metadata.race, "Unknown")

    def test_extracts_supported_races_separately(self):
        gps_directory = Path("GPS_traces")
        cases = (
            ("HORR_8+_Alex.gpx", "HORR"),
            ("WEHORR_8+_Alex.gpx", "WEHORR"),
            ("Fours_Head_4x_Alex.gpx", "Fours Head"),
            ("Scullers_Head_1x_Alex.gpx", "Scullers Head"),
            ("Vets_Head_8+_Alex.gpx", "Vets Head"),
        )
        for filename, expected_race in cases:
            with self.subTest(filename=filename):
                metadata = parse_track_metadata(
                    gps_directory / "2024" / filename, gps_directory
                )
                self.assertEqual(metadata.race, expected_race)

    def test_unknown_tags_are_kept_as_unknown(self):
        gps_directory = Path("GPS_traces")
        path = gps_directory / "not-a-year" / "Race_unknown.gpx"

        metadata = parse_track_metadata(path, gps_directory)

        self.assertEqual(metadata.year, "Unknown")
        self.assertEqual(metadata.boat_class, "Unknown")
        self.assertEqual(metadata.steerer_name, "Unknown")


if __name__ == "__main__":
    unittest.main()
