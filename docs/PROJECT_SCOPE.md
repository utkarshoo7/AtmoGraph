# AtmoGraph — Implementation Plan (Version 4)

> **Official project:** AtmoGraph — Supply Chain Ripple Effect Predictor  
> **Focused product family:** Electronic Integrated Circuits (ICs), HS heading 8542  
> **Team assumption:** 3 interns; confirm that the group arrangement is formally approved  
> **Build window:** 21-day MVP, planned for 15 November–5 December 2026  
> **Date check:** The assignment dates 11/05/2026–12/05/2026 are interpreted here as 5 November–5 December; confirm this because the letter also describes a two-month duration.  
> **Scope date:** 15 November 2026  
> **Status:** Revised implementation proposal. Mentor approval of the target, data coverage and team arrangement is still pending.

## 1. Final decision and why the plan changed

The previous proposal focused only on silicon wafers. That is not the strongest data choice for the requested prediction task.

In the ETO source files, the `Wafer` input is recorded against 2019 data. Its named company provider rows mostly have blank company-level market shares; only some country shares are numeric. ETO is also explicit that its dataset is a high-level snapshot, not a historical time series, and is not designed for tracking operational supply-chain changes or exact production locations.

Therefore:
- **Do not make silicon wafers the main forecasting target.**
- Keep silicon wafers as one important upstream input in the semiconductor context graph.
- Make the main product family **electronic integrated circuits (HS 8542)**, for which monthly international trade observations can be collected.
- Use ETO for named supplier/input/stage context, not as the source of historical delay labels.
- Use a small, curated news feed for NLP-driven disruption detection.

This gives the project one clearly bounded product family, real historical observations, a graph, an NLP component and a defensible ML target.

## 2. Final project title and problem statement

### AtmoGraph: Integrated Circuit Supply-Chain Ripple-Effect Predictor

Integrated-circuit supply chains involve suppliers, production inputs, manufacturing stages and cross-border trade. A disruption affecting a major trading economy or a critical upstream provider may expose other economies and connected parts of the supply network to supply risk.

AtmoGraph will construct a focused trade network for electronic integrated circuits, enrich it with semiconductor supplier and production-stage context, identify vulnerable dependencies, detect relevant disruption news, and estimate the risk of a future decline in reported IC trade flows. Users will be able to simulate a disruption and inspect which connected importers may be exposed.

**Prediction boundary:** The public data can support trade-flow stress analysis, not verified shipment-delay prediction. The application must not claim to predict exact delivery-delay days, inventory shortages, factory output losses or port transit times without corresponding ground-truth data.

## 3. Dataset plan

Use **one primary product-specific dataset** plus two small supporting sources with separate purposes. Do not download broad, unrelated Kaggle datasets.

### 3.1 Primary dataset — UN Comtrade monthly trade data

Official portal: https://comtradeplus.un.org/  
API documentation: https://comtradeplus.un.org/en/api-docs  
Subscriptions and limits: https://comtradeplus.un.org/en/subscriptions  
Product classification reference: https://unstats.un.org/unsd/classifications/Econ/Detail/EN/32/8542

**Product boundary:** HS 8542 — Electronic integrated circuits. Retain the six-digit subheadings for processors/controllers (854231), memories (854232), amplifiers (854233) and other integrated circuits (854239). Exclude parts (854290) from the main finished-IC analysis. Use one consistent HS classification revision across the selected period and document it.

**Proposed time window:** January 2017–December 2025, monthly. Verify reporting availability before finalizing the country panel.

**Fields to retain where available:**
- Reporter/importing economy
- Partner/exporting economy
- Period (YYYYMM)
- HS commodity code
- Trade flow (imports)
- Primary trade value in USD
- Net weight and/or quantity, when reported
- Data publication/observation status and source metadata

