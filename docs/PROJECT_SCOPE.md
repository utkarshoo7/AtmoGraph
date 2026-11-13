# AtmoGraph — Final Project Plan (Version 3)

> **Official project:** AtmoGraph — Supply Chain Ripple Effect Predictor  
> **Focused product family:** Electronic Integrated Circuits (ICs), HS heading 8542  
> **Team:** 3 interns  
> **Project build target:** 4-week MVP within the 2-month internship  
> **Scope date:** 13 November 2026  
> **Status:** Recommended technical plan; confirm the revised prediction target with the assigned mentor.

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

**Graph interpretation:** For an import record reported by country B with partner country A, create a directed edge **A → B** meaning “B reported imports of HS 8542 from A.” Weight the edge by reported trade value. Do not merge mirror exports and imports into the same edge table; use reported imports consistently to avoid double-counting.

**Country panel:** Begin with 10–15 major reporting economies selected from the actual data. Include partner economies with material trade links, then retain a manageable set of high-value partner links after EDA. Select countries based on data availability and observed trade volume—not assumptions. Target approximately 20–40 country nodes in the first graph.

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

The official AtmoGraph brief describes downstream-delay prediction. The public datasets selected here do not include verified purchase-order delivery dates, factory lead times or observed delay labels. The defensible first-version target is therefore:

**Predict whether an importing economy is likely to experience IC trade-flow stress in the next 1, 2 or 3 months.**

A trade-flow stress label can be defined as a material decline in reported HS 8542 imports relative to a seasonally comparable baseline. The drop threshold must be selected after EDA, documented before model training and checked with sensitivity analysis. For example, a 20% drop may be tested, but it must not be treated as a known industry standard.

This is a **proxy for supply stress**, not a confirmed shortage and not a delivery-delay label. The 30/60/90-day dashboard horizon refers to one-, two- and three-month trade-flow risk estimates.

If the mentor requires exact delivery-delay prediction, the team must request suitable historical order/lead-time data from the mentor or company. Do not manufacture delivery-delay labels from trade values.

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
- `IMPORTS_FROM`: importer country → exporter/partner country, with period, HS code, value and quantity properties; the direction must be clearly documented.
- `SUPPLIES_INPUT`: company/provider → input, from ETO.
- `INPUT_GOES_INTO`: input → downstream input, from ETO sequence relationships.
- `BELONGS_TO_STAGE`: process/input → production stage, where supported by ETO.
- `HEADQUARTERED_IN`: company → country, preserving the ETO headquarters meaning.
- `AFFECTS`: reviewed news event → identified company or country.

Do not treat a company's headquarters as proof that its factories are in that country. Do not invent direct company-to-country trade relationships from country-level customs records.

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

Use **spaCy**, not a fine-tuned Transformer, for the MVP:
1. Query GDELT for a narrow set of semiconductor disruption terms.
2. Retrieve headlines, available snippets, dates, publishers and article URLs.
3. Run named-entity recognition for organizations and locations.
4. Categorize disruption types using transparent keyword rules.
5. Store a human-review flag and source evidence.
6. Map an event to a graph company/country only when the entity match is sufficiently reliable.

A human-reviewed news item can trigger a scenario or add a news-risk feature. A news mention is not proof that a trade-flow change or real-world shortage occurred.

### 5.5 GNN and baseline model

**Primary ML experiment:** a small snapshot-based Graph Convolutional Network (GCN) or GraphSAGE model for country-level trade-stress classification across monthly graph snapshots.

Candidate node features:
- Recent monthly imports and exports
- 1-, 3-, 6- and 12-month lagged trade values
- Rolling averages and percentage changes
- Number of active trade partners
- Import-source HHI
- Weighted graph degree/centrality
- Reviewed disruption-event count by country/month, if available

**Target:** high/normal future IC import-flow stress for the next 1, 2 and 3 months. Define each horizon's label from future trade observations only. Features must use information available at the prediction date.

**Baselines:** seasonal-naive benchmark plus Logistic Regression or Random Forest. The GNN must be compared against these baselines; do not assume the GNN is better.

