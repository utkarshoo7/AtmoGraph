# AtmoGraph — Focused Project Scope

> **Project:** AtmoGraph — Semiconductor Supply Chain Risk & Ripple-Effect Analyzer  
> **Focal case:** Silicon wafers used in semiconductor chip manufacturing  
> **Scope baseline:** 13 November 2026  
> **Team:** 3 interns  
> **Target build window:** 4 weeks  
> **Status:** Focused implementation plan; validate the selected data fields with the mentor in Week 1.

## 1. The decision: keep the project small

The first proposal was too broad: it combined semiconductor trade data, multiple international databases, news ingestion, NLP, a large graph database, a Graph Neural Network and a separate web frontend.

That is unnecessary for a three-person team with a one-month project-completion window.

The revised project will use **one core semiconductor supply-chain dataset** and focus the dashboard on **silicon wafers**, an important input used in chip manufacturing. The goal is to identify supplier concentration and dependencies, then simulate how a disruption to a supplier or country could expose connected parts of the wafer supply network.

## 2. Problem statement

Semiconductor manufacturing depends on specialized upstream inputs and a relatively concentrated set of suppliers. A disruption affecting a critical supplier can expose downstream production stages to supply risk.

AtmoGraph will represent the selected semiconductor input network as a graph, measure supplier and country concentration, identify important dependency points, and simulate the potential ripple effect of a configurable supplier or country disruption.

The system will report **structural exposure and scenario-based risk**. It will not claim to predict exact delivery-delay days, inventory shortages or future factory output because the selected dataset does not contain those ground-truth outcomes.

## 3. Core dataset — use this first

### Emerging Technology Observatory (ETO) Semiconductor Supply Chain Dataset

- Official documentation: https://www.eto.tech/dataset-docs/chipexplorer/
- CSV repository: https://github.com/georgetown-cset/eto-supply-chain/tree/main/data
- Interactive explorer: https://chipexplorer.eto.tech/

Use the September 15, 2026 release. ETO describes this as a manually compiled, high-level dataset of semiconductor production inputs, providers, companies, countries and relationships. It consists of five related CSV tables:

| File | Purpose |
|---|---|
| `inputs.csv` | Input name, type, description and production-stage information |
| `providers.csv` | Provider/company/country identifiers and provider type |
| `provision.csv` | Provider-to-input relationships and available market-share percentages |
| `sequence.csv` | Relationships between inputs, including “goes into” and subtype links |
| `stages.csv` | Semiconductor production-stage names and descriptions |

**Why this source:** It is directly about semiconductor supply chains and contains the provider/input and production-stage relationships needed to construct a graph. It is more relevant than a generic e-commerce supply-chain dataset.

### Focal case: silicon wafers

The first dashboard case study will be the wafer input and the providers connected to it. ETO's explorer lists silicon-wafer suppliers including GlobalWafers, Siltronic, SK Siltron, SUMCO and Shin-Etsu, along with other providers.

During Week 1, confirm the exact input name/identifier in `inputs.csv`, then filter `provision.csv` and `sequence.csv` to the matching input and its directly connected records. Do not manually invent supplier links.

### Important dataset limitations

- ETO is a **snapshot**, not a historical time series.
- Market-share data for most segments is from 2025, while some segments use older 2019 or 2022 data.
- Provider-country attribution is based on the ultimate parent company's headquarters, not necessarily the physical factory or production location.
- Some provider shares may be unavailable.
- The dataset is high-level and is not designed to provide exact logistics lead times, inventories or factory capacities.

Review ETO's terms of use and include the requested dataset citation in the report. Do not assume the dataset has a Creative Commons licence unless its current terms say so.

## 4. What the application will do

### Module A — Data preparation and EDA

- Load the five ETO CSV tables.
- Inspect their dimensions, columns, nulls, duplicate identifiers and join keys.
- Normalize identifiers and preserve original source values.
- Filter to the wafer input and its source-supported connected inputs/providers.
- Produce a short data dictionary and an EDA report.

