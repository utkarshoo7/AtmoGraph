# AtmoGraph — Project Scope

> **Working title:** AtmoGraph: Integrated Circuit Supply Chain Ripple-Effect Analyzer  
> **Project category:** Data Science and Machine Learning  
> **Scope baseline:** 13 November 2026  
> **Status:** Proposed technical scope — confirm final boundaries with the project mentor before implementation.

## 1. Project overview

AtmoGraph will analyze the supply-chain ecosystem for **electronic integrated circuits (ICs)** and help users understand how a disruption affecting an upstream supplier or trading economy may expose downstream parts of the network.

The project deliberately focuses on one product family rather than attempting to model the entire global electronics industry. The trade-data boundary is **HS 8542 (electronic integrated circuits)**. The six-digit subcategories can be retained for later analysis, while the first working version may aggregate the HS 8542 family.

The system will combine:
1. Semiconductor supply-chain structure and company/input relationships.
2. International trade flows for HS 8542.
3. Selected, verifiable disruption events from news sources (as an optional extension).
4. Graph-based dependency analysis and a carefully evaluated ML baseline.
5. An interactive dashboard for inspecting dependencies and testing disruption scenarios.

## 2. Problem statement

Integrated-circuit supply chains rely on specialized inputs, providers, production stages and cross-border trade. A disruption affecting an important supplier or trading economy may therefore create risk beyond the point where the disruption began.

The project will create a data-driven representation of these dependencies, identify structurally important or highly exposed parts of the network, and estimate potential downstream trade-flow risk. It will also allow a user to introduce a hypothetical disruption and inspect the network nodes that may be exposed.

## 3. Objectives

- Build a focused dataset for the HS 8542 integrated-circuit product family.
- Represent relevant companies, inputs, processes, production stages and countries as a graph.
- Combine structural supplier information with country-to-country trade relationships where the data permits.
- Identify important nodes and concentration/dependency risks using graph analytics.
- Build a transparent disruption-propagation or scenario-analysis method.
- Evaluate a baseline model for future trade-flow stress only if the historical data supports a defensible target.
- Present the network, risk indicators, assumptions and model outputs in an interactive dashboard.

## 4. Product and data boundaries

### In scope

- Electronic integrated circuits under HS 8542.
- The 854231, 854232, 854233 and 854239 subcategories, plus 854290 parts, where classification and data availability permit.
- Companies, inputs, providers, processes and production stages represented by the selected semiconductor supply-chain source.
- Bilateral trade flows for HS 8542, retaining year, reporter/exporter, partner/importer, product code, trade value and quantity when available.
- Selected disruption events that can be tied to an identifiable company, country, input or production stage.

### Out of scope for the first version

- All electronics and all semiconductor device categories outside HS 8542.
- Claims about exact shipment-delay days, factory output loss, inventory shortages or delivery dates without corresponding ground-truth data.
- A complete, live, plant-level map of every semiconductor facility.
- A production-grade Graph Neural Network before graph size, labels and evaluation data are validated.
- Unfiltered ingestion of the full global news archive.

## 5. Candidate data sources

These are the selected starting sources. Their exact schemas, coverage, licensing/usage conditions and data quality must be checked during Week 1.

### 5.1 ETO Semiconductor Supply Chain (CSET / Emerging Technology Observatory)

Documentation: <https://www.eto.tech/dataset-docs/chipexplorer/>  
Data repository: <https://github.com/georgetown-cset/eto-supply-chain>

The published data is organized into tables including `inputs`, `providers`, `provision`, `sequence` and `stages`. It is intended to describe semiconductor supply-chain inputs, providers and production stages.

**Planned use:** Build the structural graph and inspect provider/input dependencies.

**Important limitation:** Treat this as a documented snapshot, not a time series. Do not use it alone to infer historical supplier changes or predict future disruptions. Check the dataset's country and company definitions before mapping them to physical production locations.

### 5.2 CEPII BACI international trade database

Official page: <https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37>

BACI provides harmonized bilateral trade records. The HS 2017 version is a candidate for the first HS 8542 trade panel.

**Planned use:** Create directed, weighted exporter-to-importer relationships and examine trade values/quantities over time.

**Important limitation:** Annual observations are suitable for historical trade-network analysis but provide a short sequence for forecasting. Do not claim a reliable monthly or three-month-ahead forecast from annual records alone. Record the exact BACI version and years downloaded.

### 5.3 UN Comtrade (optional validation or monthly extension)

API documentation: <https://comtradeplus.un.org/en/api-docs>

**Planned use:** Check whether monthly HS 8542 observations are sufficiently complete for selected reporter/partner countries. Use it as a complementary source or validation source, not as an assumption that monthly coverage is complete.

### 5.4 GDELT (optional disruption-event input)

Data portal: <https://www.gdeltproject.org/data.html>

**Planned use:** Find a small, filtered set of news articles about semiconductor-related factory interruptions, export restrictions, natural disasters or other supply disruptions. Store article URL, publisher, publication time, extracted entities, event category and a human-reviewed relevance flag where available.

**Important limitation:** A news mention is not proof that a supplier was disrupted or that a trade flow changed. Validate events and avoid treating article volume or sentiment as ground truth.

## 6. Proposed graph model

Use a typed graph. The first prototype can be built with NetworkX; Neo4j can be introduced if persistence and interactive graph queries add value.

### Node types

- `Company`: provider or company entity from the structural source.
- `Country`: country associated with the source's stated country field.
- `Input`: material, component, equipment or other input defined by the source.
- `Process`: manufacturing process, if represented in the source.
- `Stage`: production stage, if represented in the source.
- `DisruptionEvent`: optional, reviewed event extracted from a news item.