**Graph interpretation:** Keep each raw customs observation keyed by reporter/importer B, declared partner A, period and HS6. In the graph, represent it as importer B → declared partner A, with a relationship meaning “B reported imports from A.” Store reporter/partner codes, HS6, period, value, quantity, unit, classification revision and source query. This is a reported-partner relationship only: it does not prove the partner is the original manufacturer, country of origin or physical route. For downstream exposure, traverse the dependency in reverse (partner → reporting importer) and label the result reported-partner exposure. Use reported imports consistently; do not combine mirror exports into the same edge table.

**Country panel:** Begin with 10–15 major reporting economies selected from the actual data. Include partner economies with material trade links, then retain a manageable set of high-value partner links after EDA. Select countries based on data availability and observed trade volume—not assumptions. Target approximately 20–40 country nodes in the first graph.

**Trade-hub caution:** Do not automatically classify Hong Kong, Singapore or Malaysia as simple transit nodes. Some hubs also host manufacturing, assembly or testing activity, and the customs partner field does not identify the physical origin of a component. Report a sensitivity comparison with and without selected hubs; do not present either version as a verified factory-dependency map.

**Access:** UN Comtrade offers free registered individual access. The official plan lists up to 100,000 records per request and 500 API calls per day for the free tier. The no-key public preview is much more limited. Register for a free account/API key if required; premium access is not part of this project plan.

**Quality rules:**
- Check monthly availability for each selected reporter before training.
- Missing observations are not automatically zero trade.
- Keep reporter, partner, period and commodity codes in a documented lookup table.
- Record the classification revision and query parameters.
- Save the untouched raw extract separately from cleaned data.
- Use a reproducible download script and a download/version log.

### 3.2 Supporting source — ETO Semiconductor Supply Chain Dataset

Official documentation: https://www.eto.tech/dataset-docs/chipexplorer/  
CSV files: https://github.com/georgetown-cset/eto-chip-explorer/tree/main/data  
Interactive explorer: https://chipexplorer.eto.tech/

The ETO dataset contains five related CSV tables: `inputs.csv`, `providers.csv`, `provision.csv`, `sequence.csv` and `stages.csv`.

**Planned use:** Provide named semiconductor companies, provider countries, inputs, input-to-input relationships, market-share snapshots and production stages for the dashboard's context layer.

Use only the most relevant nodes and relationships for the IC supply-chain story; do not import every ETO record into the first graph if it does not contribute to the chosen use case.

**Important limitations:**
- It is a high-level snapshot, not a time series.
- Some inputs use 2019 or 2022 data while many others use 2025 data.
- Company/country attribution is generally based on the ultimate parent's headquarters, not the physical factory location.
- Market shares can be missing or rounded and should not be treated as exact production capacity.
- Do not use ETO alone to train a delay-forecasting model.

### 3.3 Supporting source — GDELT news and events

GDELT data portal: https://www.gdeltproject.org/data.html  
DOC 2.0 API documentation: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

**Planned use:** Collect a small, filtered stream of articles about semiconductor-related disruption events, such as:
- Factory shutdowns or fires
- Earthquakes, floods or other natural hazards affecting production
- Export controls or trade restrictions
- Strikes, port closures or transport interruptions
- Reported shortages or production interruptions

Store a compact evidence table with publication date, headline, source URL, publisher/domain, extracted organization, extracted country, event category, relevance review and confidence. Use a small curated/reviewed set rather than downloading the entire GDELT archive.

GDELT's DOC article-search API is best treated as a recent-news feed; do not assume it supplies a complete historical event corpus for the full 2017–2025 trade-training period. Article body availability varies by publisher. Use spaCy on available headlines/snippets or permitted article text. For the first version, use newly retrieved and human-reviewed news as an inference-time disruption signal and scenario trigger. Do **not** feed news counts into historical GNN training unless the team separately builds and validates a time-aligned historical news corpus with consistent coverage. Do not claim that GDELT's automated event coding is ground truth.

## 4. Exact prediction target