**Chronological split:** a starting proposal is 2017–2022 training, 2023 validation and 2024–2025 testing, adjusted only if actual coverage requires it. Never randomly mix future months into training.

**Evaluation:** confusion matrix, precision, recall, F1-score, PR-AUC and ROC-AUC where appropriate. Report class balance, false positives, false negatives and limitations. If monthly coverage or label counts are inadequate, make graph-based exposure simulation the main result and clearly report that the GNN could not be validated reliably.

### 5.6 Ripple-effect scenario simulator

Allow a user to:
- Select a country or a reviewed disruption event.
- Apply a configurable reduction to that country's outgoing IC trade edges.
- Recalculate direct importing-country exposure and, where justified, limited multi-hop exposure.
- Show affected nodes, paths, trade weights and risk changes.
- Compare a baseline and shocked scenario.

Use an explicit attenuation rule for multi-hop propagation and document it. A simulated risk score is not a measured delay or a guaranteed outcome.

### 5.7 API and dashboard

Use the stack specified by the project brief, but keep the first release small:
- **FastAPI:** serve risk outputs, graph data and scenario requests.
- **React + React Flow:** interactive network view with zoom, pan, node selection and risk highlighting. Use D3 only if there is a specific visualization that React Flow cannot handle.
- **Neo4j:** store and query the bounded supply graph.
- **Docker:** package the API and frontend for a reproducible local demonstration.
- **WebSocket:** implement a small update stream only if required for the demonstration; do not build a complex real-time distributed system.

Dashboard pages:
1. Dataset coverage and EDA
2. IC trade network
3. Supplier and production-stage context
4. NLP disruption feed with evidence links
5. 30/60/90-day trade-stress estimates
6. Disruption scenario comparison and affected-node paths

## 6. Hardware and training plan

Target laptop: Intel Core i7 HX, 16 GB RAM and NVIDIA RTX 4050.

The monthly trade panel and bounded country graph should be manageable on this machine. Use CPU for Pandas, SQL, spaCy and classical baselines. Use the RTX 4050 only for the small GNN experiment if it improves training speed.

Recommended limits:
- Around 20–40 country nodes in the initial graph, subject to data coverage.
- Keep only meaningful trade edges; store raw trade data separately.
- Use compact CSV/Parquet files and avoid loading every global partner/month into memory.
- Use a small 2-layer GNN, modest hidden size and early stopping.
- Do not fine-tune an LLM or Transformer in the first version.

## 7. Technology stack

| Layer | Technology |
|---|---|
| Data and EDA | Python, Pandas, NumPy, Matplotlib, Seaborn |
| SQL | SQLite or MySQL for structured queries |
| Graph storage | Neo4j Community |
| Graph analysis | NetworkX |
| NLP | spaCy |
| Classical ML | Scikit-learn |
| GNN | PyTorch + PyTorch Geometric |
| API | FastAPI |
| Frontend | React + React Flow |
| Experiment tracking | MLflow (local, if time permits) |
| Packaging | Docker |
| Version control/testing | GitHub + GitHub Actions |

## 8. Team of three — work allocation

| Member | Ownership | Main deliverables |
|---|---|---|
| Member 1 — Data/SQL | UN Comtrade extraction, data availability checks, HS filtering, cleaning, EDA, SQL features, dataset/version documentation | Clean monthly trade panel, EDA notebook, data dictionary |
| Member 2 — Graph/ML | Neo4j model, graph construction, NetworkX analysis, GNN/baselines, evaluation, scenario propagation | Graph schema, model notebook, evaluation report, scenario engine |
| Member 3 — NLP/Application | GDELT query and review workflow, spaCy extraction, FastAPI, React/React Flow dashboard, Docker integration | NLP event table, API, interactive dashboard |

All three members must review the graph schema, model labels and risk assumptions. Integrate work continuously; do not leave integration until the last week.

## 9. One-month MVP roadmap

