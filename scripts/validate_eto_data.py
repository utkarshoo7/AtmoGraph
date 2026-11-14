#!/usr/bin/env python3
"""Download and validate ETO semiconductor CSV tables before graph ingestion.

Uses only the Python standard library. It checks source schemas and
cross-table references; it does not rewrite or silently repair source data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SOURCE_REPOSITORY = "georgetown-cset/eto-chip-explorer"
SOURCE_COMMIT = "98dcb7821ff96d723a2ca4ff0feed77e591b204e"
SOURCE_BASE_URL = (
    f"https://raw.githubusercontent.com/{SOURCE_REPOSITORY}/"
    f"{SOURCE_COMMIT}/data"
)

TABLE_SCHEMAS: dict[str, tuple[str, ...]] = {
    "inputs.csv": (
        "input_id", "input_name", "type", "stage_name", "stage_id",
        "description", "year", "market_share_chart_global_market_size_info",
        "market_share_chart_caption", "market_share_chart_source",
    ),
    "providers.csv": (
        "provider_name", "alias", "provider_id", "provider_type", "country",
    ),
    "provision.csv": (
        "provider_name", "provider_id", "provided_name", "provided_id",
        "share_provided", "year", "source",
    ),
    "sequence.csv": (
        "input_name", "input_id", "goes_into_name", "goes_into_id",
        "is_type_of_name", "is_type_of_id",
    ),
    "stages.csv": (
        "stage_id", "stage_name", "description",
        "market_share_chart_global_market_size_info",
        "market_share_chart_caption", "market_share_chart_source",
    ),
}


def download_source_files(
    data_dir: Path, *, overwrite: bool = False, timeout: int = 30
) -> list[str]:
    """Download source files from a pinned upstream commit; preserve existing files."""
    data_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []
    for filename in TABLE_SCHEMAS:
        destination = data_dir / filename
        if destination.exists() and not overwrite:
            continue
        request = urllib.request.Request(
            f"{SOURCE_BASE_URL}/{filename}",
            headers={"User-Agent": "AtmoGraph-ETO-validator/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
        if not payload:
            raise ValueError(f"Upstream returned an empty file for {filename}")
        temporary = destination.with_suffix(destination.suffix + ".part")
        temporary.write_bytes(payload)
        temporary.replace(destination)
        downloaded.append(filename)
    return downloaded


def _error(report: dict[str, Any], message: str) -> None:
    report["errors"].append(message)


def _warning(report: dict[str, Any], message: str) -> None:
    report["warnings"].append(message)


def _read_table(
    data_dir: Path, filename: str, required: tuple[str, ...],
    report: dict[str, Any],
) -> dict[str, Any] | None:
    path = data_dir / filename
    if not path.is_file():
        _error(report, f"{filename}: file not found at {path}")
        return None
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames
            if not headers:
                _error(report, f"{filename}: missing CSV header")
                return None
            duplicate_headers = sorted(
                name for name, count in Counter(headers).items() if count > 1
            )
            if duplicate_headers:
                _error(report, f"{filename}: duplicate headers {duplicate_headers}")
            missing = [name for name in required if name not in headers]
            if missing:
                _error(report, f"{filename}: missing required columns {missing}")
            rows = []
            for line, raw in enumerate(reader, start=2):
                if None in raw:
                    _warning(report, f"{filename}:{line}: extra values beyond header")
                rows.append({
                    key: (value or "").strip()
                    for key, value in raw.items() if key is not None
                })
    except (OSError, UnicodeError, csv.Error) as exc:
        _error(report, f"{filename}: could not read CSV: {exc}")
        return None
    report["tables"][filename] = {"rows": len(rows), "columns": len(headers)}
    return {"rows": rows, "columns": set(headers)}


def _has(table: dict[str, Any] | None, *columns: str) -> bool:
    return table is not None and set(columns).issubset(table["columns"])


def _unique_ids(
    table: dict[str, Any], filename: str, column: str,
    report: dict[str, Any],
) -> set[str]:
    values = [row.get(column, "") for row in table["rows"]]
    for value, count in Counter(v for v in values if v).items():
        if count > 1:
            _error(report, f"{filename}: duplicate {column} {value!r}")
    for line, value in enumerate(values, start=2):
        if not value:
            _error(report, f"{filename}:{line}: {column} is blank")
    return {value for value in values if value}


def _reference(
    rows: list[dict[str, str]], filename: str, column: str,
    allowed: set[str], report: dict[str, Any], *, optional: bool = False,
) -> None:
    for line, row in enumerate(rows, start=2):
        value = row.get(column, "")
        if not value and optional:
            continue
        if not value:
            _error(report, f"{filename}:{line}: {column} is blank")
        elif value not in allowed:
            _error(report, f"{filename}:{line}: {column} references unknown ID {value!r}")


def _years(rows: list[dict[str, str]], filename: str, report: dict[str, Any]) -> None:
    for line, row in enumerate(rows, start=2):
        value = row.get("year", "")
        if value and (len(value) != 4 or not value.isdigit()):
            _error(report, f"{filename}:{line}: invalid four-digit year {value!r}")


def validate_dataset(data_dir: Path) -> dict[str, Any]:
    """Validate ETO CSV headers, IDs, and cross-table references."""
    report: dict[str, Any] = {
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "data_directory": str(data_dir),
        "tables": {}, "errors": [], "warnings": [],
    }
    tables = {
        name: _read_table(data_dir, name, required, report)
        for name, required in TABLE_SCHEMAS.items()
    }
    inputs, providers, provision, sequence, stages = (
        tables["inputs.csv"], tables["providers.csv"], tables["provision.csv"],
        tables["sequence.csv"], tables["stages.csv"],
    )

    input_ids: set[str] = set()
    stage_ids: set[str] = set()
    provider_ids: set[str] = set()

    if _has(inputs, "input_id", "input_name", "type", "stage_id", "year"):
        input_ids = _unique_ids(inputs, "inputs.csv", "input_id", report)
        for line, row in enumerate(inputs["rows"], start=2):
            for field in ("input_name", "type"):
                if not row.get(field):
                    _error(report, f"inputs.csv:{line}: {field} is blank")
        _years(inputs["rows"], "inputs.csv", report)

    if _has(stages, "stage_id", "stage_name"):
        stage_ids = _unique_ids(stages, "stages.csv", "stage_id", report)
        for line, row in enumerate(stages["rows"], start=2):
            if not row.get("stage_name"):
                _error(report, f"stages.csv:{line}: stage_name is blank")

    if _has(providers, "provider_id", "provider_name", "provider_type", "country"):
        counts: Counter[str] = Counter()
        identities: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
        for line, row in enumerate(providers["rows"], start=2):
            pid = row.get("provider_id", "")
            if not pid:
                _error(report, f"providers.csv:{line}: provider_id is blank")
                continue
            counts[pid] += 1
            identities[pid].add((
                row.get("provider_name", ""), row.get("provider_type", ""),
                row.get("country", ""),
            ))
            if not row.get("provider_name"):
                _error(report, f"providers.csv:{line}: provider_name is blank")
            if row.get("provider_type") not in {"country", "organization"}:
                _warning(report, f"providers.csv:{line}: unfamiliar provider_type")
        provider_ids = set(counts)
        for pid, variants in identities.items():
            if len(variants) > 1:
                _error(report, f"providers.csv: provider_id {pid!r} has conflicting identities")
            elif counts[pid] > 1:
                _warning(
                    report,
                    f"providers.csv: {pid!r} occurs {counts[pid]} times with the same "
                    "identity; deduplicate by provider_id before graph import",
                )
        country_names = {
            row.get("provider_name", "")
            for row in providers["rows"]
            if row.get("provider_type") == "country" and row.get("provider_name")
        }
        for line, row in enumerate(providers["rows"], start=2):
            country = row.get("country", "")
            if country and country not in country_names:
                _error(report, f"providers.csv:{line}: unknown country provider {country!r}")

    if _has(inputs, "stage_id") and stage_ids:
        _reference(inputs["rows"], "inputs.csv", "stage_id", stage_ids, report, optional=True)

    if _has(provision, "provider_id", "provided_id", "share_provided", "year"):
        rows = provision["rows"]
        if provider_ids:
            _reference(rows, "provision.csv", "provider_id", provider_ids, report)
        if input_ids or stage_ids:
            # ETO provision records can point to either an input (N...) or a stage (S...).
            _reference(rows, "provision.csv", "provided_id", input_ids | stage_ids, report)
        keys = [
            (r.get("provider_id", ""), r.get("provided_id", ""), r.get("year", ""))
            for r in rows
        ]
        for key, count in Counter(keys).items():
            if key[0] and count > 1:
                _warning(report, f"provision.csv: repeated provider/target/year key {key!r}")
        for line, row in enumerate(rows, start=2):
            share = row.get("share_provided", "")
            if share:
                try:
                    number = float(share)
                except ValueError:
                    _error(report, f"provision.csv:{line}: non-numeric share_provided {share!r}")
                else:
                    if not math.isfinite(number) or not 0 <= number <= 100:
                        _error(report, f"provision.csv:{line}: share_provided outside [0, 100]")
        _years(rows, "provision.csv", report)

    if _has(sequence, "input_id", "goes_into_id", "is_type_of_id") and input_ids:
        rows = sequence["rows"]
        _reference(rows, "sequence.csv", "input_id", input_ids, report)
        _reference(rows, "sequence.csv", "goes_into_id", input_ids, report, optional=True)
        _reference(rows, "sequence.csv", "is_type_of_id", input_ids, report, optional=True)
        keys = [
            (r.get("input_id", ""), r.get("goes_into_id", ""), r.get("is_type_of_id", ""))
            for r in rows
        ]
        for key, count in Counter(keys).items():
            if key[0] and count > 1:
                _warning(report, f"sequence.csv: repeated relationship {key!r}")

    report["summary"] = {
        "table_count": len(report["tables"]),
        "total_rows": sum(table["rows"] for table in report["tables"].values()),
        "error_count": len(report["errors"]),
        "warning_count": len(report["warnings"]),
        "valid": not report["errors"],
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download and validate the pinned ETO semiconductor CSV tables."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/eto"))
    parser.add_argument(
        "--download", action="store_true",
        help="download missing CSVs from the pinned upstream commit",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="replace existing CSVs (requires --download)",
    )
    parser.add_argument(
        "--strict-warnings", action="store_true",
        help="return exit code 1 when warnings are present",
    )
    args = parser.parse_args(argv)
    if args.overwrite and not args.download:
        parser.error("--overwrite requires --download")
    downloaded: list[str] = []
    if args.download:
        try:
            downloaded = download_source_files(args.data_dir, overwrite=args.overwrite)
        except Exception as exc:
            print(json.dumps({"download_error": str(exc)}, indent=2), file=sys.stderr)
            return 2
    report = validate_dataset(args.data_dir)
    report["downloaded_files"] = downloaded
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["errors"] or (args.strict_warnings and report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