### Relationship types

- `PROVIDES`: company/provider supplies an input.
- `LOCATED_IN` or `HEADQUARTERED_IN`: use only when the source definition supports the relationship; preserve the meaning of the original field.
- `USED_IN`: input is used by a process or stage, where supported.
- `NEXT_STAGE`: process/stage sequence, where supported.
- `EXPORTS_TO`: reporter/exporter country to partner/importer country, with product code, year, value and quantity as edge properties.
- `AFFECTS`: reviewed disruption event to a company, country, input or stage.

Do not create a direct company-to-country trade edge unless a source explicitly supports that company-level trade relationship. Country-level trade flows and company-level supplier relationships are different evidence types and must remain distinguishable.

## 7. Analysis and modelling plan

### 7.1 Exploratory analysis

- Inspect table dimensions, field definitions, duplicate keys and missing values.
- Standardize country names/codes and product codes without discarding original identifiers.
- Summarize HS 8542 trade by year, reporter, partner and six-digit code.
- Measure concentration and changes in trading-partner dependence.
- Validate graph joins and report how many records/nodes/edges were excluded and why.

### 7.2 Graph analytics and scenario analysis

Start with interpretable methods:
- Degree and weighted degree.
- Betweenness and closeness centrality where graph structure makes them meaningful.
- PageRank, where direction and edge semantics justify it.
- Concentration measures for supplier/trade dependence.
- A documented scenario engine that applies a configurable shock to a selected node or edge and propagates exposure over supported relationships.

Every risk score must state its inputs, normalization and assumptions. A scenario result is a modelled exposure indicator, not proof that a real-world shortage or delay will occur.

### 7.3 Machine Learning

Start with a simple baseline such as a persistence/naive forecast and a Scikit-learn model (for example, Random Forest) only after a valid panel and target have been created.

A possible research target is a future decline in reported HS 8542 trade value for a country/product/partner series. The team must define the observation window and decline threshold before training, document that this is a **proxy label**, and compare the model against a baseline. Do not label a trade decline as a confirmed supply-chain disruption without independent evidence.

Use chronological train/validation/test splits. Avoid random splits that leak future information into training. If the available monthly or annual history is too short or sparse, report that forecasting is not adequately supported and keep graph-based scenario analysis as the primary predictive component.

A GCN or GraphSAGE experiment is an optional extension only if the team has enough graph observations, meaningful node/edge features, defensible labels and a valid evaluation design.

### 7.4 Evaluation

For regression: MAE, RMSE and R-squared, interpreted against a naive baseline.

For classification (only if a defensible binary target exists): precision, recall, F1-score, confusion matrix and ROC-AUC where class balance permits.

For graph/scenario analysis: sanity checks on known relationships, controlled shock tests, sensitivity analysis and clear inspection of the affected-node paths.

## 8. Proposed system workflow

1. Download and version the source datasets.
2. Validate schemas and create clean, documented intermediate tables.
3. Filter trade records to HS 8542 and retain the source product code.
4. Build graph nodes and edges with source/provenance attributes.
5. Run graph analytics and disruption scenarios.
6. Build and evaluate an ML baseline if sufficient observations exist.
7. Expose results through an API.
8. Visualize the network, filters, scenario inputs and risk outputs in the dashboard.

## 9. Suggested team responsibilities

| Workstream | Main responsibilities |
|---|---|
| Data and EDA | Source downloads, schema inspection, cleaning, HS 8542 filtering, data dictionary and trade analysis |
| Graph and ML | Graph schema, graph construction, dependency analysis, scenario propagation and model evaluation |
| NLP and application | Curated news-event extraction, API integration, dashboard and end-to-end testing |

All members should review the shared data definitions, model assumptions and final results. Work should be integrated regularly rather than left until the final week.

## 10. One-month milestone plan

| Period | Deliverable |
|---|---|
| Week 1 | Data inventory, source/version log, cleaned HS 8542 trade sample, ETO schema notes and initial EDA |
| Week 2 | First connected graph, graph-quality checks, dependency analysis and one reproducible disruption scenario |
| Week 3 | Baseline ML evaluation if data supports it; otherwise documented forecasting limitation; optional reviewed news-event prototype |
| Week 4 | Integrated dashboard, tests, reproducibility notes, report, presentation and demonstration |

## 11. Initial acceptance criteria

- The downloaded source versions and collection dates are recorded.
- HS 8542 filtering is reproducible from the original trade data.
- Graph nodes and edges retain provenance and relationship meaning.
- The team can demonstrate at least one source-supported path through the graph.
- A configurable disruption scenario produces an explainable list of exposed nodes.
- Any ML result is compared with an appropriate baseline and uses a leakage-safe chronological split.
- Unsupported claims about exact delays, inventories or factory output are excluded from the report.
- Another team member can reproduce the data preparation and main analysis from the repository instructions.

## 12. Open questions to resolve in Week 1

1. Which BACI HS 2017 release and years will be used?
2. Are monthly UN Comtrade records complete enough for the chosen country/product panel?
3. Which ETO table keys can be joined reliably, and what do its country fields represent?
4. What minimum evidence will qualify a news article as a disruption event?
5. Does the mentor expect a trained ML model, or will a transparent graph-risk simulation plus an appropriately scoped baseline satisfy the project requirement?

---

**Scope principle:** Prefer a small, traceable and reproducible system over a large graph or advanced model built on unsupported assumptions.
