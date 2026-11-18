import networkx as nx
import pytest

from scripts.trade_graph import IC_HS_CODES, build_trade_graph


def sample_record(**overrides):
    record = {
        "reporter": "India",
        "partner": "Taiwan",
        "period": "202501",
        "hs_code": "854231",
        "import_value_usd": "1200",
        "quantity_tonnes": "2.5",
    }
    record.update(overrides)
    return record


def test_builds_directed_edge_from_exporter_to_importer():
    graph = build_trade_graph([sample_record()])

    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.has_edge("Taiwan", "India")
    assert not graph.has_edge("India", "Taiwan")


def test_filters_out_of_scope_hs_codes():
    records = [
        sample_record(hs_code="854231"),
        sample_record(hs_code="854290"),
    ]

    graph = build_trade_graph(records)

    assert set(IC_HS_CODES) == {"854231", "854232", "854233", "854239"}
    assert graph.number_of_edges() == 1
    assert graph.has_edge("Taiwan", "India")


def test_aggregates_duplicate_records_for_same_trade_key():
    records = [
        sample_record(import_value_usd="1200", quantity_tonnes="2.5"),
        sample_record(import_value_usd="800", quantity_tonnes="1.5"),
    ]

    graph = build_trade_graph(records)
    edge = graph["Taiwan"]["India"]["202501_854231"]

    assert graph.number_of_edges() == 1
    assert edge["import_value_usd"] == pytest.approx(2000)
    assert edge["quantity_tonnes"] == pytest.approx(4)
    assert edge["source_row_count"] == 2


def test_missing_quantity_is_preserved_as_none():
    graph = build_trade_graph([sample_record(quantity_tonnes="")])
    edge = graph["Taiwan"]["India"]["202501_854231"]

    assert edge["quantity_tonnes"] is None


def test_rejects_invalid_period():
    with pytest.raises(ValueError, match="period"):
        build_trade_graph([sample_record(period="202513")])


@pytest.mark.parametrize("value", ["-10", "nan", "inf", "not-a-number"])
def test_rejects_invalid_import_values(value):
    with pytest.raises(ValueError):
        build_trade_graph([sample_record(import_value_usd=value)])


def test_skips_self_loops():
    graph = build_trade_graph([sample_record(partner="India")])

    assert graph.number_of_nodes() == 0
    assert graph.number_of_edges() == 0


def test_preserves_period_product_and_relationship_metadata():
    graph = build_trade_graph([sample_record()])
    edge = graph["Taiwan"]["India"]["202501_854231"]

    assert edge["period"] == "202501"
    assert edge["hs_code"] == "854231"
    assert edge["relationship"] == "REPORTED_IMPORT"
    assert edge["source"] == "UN Comtrade"