### Module B — Supply-chain graph

Use **NetworkX** initially; do not add Neo4j in the first version.

Node types:
- Input
- Company/provider
- Country
- Production stage

Create only relationships supported by the source tables:
- Provider supplies input
- Input goes into another input
- Input belongs to a production stage, where the source defines that relationship
- Company is headquartered in country, preserving that meaning

Keep company-level and country-level market-share distributions separate. ETO country shares aggregate the market share of companies headquartered in that country; adding company and country shares together would double-count supply.

### Module C — Risk indicators

Calculate interpretable measures from available shares:
- Number of identified company providers
- Number of provider countries
- Largest provider share
- Top-three provider share
- Herfindahl–Hirschman Index (HHI), calculated separately at company and country level when valid shares exist
- Supplier-share entropy, where enough comparable share values exist

Treat missing or incomplete shares as unknown, not zero. State the coverage and assumptions behind every risk indicator.

### Module D — Small ML component

Use **unsupervised clustering** to group semiconductor inputs by their supplier-concentration profiles.

One modelling row represents one input category in the ETO dataset. Candidate features include provider count, country count, top-one share, top-three share, HHI and entropy. Use `StandardScaler` and `KMeans` as the first baseline. Try a small number of clusters and use silhouette score plus domain review to decide whether the clusters are meaningful.

The wafer input will be the main case study shown in the dashboard; other inputs from the same semiconductor dataset provide additional input-level observations for the clustering task.

**Be precise about what this model does:** it groups inputs by structural concentration/dependency patterns. It does not forecast a future disruption, and the cluster names “lower/moderate/higher concentration” are assigned after inspecting the cluster profiles. If there are too few valid input observations or missing share values make clustering unstable, use the transparent concentration metrics alone rather than forcing a model.

### Module E — Disruption scenario simulator