The official brief asks for a GNN that estimates downstream ripple effects. The selected public sources do not contain verified purchase-order delivery dates, factory lead times or observed shipment-delay labels. The primary measurable target is therefore **continuous node-level deviation in reported IC import quantity from a seasonal baseline**. This is a trade-flow stress proxy, not exact delivery-delay prediction.

For each importing-country node and HS6 series, predict the deviation at 1, 2 and 3 months ahead:

- Observed quantity: the reported import quantity or net weight, only where its unit is consistent for that reporter/HS6 series.
- Seasonal baseline: a predeclared statistic (for example, the median of available prior observations for the same calendar month), computed using only data available at the forecast origin.
- Target: relative deviation = (future observed quantity − seasonal baseline) / seasonal baseline. Do not calculate it when the baseline is missing, zero or not comparable.

Keep HS6 subheadings separate when their quantity units are incompatible. Do not sum unlike units. If quantity coverage is too sparse, use trade value as a separately named fallback target, not as physical supply. Where quantity is available, inspect unit value (trade value / quantity) as a price-effect diagnostic and run a value-based sensitivity check. A decline in USD value alone may reflect chip-price movements rather than lower physical volume.

The dashboard may derive a high/normal stress label from the continuous deviation, but choose its threshold after EDA, document it before final evaluation and report sensitivity to alternative thresholds. Missing observations are not zero. All features must be available at the forecast origin; future observations are used only to construct targets.

The 30/60/90-day horizon means one-, two- and three-month-ahead trade-flow deviation estimates. Do not describe these as confirmed shortages, factory-output losses, inventory depletion or delivery-delay days. If exact delay prediction is mandatory, obtain genuine historical order/shipment/lead-time labels from the mentor or company before training such a model.

## 5. System architecture

### 5.1 Data preparation
- Download and version monthly HS 8542 import records.
- Check data availability, duplicates, missing periods, country codes, product codes and outliers.
- Build a clean reporter–partner–month panel.
- Use SQL for filtering, grouping, joins and monthly feature extraction.
- Use Pandas/NumPy for cleaning and feature engineering.

### 5.2 Graph database and graph model

Use **Neo4j Community** as the project graph database, as named in the official project brief. Keep the loaded network bounded to selected countries, relevant company/provider records and relevant production inputs/stages.

Suggested node labels:
- `Country`
- `Company`
- `Input`
- `ProductionStage`
- `DisruptionEvent`

Suggested relationship types:
- **REPORTED_IMPORTS_FROM:** importer/reporting country → declared customs partner; time-stamped and source-backed, not proof of physical origin or manufacturer.
- **SUPPLIES_INPUT:** company/provider → input, from ETO.
- **INPUT_GOES_INTO:** input → downstream input, from ETO sequence relationships.
- **BELONGS_TO_STAGE:** input/process → production stage, where supported by ETO.
- **HEADQUARTERED_IN:** company → country, preserving the ETO headquarters meaning only.
- **AFFECTS:** disruption event → candidate company/country entity, with source URL, event date, extraction method, confidence and review status.

Do not treat a company's headquarters as proof that its factories are in that country. Do not invent direct company-to-country trade relationships from country-level customs records. Keep the customs trade layer and ETO production-context layer distinct; join them only through explicit, provenance-labelled relationships. For multi-hop exposure, make the reverse traversal from a reported partner to the importers that name it explicit; describe the result as reported-partner exposure, not a verified physical supply chain.

Use NetworkX for local graph analysis and PyTorch Geometric for the GNN input representation. Neo4j is the persistent graph store and interactive query layer.

### 5.3 Graph and concentration analysis

Calculate:
- Country import/export trade value trends
- Number of active trading partners
- Import-source concentration (HHI)
- Weighted in-degree/out-degree
- Betweenness or PageRank where the graph structure makes the measure meaningful
- Major supplier/importer dependencies
- Exposed downstream importers under a selected shock scenario

Label every metric as observed, derived or simulated. Avoid adding company and country market shares together; they describe overlapping levels and would double-count.

### 5.4 NLP disruption ingestion

