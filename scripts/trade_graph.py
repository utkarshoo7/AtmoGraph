from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping

import networkx as nx


IC_HS_CODES = frozenset({"854231", "854232", "854233", "854239"})
SOURCE_NAME = "UN Comtrade"


def _required_text(row: Mapping[str, object], field: str, row_number: int) -> str:
    value = row.get(field)
    if value is None or not str(value).strip():
        raise ValueError(f"Row {row_number}: missing required field '{field}'")
    return str(value).strip()


def _number(
    value: object, field: str, row_number: int, *, optional: bool = False
) -> float | None:
    if value is None or str(value).strip() == "":
        if optional:
            return None
        raise ValueError(f"Row {row_number}: missing numeric field '{field}'")

    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Row {row_number}: '{field}' must be numeric, got {value!r}"
        ) from exc

    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(
            f"Row {row_number}: '{field}' must be finite and non-negative"
        )
    return parsed


def build_trade_graph(
    records: Iterable[Mapping[str, object]],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(
        name="AtmoGraph monthly integrated-circuit reported imports",
        source=SOURCE_NAME,
        hs_scope="854231,854232,854233,854239",
        direction="exporter_to_importer",
        edge_semantics="reported_import_relationship_not_physical_shipping_route",
    )

    totals: dict[tuple[str, str, str, str], dict[str, float | int]] = defaultdict(
        lambda: {
            "import_value_usd": 0.0,
            "quantity_tonnes": 0.0,
            "quantity_rows": 0,
            "source_row_count": 0,
        }
    )

    for row_number, row in enumerate(records, start=2):
        hs_code = _required_text(row, "hs_code", row_number).replace(".", "")
        if hs_code not in IC_HS_CODES:
            continue

        reporter = _required_text(row, "reporter", row_number)
        partner = _required_text(row, "partner", row_number)
        period = _required_text(row, "period", row_number)

        if len(period) != 6 or not period.isdigit():
            raise ValueError(
                f"Row {row_number}: period must use YYYYMM format, got {period!r}"
            )
        month = int(period[4:6])
        if month < 1 or month > 12:
            raise ValueError(
                f"Row {row_number}: invalid month in period {period!r}"
            )

        exporter, importer = partner, reporter
        if exporter == importer:
            continue

        import_value = _number(row.get("import_value_usd"), "import_value_usd", row_number)
        quantity = _number(
            row.get("quantity_tonnes"),
            "quantity_tonnes",
            row_number,
            optional=True,
        )

        key = (exporter, importer, period, hs_code)
        totals[key]["import_value_usd"] += import_value
        totals[key]["source_row_count"] += 1
        if quantity is not None:
            totals[key]["quantity_tonnes"] += quantity
            totals[key]["quantity_rows"] += 1

    for (exporter, importer, period, hs_code), values in totals.items():
        quantity = (
            values["quantity_tonnes"]
            if values["quantity_rows"] > 0
            else None
        )
        graph.add_edge(
            exporter,
            importer,
            key=f"{period}_{hs_code}",
            period=period,
            hs_code=hs_code,
            relationship="REPORTED_IMPORT",
            import_value_usd=values["import_value_usd"],
            quantity_tonnes=quantity,
            source=SOURCE_NAME,
            source_row_count=values["source_row_count"],
        )

    return graph


def read_trade_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"reporter", "partner", "period", "hs_code", "import_value_usd"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
        return list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert cleaned UN Comtrade IC imports into a GraphML network."
    )
    parser.add_argument("input_csv", type=Path, help="Standardized trade CSV")
    parser.add_argument(
        "output_graphml", type=Path, help="Destination .graphml file"
    )
    args = parser.parse_args()

    graph = build_trade_graph(read_trade_csv(args.input_csv))
    args.output_graphml.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, args.output_graphml)

    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Trade edges: {graph.number_of_edges()}")
    print(f"GraphML saved to: {args.output_graphml}")


if __name__ == "__main__":
    main()
