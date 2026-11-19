import pytest

from scripts.trade_graph import read_trade_csv


def test_reads_valid_csv(tmp_path):
    csv_path = tmp_path / "trade.csv"
    csv_path.write_text(
        "reporter,partner,period,hs_code,import_value_usd,quantity_tonnes\n"
        "India,Taiwan,202501,854231,1200,2.5\n",
        encoding="utf-8",
    )

    records = read_trade_csv(csv_path)

    assert records == [
        {
            "reporter": "India",
            "partner": "Taiwan",
            "period": "202501",
            "hs_code": "854231",
            "import_value_usd": "1200",
            "quantity_tonnes": "2.5",
        }
    ]


def test_reads_csv_with_utf8_bom(tmp_path):
    csv_path = tmp_path / "trade_bom.csv"
    csv_path.write_text(
        "\ufeffreporter,partner,period,hs_code,import_value_usd\n"
        "India,Taiwan,202501,854231,1200\n",
        encoding="utf-8",
    )

    records = read_trade_csv(csv_path)

    assert records[0]["reporter"] == "India"
    assert records[0]["import_value_usd"] == "1200"


def test_rejects_csv_with_missing_required_columns(tmp_path):
    csv_path = tmp_path / "incomplete.csv"
    csv_path.write_text(
        "reporter,partner,period,hs_code\n"
        "India,Taiwan,202501,854231\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required columns"):
        read_trade_csv(csv_path)


def test_header_only_csv_returns_empty_records(tmp_path):
    csv_path = tmp_path / "empty_rows.csv"
    csv_path.write_text(
        "reporter,partner,period,hs_code,import_value_usd\n",
        encoding="utf-8",
    )

    assert read_trade_csv(csv_path) == []


def test_csv_without_header_is_rejected(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        read_trade_csv(csv_path)


def test_quantity_column_is_optional(tmp_path):
    csv_path = tmp_path / "without_quantity.csv"
    csv_path.write_text(
        "reporter,partner,period,hs_code,import_value_usd\n"
        "India,Taiwan,202501,854231,1200\n",
        encoding="utf-8",
    )

    records = read_trade_csv(csv_path)

    assert records[0]["import_value_usd"] == "1200"
    assert "quantity_tonnes" not in records[0]
