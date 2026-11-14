import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_eto_data as validator


def write_table(directory: Path, filename: str, rows: list[dict[str, str]]) -> None:
    columns = validator.TABLE_SCHEMAS[filename]
    with (directory / filename).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def valid_tables(directory: Path) -> None:
    write_table(directory, "stages.csv", [{
        "stage_id": "S2", "stage_name": "Fabrication", "description": "test",
    }])
    write_table(directory, "inputs.csv", [
        {
            "input_id": "N1", "input_name": "Silicon wafer", "type": "material_resource",
            "stage_name": "", "stage_id": "S2", "description": "test", "year": "2025",
        },
        {
            "input_id": "N2", "input_name": "Photolithography", "type": "process",
            "stage_name": "Fabrication", "stage_id": "S2", "description": "test", "year": "",
        },
    ])
    write_table(directory, "providers.csv", [
        {"provider_name": "USA", "provider_id": "P1", "provider_type": "country", "country": ""},
        {"provider_name": "Example Corp", "provider_id": "P2", "provider_type": "organization", "country": "USA"},
        # The upstream source contains repeated identical provider rows; these are warnings.
        {"provider_name": "Example Corp", "provider_id": "P2", "provider_type": "organization", "country": "USA"},
    ])
    write_table(directory, "provision.csv", [
        {
            "provider_name": "Example Corp", "provider_id": "P2",
            "provided_name": "Silicon wafer", "provided_id": "N1",
            "share_provided": "42.5", "year": "2025", "source": "test",
        },
        {
            "provider_name": "USA", "provider_id": "P1",
            "provided_name": "Fabrication", "provided_id": "S2",
            "share_provided": "100", "year": "2022", "source": "test",
        },
    ])
    write_table(directory, "sequence.csv", [{
        "input_name": "Silicon wafer", "input_id": "N1",
        "goes_into_name": "Photolithography", "goes_into_id": "N2",
        "is_type_of_name": "", "is_type_of_id": "",
    }])


class ValidateEtoDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name)
        valid_tables(self.data_dir)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_source_shape_and_stage_references(self) -> None:
        report = validator.validate_dataset(self.data_dir)
        self.assertEqual(report["errors"], [])
        self.assertTrue(report["summary"]["valid"])
        self.assertEqual(report["summary"]["table_count"], 5)
        self.assertTrue(any("same identity" in warning for warning in report["warnings"]))

    def test_unknown_provider_and_target_are_errors(self) -> None:
        path = self.data_dir / "provision.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["provider_id"] = "P999"
        rows[0]["provided_id"] = "N999"
        write_table(self.data_dir, "provision.csv", rows)
        report = validator.validate_dataset(self.data_dir)
        self.assertTrue(any("unknown ID 'P999'" in error for error in report["errors"]))
        self.assertTrue(any("unknown ID 'N999'" in error for error in report["errors"]))

    def test_invalid_share_is_rejected(self) -> None:
        path = self.data_dir / "provision.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["share_provided"] = "100.1"
        write_table(self.data_dir, "provision.csv", rows)
        report = validator.validate_dataset(self.data_dir)
        self.assertTrue(any("outside [0, 100]" in error for error in report["errors"]))

    def test_conflicting_provider_identity_is_rejected(self) -> None:
        path = self.data_dir / "providers.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[2]["provider_name"] = "Different Company"
        write_table(self.data_dir, "providers.csv", rows)
        report = validator.validate_dataset(self.data_dir)
        self.assertTrue(any("conflicting identities" in error for error in report["errors"]))

    def test_missing_required_column_is_reported(self) -> None:
        path = self.data_dir / "stages.csv"
        path.write_text("stage_id,description\nS2,test\n", encoding="utf-8")
        report = validator.validate_dataset(self.data_dir)
        self.assertTrue(any("missing required columns" in error for error in report["errors"]))

    def test_multiline_csv_fields_are_read_as_one_record(self) -> None:
        path = self.data_dir / "inputs.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["description"] = "first line\nsecond line, with comma"
        write_table(self.data_dir, "inputs.csv", rows)
        report = validator.validate_dataset(self.data_dir)
        self.assertTrue(report["summary"]["valid"])
        self.assertEqual(report["tables"]["inputs.csv"]["rows"], 2)

    def test_missing_file_is_reported(self) -> None:
        (self.data_dir / "sequence.csv").unlink()
        report = validator.validate_dataset(self.data_dir)
        self.assertTrue(any("sequence.csv: file not found" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