NLP must create graph updates, not remain a manually reviewed news list:

1. Query GDELT for a narrow set of semiconductor disruption terms and retain headline, available snippet, publication time, publisher/domain and source URL.
2. Build a gazetteer from ETO provider names and aliases plus a maintained country/location list. Use spaCy EntityRuler and normalization before accepting a match.
3. Use a pretrained Hugging Face NER model as an inference-only comparator or fallback if useful; do not fine-tune a Transformer for the MVP.
4. Categorize event types with transparent rules (fire, shutdown, natural hazard, export control, strike, port/transport interruption, shortage report).
5. Create or update a DisruptionEvent node and candidate AFFECTS relationships in Neo4j. Store source URL, article date, extracted text span, entity-resolution method, confidence and review state. Low-confidence or ambiguous matches remain pending review; only accepted links should affect model features or risk scores.
6. Hand-label a target of approximately 100 headlines (or report the actual available sample) and measure organization/location entity precision, recall and F1. Record ambiguous and unmatched cases rather than hiding them.

GDELT DOC is a recent-news feed, not a complete historical event corpus for the 2017–2025 trade panel. Use it for inference-time graph updates and demonstrations; do not backfill historical GNN features from incomplete recent coverage. A news mention is evidence of a report, not proof that a disruption caused a trade decline or shortage.

### 5.5 GNN and baseline model

**Required graph model:** implement a small GraphSAGE model in PyTorch Geometric for **node regression** on monthly graph snapshots. The model predicts the continuous seasonal-baseline deviation defined in Section 4 for 1-, 2- and 3-month horizons. The GNN is a required project component, not an optional experiment; its performance must still be reported honestly.

Candidate node features, calculated only from information available at the forecast origin:
- Lagged monthly import quantity by HS6 where units are comparable; trade value and unit value as separate fields.
- 1-, 3-, 6- and 12-month lags and rolling summaries.
- Active reported trade-partner count and import-source concentration (HHI).
- Weighted graph degree/centrality, clearly marked as derived from the same trade panel.
- Accepted NLP disruption-event indicators with event date and provenance, only for periods where coverage is genuinely available.
- ETO supplier/input/stage context only where a defensible entity relationship exists; headquarters must not be treated as factory location.

**Baselines:** seasonal-naive forecast, Ridge/linear regression, Random Forest and XGBoost. Compare all models on the same chronological folds and target definition. Run an ablation comparing trade-only features with trade-plus-graph features: degree and HHI come from the same trade data, so they may add little predictive information. Do not assume GraphSAGE beats XGBoost or that graph features improve accuracy.

**Validation:** use expanding-window walk-forward validation, not one fixed split. A starting design is train through 2020 → validate 2021; expand through 2021 → validate 2022; expand through 2022 → validate 2023; then reserve 2024–2025 as a final holdout if coverage permits. Adjust dates only to documented data availability. Never shuffle months across time or allow future information into features or seasonal baselines.

**Evaluation:** report MAE and RMSE for continuous node regression, plus direction accuracy. Derive stress labels from the continuous target only for secondary classification metrics such as precision, recall, F1 and PR-AUC. Report coverage, missingness, sample counts and performance by horizon/HS6. If coverage is insufficient, report that limitation; do not silently replace the required GNN with a classifier or claim an unvalidated result.

**Experiment tracking:** MLflow is required for model runs. Log dataset/version identifiers, feature set, fold dates, parameters, metrics and model artifacts.

### 5.6 Ripple-effect scenario simulator

Allow a user to:
- Select a country or an NLP-created, source-backed disruption event.
- Apply a configurable reduction to the selected entity's relevant reported-trade exposure edges.
- Recalculate direct and limited multi-hop importer exposure, showing paths, edge provenance and the assumed attenuation at each hop.
- Compare baseline and shocked scenarios and inspect sensitivity to shock size and hop attenuation.

