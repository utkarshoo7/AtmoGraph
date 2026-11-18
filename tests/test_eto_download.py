import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_eto_data as validator


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class DownloadSourceFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_downloads_all_missing_tables_from_pinned_snapshot(self):
        requested_urls = []

        def open_url(request, timeout):
            requested_urls.append(request.full_url)
            return FakeResponse(b"header\nvalue\n")

        with patch.object(validator.urllib.request, "urlopen", side_effect=open_url):
            downloaded = validator.download_source_files(self.data_dir)

        self.assertEqual(downloaded, list(validator.TABLE_SCHEMAS))
        self.assertEqual(len(requested_urls), len(validator.TABLE_SCHEMAS))
        for filename, url in zip(validator.TABLE_SCHEMAS, requested_urls):
            self.assertEqual(
                url,
                f"{validator.SOURCE_BASE_URL}/{filename}",
            )
            self.assertEqual((self.data_dir / filename).read_bytes(), b"header\nvalue\n")

    def test_existing_files_are_preserved_without_overwrite(self):
        existing = self.data_dir / "inputs.csv"
        existing.write_bytes(b"locally reviewed data")
        requested_urls = []

        def open_url(request, timeout):
            requested_urls.append(request.full_url)
            return FakeResponse(b"upstream data")

        with patch.object(validator.urllib.request, "urlopen", side_effect=open_url):
            downloaded = validator.download_source_files(self.data_dir)

        self.assertNotIn("inputs.csv", downloaded)
        self.assertEqual(existing.read_bytes(), b"locally reviewed data")
        self.assertEqual(len(requested_urls), len(validator.TABLE_SCHEMAS) - 1)

    def test_overwrite_replaces_existing_file_only_when_requested(self):
        existing = self.data_dir / "inputs.csv"
        existing.write_bytes(b"old snapshot")

        with patch.object(
            validator.urllib.request,
            "urlopen",
            return_value=FakeResponse(b"pinned snapshot"),
        ):
            downloaded = validator.download_source_files(self.data_dir, overwrite=True)

        self.assertIn("inputs.csv", downloaded)
        self.assertEqual(existing.read_bytes(), b"pinned snapshot")


if __name__ == "__main__":
    unittest.main()