| Week | Work | Exit criteria |
|---|---|---|
| 1 — Data | Confirm HS 8542 scope, test monthly data availability, retrieve a pilot and then the selected reporter panel, build clean tables, run EDA and initial SQL queries | Reproducible dataset, data dictionary, coverage report and first trade-network sample |
| 2 — Graph | Build bounded Neo4j graph, import country trade edges and ETO context, calculate concentration/centrality, create graph view | Working, source-traceable graph and dependency analysis |
| 3 — NLP + ML | Implement reviewed GDELT/spaCy event pipeline, build baselines, train/evaluate small GNN, run first disruption scenarios | Working news extraction, baseline/GNN comparison and reproducible scenario |
| 4 — Integration | FastAPI, React Flow dashboard, 30/60/90-day risk views, tests, Docker, report, PPT and demo | End-to-end local demonstration and complete submission package |

## 10. Second-month improvements and training alignment

The assignment letter gives the internship a two-month duration but a one-month project-completion duration. Complete the MVP in the first month. Use the remaining internship time for deeper validation and packaging, subject to mentor direction.

Map the DSML session plan to the project:
- NumPy/Pandas, cleaning, missing values and EDA: Week 1.
- SQL, joins, CTEs and window functions: data preparation.
- Statistics/probability: concentration analysis and shock thresholds.
- Regression/classification and tree models: baselines where appropriate.
- K-Means/PCA: optional exploratory grouping, not a substitute for the main prediction task.
- Scikit-learn pipelines and data leakage: model preparation and validation.
- NLP: spaCy event extraction.
- Deep learning/GNN: bounded PyTorch Geometric experiment.
- MLOps: MLflow experiment tracking and data/model version notes.
- Serving/deployment: FastAPI and Docker.
- CI/CD: GitHub Actions for unit tests and schema checks.

Do not add Computer Vision, LLM fine-tuning, cloud infrastructure or a complex WebSocket platform unless the mentor specifically requires it and the core project is already stable.

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
1. Every trade edge can be traced to a reporter, partner, period, product and source record.
2. Missing periods are not silently changed to zero.
3. HS revision and all query filters are documented.
4. Company HQ links are not represented as factory locations.
5. Every news-driven event includes a source URL and a review status.
6. The model uses time-safe chronological splits and is compared to baselines.
7. GNN results are not overstated if the baseline performs better or test coverage is weak.
8. The demo shows a real trade-network scenario and explains what is observed, derived and simulated.
9. Exact delay forecasts are excluded unless genuine delay labels are obtained.

## 12. Explicit exclusions for the first release

- All electronics beyond the selected IC product family.
- A global all-country graph with every commodity.
- A full factory/port/logistics route map without reliable location and route data.
- Exact delivery-delay, inventory or production-capacity forecasts without ground truth.
- Fine-tuned Transformers/LLMs, computer vision and reinforcement learning.
- Cloud-scale deployment or complex streaming infrastructure.
- Fabricated supplier links, synthetic delivery-delay labels or unsupported claims.

## 13. Mentor approval item — must be resolved before final model training

The official AtmoGraph brief describes a GNN predicting downstream delivery delays. The selected public sources do not provide measured order lead times or delivery-delay labels.

Present this proposed adjustment to the mentor:

> “We will focus on electronic integrated circuits (HS 8542), build a country-level monthly import network from UN Comtrade, enrich it with named semiconductor company/input relationships from ETO, and use NLP to identify relevant disruption news. Our GNN will estimate 30/60/90-day IC trade-flow stress and the dashboard will simulate downstream exposure. Since the public sources do not contain actual order-delay labels, we will not claim exact delivery-delay prediction. If delay prediction is mandatory, can the company provide historical shipment/lead-time data?”

If the mentor rejects the proxy target, request the required delay dataset before changing the model. Do not build a delay model on invented labels.

---

**Final scope principle:** One product family, one primary historical trade dataset, a small named semiconductor context graph, a narrow news feed, one evaluated graph model and one working dashboard. Deliver a defensible system before adding complexity.