**Explicit limitation:** the first simulator does not model supplier substitution, spare capacity, inventory buffers or alternative sourcing. Its output is gross exposure under a stated no-substitution assumption, not a forecast of actual lost supply or delay. Make the assumption visible in the UI.

Backtest candidate historical events where the reporter/partner panel and event mapping permit: the Renesas fire (company-level event, March 2021), Malaysia COVID restrictions (2021), Shanghai lockdowns (city-level event, 2022) and Taiwan earthquake (April 2024). Compare simulated exposure rankings with seasonally adjusted observed trade deviations in predeclared post-event windows; use matched control countries or placebo windows where feasible. Report data coverage and mapping limitations. This is an association/predictive validation exercise, not causal proof. Do not map a company event to a country solely through its ETO headquarters.

### 5.7 API and dashboard

Keep the first release small but satisfy the brief's live-update requirement:
- **FastAPI:** serve risk outputs, graph data and scenario requests.
- **Neo4j:** persist and query the bounded graph, including NLP-created disruption nodes and candidate/accepted AFFECTS links.
- **FastAPI WebSocket:** publish a small event when an accepted NLP disruption updates the graph or a scenario/risk result changes. Use lightweight polling only as a fallback if WebSocket deployment is blocked.
- **React + React Flow:** interactive network view with zoom, pan, node selection, provenance details and risk highlighting.
- **Docker:** package the API and frontend for a reproducible local demonstration.

Dashboard views:
1. Dataset coverage, quantity/value quality and EDA
2. Reported IC trade-partner network
3. ETO supplier and production-stage context, with headquarters caveat
4. NLP disruption feed, extracted entities, confidence and source evidence
5. 30/60/90-day node-regression estimates and derived stress labels
6. Disruption scenario comparison, multi-hop exposure paths and simulator assumptions

## 6. Hardware and training plan

Target laptop: Intel Core i7 HX, 16 GB RAM and NVIDIA RTX 4050.

The monthly trade panel and bounded country graph should be manageable on this machine. Use CPU for Pandas, SQL, spaCy and classical baselines. Use the RTX 4050 only for the small GNN experiment if it improves training speed.

Recommended limits:
- Around 20–40 country nodes in the initial graph, subject to data coverage.
- Keep only meaningful trade edges; store raw trade data separately.
- Use compact CSV/Parquet files and avoid loading every global partner/month into memory.
- Use a small 2-layer GNN, modest hidden size and early stopping.
- Do not fine-tune an LLM or Transformer in the first version.

The GraphSAGE node-regression path must be implemented even if the first data pilot is small. If the real panel is not ready, use a clearly labelled illustrative seed graph only to exercise graph ingestion, API and UI wiring; never use mock records for model training, backtesting or performance claims.

## 7. Technology stack

| Layer | Technology |
|---|---|
| Data and EDA | Python, Pandas, NumPy, Matplotlib, Seaborn |
| SQL | SQLite or MySQL for structured queries |
| Graph storage | Neo4j Community |
| Graph analysis | NetworkX |
| NLP | spaCy EntityRuler + pretrained Hugging Face NER (inference only) |
| Classical ML | Scikit-learn + XGBoost |
| GNN | PyTorch + PyTorch Geometric |
| API | FastAPI |
| Frontend | React + React Flow |
| Experiment tracking | MLflow (required, local) |
| Live updates | FastAPI WebSocket (polling fallback) |
| Packaging | Docker |
| Version control/testing | GitHub + GitHub Actions |

## 8. Team of three — work allocation

| Member | Ownership | Main deliverables |
|---|---|---|
| Member 1 — Data/SQL | UN Comtrade pilot and extraction, HS6/classification checks, quantity-unit coverage, cleaning, EDA, seasonal baseline and SQL features | Reproducible raw/clean panel, coverage report, data dictionary and EDA |
| Member 2 — Graph/ML | Neo4j schema and import, monthly graph snapshots, GraphSAGE node regression, Ridge/Random Forest/XGBoost baselines, walk-forward evaluation, scenario engine and event backtests | Source-traceable graph, model comparison, MLflow runs, simulator and backtest report |
| Member 3 — NLP/Application | GDELT feed, ETO/country gazetteer, headline annotation/evaluation, NLP-triggered graph updates, FastAPI/WebSocket, React Flow dashboard and Docker | Evidence-linked event table, NER evaluation, API, live dashboard and reproducible demo |

