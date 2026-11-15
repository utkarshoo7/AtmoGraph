# AtmoGraph — Technology Stack

This document records the technologies named in the AtmoGraph project brief and the role each is expected to play. It is a planning document, not evidence that every component has already been installed or integrated.

## 1. Backend and data layer

| Technology | Planned role | Expected responsibility |
|---|---|---|
| Neo4j | Graph database | Store supply-chain entities and their relationships; support graph traversal and risk-state updates |
| Cypher | Graph query language | Create, update, and query nodes and relationships in Neo4j |
| Python | Backend implementation language | Implement data ingestion, NLP processing, graph interaction, and model workflows |
| FastAPI | API layer (integration phase) | Expose backend functionality to the dashboard and serve prediction results |
| WebSocket | Live update channel (integration phase) | Push changing risk and prediction information to connected clients |

## 2. NLP and disruption ingestion

| Technology | Planned role | Expected responsibility |
|---|---|---|
| spaCy | NLP processing | Perform text processing and Named Entity Recognition (NER) |
| Hugging Face | NLP model ecosystem | Provide pretrained language models or pipelines where they are useful for extracting disruption information |

The ingestion pipeline should preserve the source text and source metadata. Extracted organization, location, and event mentions are candidates until they are resolved against entities in the graph.

## 3. Machine learning

| Technology | Planned role | Expected responsibility |
|---|---|---|
| PyTorch | Deep learning framework | Define, train, and evaluate neural network models |
| PyTorch Geometric | Graph Neural Network library | Represent graph data and implement GNN-based downstream impact or delay prediction |

The model's prediction target, graph features, and training labels must be defined before training. A GNN does not produce trustworthy delay estimates merely because a graph and a news article are available.

## 4. Frontend and visualization

| Technology | Planned role | Expected responsibility |
|---|---|---|
| React | Frontend framework | Build the interactive dashboard and application components |
| D3.js or React Flow | Graph visualization option | Render connected entities and relationships, with interaction such as zooming, panning, and selecting nodes |

The project brief lists D3.js or React Flow as alternatives. The team should select one based on graph size, interaction needs, and implementation complexity rather than attempting to use both without a reason.

## 5. Proposed data flow

1. A disruption article or text item enters the ingestion pipeline.
2. spaCy and/or a Hugging Face model extracts candidate entities and event details.
3. Entity resolution attempts to match those candidates to existing Neo4j nodes.
4. Neo4j stores the relevant event and risk-state changes.
5. PyTorch Geometric processes graph structure and features for downstream impact prediction.
6. FastAPI exposes graph and prediction data to the React application.
7. WebSocket can deliver updates to the dashboard when the live integration phase is implemented.
8. D3.js or React Flow visualizes the network and highlights predicted at-risk entities.

## 6. Development sequence

To reduce integration risk, build and verify the components in this order:

- Establish the Neo4j schema and load a small, clearly labelled mock graph.
- Verify graph queries and multi-hop traversal independently.
- Build a small NLP experiment using sample disruption text.
- Test entity matching before allowing NLP output to modify graph records.
- Define the prediction target and prepare labelled training/evaluation examples.
- Build and evaluate a baseline GNN before connecting predictions to the UI.
- Connect the backend API to the frontend.
- Add streaming updates only after request/response integration works.

## 7. Decisions still to be made

- D3.js or React Flow for the graph interface.
- Exact Neo4j node labels, relationship types, and property schema.
- News source or sample corpus for the first NLP prototype.
- Entity-resolution strategy for aliases and ambiguous names.
- GNN prediction target, features, labels, and evaluation metrics.
- Whether FastAPI and WebSocket are both required for the final deployment architecture.

## 8. Implementation status

At the time this document is written, these items describe the intended stack from the project brief and the proposed implementation sequence. Installation, configuration, integration, and testing should be recorded separately as they are completed.
