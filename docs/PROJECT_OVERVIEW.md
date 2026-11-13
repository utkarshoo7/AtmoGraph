# AtmoGraph — Project Overview and Initial Technical Plan

## 1. Project objective

AtmoGraph is a Supply Chain Ripple Effect Predictor. It is intended to identify how a localized disruption can propagate through connected suppliers, manufacturers, shipping routes, and other supply-chain entities.

The project brief highlights a limitation of traditional isolated time-series approaches: they do not adequately represent complex relationships across a global supply-chain network.

## 2. Intended end-to-end workflow

1. **News ingestion:** collect a disruption-related news item or text input.
2. **NLP extraction:** use spaCy and/or Hugging Face NLP components to identify relevant entities and disruption information.
3. **Entity resolution:** match extracted names and locations to entities already represented in the supply-chain graph.
4. **Graph update:** store or update the disruption and risk-related attributes in Neo4j.
5. **Graph analysis and prediction:** use a Graph Neural Network (GNN), implemented with PyTorch Geometric, to estimate downstream effects such as delay risk.
6. **API and visualization:** expose graph/prediction data through an API and display the network and at-risk entities in a React interface.

This is the intended architecture from the project brief. The implementation will be developed and validated incrementally.

## 3. Initial graph design

The following are proposed starting entity types. They should be refined as the dataset and implementation are selected.

### Candidate node types

- Supplier
- Manufacturer
- Port
- ShippingRoute
- LogisticsProvider
- Retailer

### Candidate relationships

- `SUPPLIES_TO`: a supplier provides material or components to another entity.
- `SHIPS_THROUGH`: a shipment or route uses a port.
- `TRANSPORTED_BY`: goods are transported by a logistics provider.
- `DISTRIBUTES_TO`: a manufacturer or distributor supplies a retailer.

Relationships should represent documented or explicitly simulated dependencies. Unknown relationships must not be presented as real-world facts.

## 4. Initial disruption record

A disruption record should capture, where available:

- Source article or source identifier
- Article publication time
- Event type (for example, port strike or port closure)
- Mentioned location and affected entity
- Event start time and expected duration, if reported
- Extraction confidence
- Entity-resolution status

Missing values should remain unknown rather than being invented. News mentions should be traceable to their source.

## 5. Prediction considerations

The GNN requires a graph with meaningful node/edge features and a defined prediction target. For delay prediction, the project will need historical or clearly labelled simulated examples containing disruption features and observed/assigned delay targets.

The initial prototype should distinguish:
- **Observed information:** facts extracted from source data.
- **Graph-derived information:** entities connected to the disrupted entity.
- **Model predictions:** estimated risk or delay, with the model/version and prediction horizon recorded.

Predictions must not be described as verified outcomes. Model performance should be evaluated against held-out labelled examples before claims about accuracy are made.

## 6. Planned implementation milestones

The project brief specifies these four weekly phases:

- **Week 1 — Graph foundations:** set up Neo4j, design a mock global supply-chain graph, write Cypher ingestion scripts; scaffold the React dashboard and render a static graph.
- **Week 2 — NLP pipeline:** ingest text, perform Named Entity Recognition (NER), and update risk states in Neo4j; connect the frontend to graph data and add zoom, pan, and node-click details.
- **Week 3 — GNN engineering:** develop a GNN for downstream delay prediction using upstream disruption features; add a visual overlay for at-risk nodes.
- **Week 4 — Integration:** connect predictions to a FastAPI/WebSocket stream; add 30/60/90-day timeline controls and refine the interface.

## 7. Initial validation checklist

- [ ] Neo4j starts locally and accepts a connection.
- [ ] A small, documented mock supply-chain graph can be created with Cypher.
- [ ] A graph query can retrieve multi-hop neighbours of a selected entity.
- [ ] NLP can extract candidate entities from a sample disruption article.
- [ ] Extracted entities can be matched to graph entities, with unmatched cases reported.
- [ ] Risk updates can be written to and read from Neo4j.
- [ ] The React interface can render the sample graph and show node details.
- [ ] A prediction dataset and target are documented before GNN training begins.

## 8. Open decisions to resolve during implementation

- Which public or internally prepared dataset will provide supply-chain entities and relationships?
- Which news source or sample corpus will be used for the NLP prototype?
- How will entity aliases and ambiguous locations be resolved?
- What exact target will the GNN predict (for example, delay duration or risk class)?
- What historical or simulated labels are available to train and evaluate the model?

These decisions must be supported by available data and documented assumptions before predictive results are treated as meaningful.