All three members must review the graph semantics, prediction target, leakage rules and risk assumptions. Build and integrate a thin vertical slice together in Days 1–5; do not wait for the full Comtrade panel before starting the UI or API.

## 9. 21-day MVP roadmap

| Window | Work | Exit criteria |
|---|---|---|
| Days 1–5 — approval and vertical slice | Obtain mentor sign-off on the proxy target and brief alignment; pilot Comtrade coverage for 15–20 candidate economies; create a small illustrative seed graph; connect Neo4j, FastAPI and React Flow with a stub prediction; start the GDELT/NLP event path. | The app can display a graph and stub risk update end to end using clearly labelled mock data; the Comtrade pilot produces a real coverage report. Mock data is never used for model evaluation. |
| Days 6–12 — real data and baselines | Build the cleaned monthly panel and data dictionary; inspect quantity units, value and unit-value effects; define the seasonal baseline; run seasonal-naive, Ridge and XGBoost baselines with expanding-window validation; build the ETO/country gazetteer and annotate about 100 headlines. | Reproducible real-data panel, coverage/EDA report, baseline metrics and measured NER precision/recall. |
| Days 13–18 — graph intelligence | Build monthly trade graph snapshots and ETO context layer; implement GraphSAGE node regression; compare with baselines and run graph-feature ablation; implement the no-substitution scenario simulator and feasible historical-event backtests; wire NLP graph updates to the dashboard and WebSocket. | Evaluated GNN, documented simulator assumptions/backtest, source-backed NLP graph updates and live dashboard refresh. |
| Days 19–21 — hardening and delivery | Run tests, fix integration issues, package with Docker, verify setup instructions, freeze metrics, prepare report/PPT and rehearse the demonstration. | Reproducible end-to-end MVP and submission package; no new features added during the final window. |

The seed graph is an interface/integration fallback only. Label every illustrative node/edge as mock data and keep it separate from observed data, training and evaluation. If Comtrade coverage or quantity units fail the pilot, narrow the reporter/HS6 panel or use a separately named value-stress target; do not fabricate missing observations.

## 10. DSML alignment and required MLOps

The assignment letter's dates appear to span 5 November–5 December 2026 if read as day/month, while its text also says two months. Confirm the actual end date and whether the three-person team is formally approved. Plan against the earlier 5 December date until clarified; do not assume an extra month.

Map the DSML session plan to the project:
- NumPy/Pandas, cleaning, missing values and EDA: Comtrade panel and coverage.
- SQL, joins, CTEs and window functions: monthly feature extraction.
- Statistics/probability: seasonal baselines, concentration and shock sensitivity.
- Regression and tree models: Ridge, Random Forest and XGBoost baselines.
- Scikit-learn pipelines and data leakage: expanding-window validation.
- NLP: spaCy gazetteer/EntityRuler and pretrained Hugging Face NER inference.
- Deep learning/GNN: required GraphSAGE node-regression experiment.
- MLOps: **MLflow is required**, not optional; track data versions, parameters, folds, metrics and model artifacts.
- Serving/deployment: FastAPI, WebSocket updates and Docker.
- CI/CD: GitHub Actions for tests and schema checks.

Do not add Computer Vision, LLM fine-tuning, cloud infrastructure or complex distributed streaming unless the mentor explicitly requires them and the core deliverables are already stable.

## 11. Deliverables and acceptance checklist

Required by the internship assignment letter:
- Source code
- Project documentation
- Project report
- Presentation (PPT)
- Model evaluation results
- Final project demonstration

