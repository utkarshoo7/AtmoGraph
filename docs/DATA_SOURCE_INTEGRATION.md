# AtmoGraph — Data Source Integration Contract

## Purpose

This document defines how the three approved AtmoGraph sources connect to the graph and analysis layers. It is an integration contract for the Graph/ML workstream; it does not replace the Data/SQL workstream's source extraction, cleaning, coverage checks, or EDA.

Project scope: electronic integrated circuits (HS 8542). The source guide identifies UN Comtrade as the primary monthly trade source, ETO as semiconductor company/input/stage context, and GDELT as a current disruption-news signal.

## 1. Source responsibilities

| Source | Information supplied | Role in AtmoGraph | Important limitation |
|---|---|---|---|
| UN Comtrade | Monthly reporter/partner trade observations, HS code, import value, reported quantity/weight, source/status fields | Primary country trade network and monthly prediction panel | A reported trade link is not a confirmed shipping route or delivery delay |
| ETO Semiconductor Supply Chain | Providers, inputs, provision links, input sequence and production stages | Adds company and production-context relationships | Snapshot with mixed data years and missing shares; company country is ultimate-parent headquarters, not necessarily factory location |
| GDELT | Recent news article metadata and text references | Supplies candidate disruption events for review and scenario triggering | Rolling recent-news signal; not a complete historical 2017–2025 training corpus |

## 2. Graph mapping contract

### Country trade relationships

- Create a `Country` node for each country identifier after the data workstream supplies a validated country mapping.
- When country B reports imports from partner A, represent the directed relationship as A `-[:REPORTED_IMPORT]`-> B.
- Use reported import value as the edge weight.
- Preserve the observation period, HS product code, source and reporting/status evidence on the relationship or an associated observation record.
- Use import observations consistently in the first version. Do not add mirror export observations for the same flow, because that can double-count trade.
- A trade relationship must not be labelled as a physical route.

### ETO company and production context

Use only relationships supported by the ETO source records:

- `Company` `-[:SUPPLIES_INPUT]`-> `Input`
- `Input` `-[:GOES_INTO]`-> `Input`
- `Process` `-[:HAS_STAGE]`-> `ProductionStage` (only where the source provides a valid stage mapping)

Retain source identifiers and available provenance fields so that a relationship can be traced back to its ETO record. Do not infer factory locations from ultimate-parent headquarters.

### Disruption events from GDELT

- Represent an article-derived event as a candidate `DisruptionEvent` only after extraction and human review.
- Link a reviewed event to a `Country` or `Company` only after entity matching is checked.
- Retain article URL, headline, publication date, publisher and review status.
- Do not let an unreviewed entity mention automatically alter graph risk values.
- Treat GDELT as a current signal or scenario trigger, not as historical model ground truth.

## 3. Minimum provenance requirements

Every graph fact should retain enough evidence to explain where it came from.

| Graph information | Minimum provenance to retain |
|---|---|
| Trade observation | Source, period (YYYYMM), HS code, reporter, partner, reported import value, source/status fields |
| ETO relationship | Source dataset/table, source record identifiers and relationship type |
| News event | Article URL, headline, publication date, publisher and human-review status |
| Model output | Model/version, prediction timestamp, prediction horizon, target definition and input-data cutoff |
| Scenario output | Selected disrupted entity, shock magnitude, scenario parameters and timestamp |

Missing observations must remain unknown unless the source explicitly records zero trade. Do not silently convert missing months into zero-valued edges.

## 4. Graph/ML workstream boundary

The Data/SQL owner is responsible for Comtrade extraction, HS filtering, coverage checks, cleaning, EDA, SQL features, data dictionary and version log.

The Graph/ML owner consumes validated outputs to implement:

1. Neo4j schema and import logic.
2. NetworkX analysis and graph-derived features.
3. Dependency and centrality analysis.
4. Baseline and, if justified, GNN experiments.
5. Time-safe evaluation.
6. Disruption simulation.

The NLP/Application owner is responsible for GDELT review workflow, spaCy extraction, FastAPI, React/React Flow and Docker integration. Graph integration should accept only reviewed event records with evidence.

## 5. Prediction boundary

The public sources do not provide verified purchase-order delivery dates or actual lead-time delay labels. The initial target described in the team guide is future IC import trade-flow stress: whether reported HS 8542 imports fall materially below a seasonally comparable baseline over the next 1, 2 or 3 months.

This is a proxy for supply stress, not an exact delivery-delay forecast. The drop threshold must be selected after EDA, documented before training, and tested with sensitivity checks. Training and evaluation must use chronological splits and features available at prediction time.

## 6. Integration acceptance checks

- [ ] Country identifiers resolve consistently between trade records and graph nodes.
- [ ] Trade edges use reporter-imports-from-partner direction consistently.
- [ ] Trade observations retain period, HS code, value and source evidence.
- [ ] Missing months are not silently converted to zero trade.
- [ ] ETO relationships are created only where source records support them.
- [ ] ETO headquarters location is not misrepresented as factory location.
- [ ] GDELT events require human review before graph linkage or risk updates.
- [ ] Model predictions are clearly distinguished from observed data and simulated scenarios.

## Source basis

Prepared from the AtmoGraph Team Working Guide, version 1.0 (15 Nov 2026), especially Sections 2, 4–7 and 8. This document records integration rules; it does not claim that datasets have already been downloaded, validated, or loaded into Neo4j.
