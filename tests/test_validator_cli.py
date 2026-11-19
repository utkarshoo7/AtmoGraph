import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_eto_data as validator


def sample_report(*, errors=None, warnings=None):
    errors = errors or []
    warnings = warnings or []
    return {
        "tables": {},
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "table_count": 5,
            "total_rows": 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "valid": not errors,
        },
    }


class ValidatorCliTests(unittest.TestCase):
    def test_valid_report_returns_zero_and_prints_json(self):
        output = io.StringIO()
        with patch.object(validator, "validate_dataset", return_value=sample_report()):
            with contextlib.redirect_stdout(output):
                exit_code = validator.main(["--data-dir", "unused"])

        self.assertEqual(exit_code, 0)
        self.assertIn('"valid": true', output.getvalue())

    def test_validation_errors_return_one(self):
        with patch.object(
            validator, "validate_dataset",
            return_value=sample_report(errors=["bad reference"]),
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = validator.main([])

        self.assertEqual(exit_code, 1)

    def test_strict_warnings_return_one_but_default_mode_allows_them(self):
        report = sample_report(warnings=["duplicate source row"])
        with patch.object(validator, "validate_dataset", return_value=report):
            with contextlib.redirect_stdout(io.StringIO()):
                default_exit = validator.main([])
            with contextlib.redirect_stdout(io.StringIO()):
                strict_exit = validator.main(["--strict-warnings"])

        self.assertEqual(default_exit, 0)
        self.assertEqual(strict_exit, 1)

    def test_overwrite_without_download_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                validator.main(["--overwrite"])

        self.assertEqual(raised.exception.code, 2)

    def test_downloaded_filenames_are_included_in_report(self):
        output = io.StringIO()
        with patch.object(
            validator, "download_source_files", return_value=["inputs.csv"]
        ) as download, patch.object(
            validator, "validate_dataset", return_value=sample_report()
        ):
            with contextlib.redirect_stdout(output):
                exit_code = validator.main(["--download"])

        download.assert_called_once()
        self.assertEqual(exit_code, 0)
        self.assertIn('"downloaded_files": [', output.getvalue())
        self.assertIn('"inputs.csv"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