Additional working artifacts:
- Raw-data download instructions and version log
- Cleaned monthly trade panel
- Data dictionary and EDA notebook
- SQL queries and schema
- Neo4j graph schema/import scripts
- NLP disruption evidence table
- Baseline and GNN training/evaluation notebooks
- Model card with target definition and limitations
- Scenario tests and dashboard
- `requirements.txt` or environment file
- Dockerfile/compose file and GitHub Actions tests
- Weekly mentor progress notes

Acceptance criteria:
1. Every trade observation can be traced to reporter, declared partner, period, HS6, classification and source query.
2. Reported partner links are not described as verified origin, manufacturer, factory or physical route.
3. Missing periods and incompatible quantity units are not silently changed to zero or aggregated.
4. The seasonal baseline and all model features use only information available at the forecast origin.
5. The primary GNN is GraphSAGE node regression for continuous 30/60/90-day seasonal-baseline deviation and is compared with seasonal-naive, Ridge and XGBoost baselines.
6. Expanding-window validation and a final chronological holdout are used where coverage permits; graph-feature ablation is reported.
7. MLflow records the dataset/version, folds, parameters, metrics and artifacts.
8. NLP creates source-linked disruption graph updates with confidence and review status; NER quality is measured on a labelled sample.
9. The dashboard receives graph/risk updates through WebSocket or a documented polling fallback.
10. Scenario outputs state the no-substitution assumption and are compared with observed event-window trade deviations where coverage permits; no causal claim is made.
11. The demo distinguishes observed, derived, predicted and simulated information.
12. Exact delay forecasts are excluded unless genuine delay labels are obtained.

## 12. Explicit exclusions for the first release

- All electronics beyond the selected IC product family.
- A global all-country graph with every commodity.
- A full factory/port/logistics route map without reliable location and route data.
- Exact delivery-delay, inventory or production-capacity forecasts without ground truth.
- Fine-tuned Transformers/LLMs, computer vision and reinforcement learning.
- Cloud-scale deployment or complex streaming infrastructure.
- Fabricated supplier links, synthetic delivery-delay labels or unsupported claims.

## 13. Mentor approval item — resolve this week, before final model training

The official brief expects NLP-triggered graph updates, a GNN for multi-hop ripple effects and a live dashboard. The current public sources do not provide verified order/shipment delay labels, so the proposed primary target is continuous node-level deviation in reported IC import quantity from a seasonal baseline. The stress label is derived from that regression target.

Ask the mentor to confirm:
1. Whether this trade-flow deviation target is accepted as the measurable proxy, or whether the company can provide genuine historical delivery-delay labels.
2. That a GraphSAGE node-regression model, NLP-created Neo4j disruption updates and a live FastAPI/WebSocket dashboard satisfy the required implementation.
3. That the small seed graph may be used for the Week 1 vertical slice while real Comtrade data is being collected.
4. That the three-person team arrangement is approved, since the assignment letter is addressed to one intern.
5. The correct internship end date, because the written duration and numeric dates appear inconsistent.

Suggested mentor message:

> “We will focus on electronic integrated circuits (HS 8542), build a monthly reported-import-partner graph from UN Comtrade, and enrich it with ETO supplier/input/stage context. NLP will extract disruption entities from recent GDELT news and create source-backed event updates in Neo4j. Our required GraphSAGE model will perform node regression on 30/60/90-day deviation from a seasonal trade-quantity baseline; stress labels will be derived from that continuous output. The dashboard will show multi-hop exposure scenarios and live graph updates. Public data does not contain verified order-delay labels, so we will not claim exact delivery-delay prediction. Is this target acceptable, or can the company provide historical shipment/lead-time labels?”

Do not start final model training until the target and data-coverage approach are approved. If the mentor requires exact delay prediction, request the corresponding labelled dataset rather than manufacturing delay targets.

---

**Final scope principle:** One product family, one primary historical trade dataset, a small named semiconductor context graph, a narrow news feed, one evaluated graph model and one working dashboard. Deliver a defensible system before adding complexity.