Let the user select an identified supplier or provider country and apply a hypothetical shock (for example, remove that provider's contribution or reduce its share by a chosen percentage).

Show:
- The selected provider and its source-recorded share, if available.
- Directly connected inputs.
- Downstream nodes reachable through documented graph relationships.
- A transparent exposure score based on source-supported shares and graph paths.
- A clear label that this is a scenario, not an observed historical event or a guaranteed real-world outcome.

Do not convert exposure into a delivery-delay estimate without actual lead-time labels.

### Module F — Dashboard

Use **Streamlit + Plotly + NetworkX** for the first version. A single Python application is enough for this scope.

Dashboard pages:
1. Dataset overview and coverage.
2. Wafer supplier/company and country concentration.
3. Dependency graph.
4. Supplier/country disruption scenario.
5. Model clusters and evaluation.

## 5. Technology stack — keep it lean

| Task | Technology |
|---|---|
| Data processing | Python, Pandas, NumPy |
| EDA | Matplotlib, Seaborn |
| Graph | NetworkX |
| Risk clustering | Scikit-learn (StandardScaler, KMeans, silhouette score) |
| Dashboard | Streamlit, Plotly |
| Development | Jupyter Notebook, VS Code, Git/GitHub |

Do **not** add PyTorch Geometric, a Graph Neural Network, Transformers, live news scraping, Neo4j, React, FastAPI, Docker or CI/CD to the first deliverable. These are stretch items only after the core project is working and validated.

## 6. Hardware plan

Development target: laptop with Intel Core i7 HX processor, 16 GB RAM and NVIDIA RTX 4050 Laptop GPU.

This dataset and the proposed scikit-learn/NetworkX workflow are small. They should run comfortably on the CPU; forcing GPU training would add setup complexity without improving the result. The RTX 4050 is available for a later, justified PyTorch experiment, but **GPU use is not an acceptance criterion**. Keep data in compact CSV/Parquet form, avoid loading unrelated datasets and close unused notebooks/apps if memory becomes tight.

## 7. Work allocation for three members

| Member | Ownership | Deliverables |
|---|---|---|
| Member 1 — Data | Download/version log, schema inspection, cleaning, wafer filtering, EDA and data dictionary | Reproducible cleaned tables and EDA |
| Member 2 — Graph/risk | NetworkX graph, source-supported edges, concentration metrics and disruption simulation | Graph builder, risk calculations and scenario tests |
| Member 3 — ML/app | Feature table, KMeans baseline/evaluation, Streamlit and Plotly dashboard | Model notebook, dashboard and demo |

All three members should review the graph schema and risk assumptions. Integrate every few days; do not wait until Week 4.

## 8. Four-week delivery plan

| Week | Work | Exit criteria |
|---|---|---|
| 1 | Download ETO tables, inspect data, confirm wafer input ID, document schemas and clean records | Reproducible data-loading and EDA notebook |
| 2 | Build NetworkX graph, validate joins and calculate supplier/country concentration | Working graph and verified wafer supplier view |
| 3 | Build disruption simulator and test KMeans concentration clusters | Reproducible scenarios and honest model evaluation |
| 4 | Build Streamlit dashboard, integrate, test and prepare report/PPT | End-to-end demonstration and documentation |

## 9. Evaluation and acceptance criteria

- Every node and edge has a traceable source record or a clearly labelled derived calculation.
- Company-level and country-level shares are never double-counted.
- Unknown shares are not silently treated as zero.
- The team can identify the top suppliers and concentration indicators for the wafer input where data coverage permits.
- A hypothetical supplier/country shock produces explainable affected nodes and paths.
- Clustering is retained only if the clusters are stable and interpretable; report silhouette score and limitations.
- The dashboard distinguishes observed source data, derived metrics and hypothetical scenario outputs.
- No exact delay, inventory or production-loss claims are made without data to support them.

## 10. Optional Kaggle dataset — only if the mentor insists on supervised ML

**UCI SECOM (Kaggle mirror):** https://www.kaggle.com/datasets/paresh2047/uci-semcom  
**Official UCI source:** https://archive.ics.uci.edu/dataset/179/secom

SECOM contains 1,567 semiconductor manufacturing observations, 591 sensor features and 104 failure labels. It is a compact, real semiconductor manufacturing dataset with missing values and a strongly imbalanced pass/fail target.

It can support a separate wafer/manufacturing defect-classification exercise, but it does **not** contain supplier relationships, country dependencies or disruption outcomes. Therefore, it is not part of AtmoGraph's core dataset and should not be mixed into the supply-chain graph as if it measured supplier disruptions.

If the mentor requires a supervised ML model specifically, discuss whether the project scope should change to semiconductor manufacturing defect prediction before adopting SECOM.

## 11. Datasets and approaches intentionally excluded

- **BACI + UN Comtrade + GDELT together:** too many sources and joins for the first month; not required for the focused prototype.
- **DataCo Smart Supply Chain:** generic e-commerce orders, not a semiconductor supplier network. It is not suitable as the core dataset for this project.
- **Large GNN / Transformer / real-time ingestion:** no validated labels or need in the first version.
- **Synthetic supplier-delay labels:** do not fabricate labels or present simulated outcomes as observed data.

## 12. Mentor-facing summary

“Our team will use the Emerging Technology Observatory Semiconductor Supply Chain Dataset (September 2026 release) as the single core source. We will focus the case study on silicon wafers used in chip manufacturing. The system will map the documented suppliers, provider countries, inputs and production-stage relationships; calculate supplier concentration and dependency indicators; group input-level concentration profiles using a small unsupervised clustering model; and simulate the potential ripple effect of a selected supplier or country disruption. The first version will use Python, Pandas, NetworkX, Scikit-learn and Streamlit. We will not claim exact delay forecasts because the selected source does not provide historical lead-time labels.”

---

**Scope rule:** A small, reproducible, source-backed risk-analysis system is better than an ambitious graph/AI stack built on data that cannot support its predictions.
