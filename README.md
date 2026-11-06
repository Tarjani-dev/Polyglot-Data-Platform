# Polyglot Data Platform (PolyglotAI)

> **Note:** This is a personal sandbox project. The Azure resources referenced (storage account, app registration) have been decommissioned and are no longer active.

## 1. Executive Summary & Architecture Overview

PolyglotAI is an enterprise-grade, metadata-driven data platform built on Azure. It is designed to ingest, process, and govern multi-format enterprise data streams — tabular structured and nested semi-structured data — using a scalable **Medallion Architecture** (Raw → Bronze → Silver → Gold), backed by open-source Delta Lake storage.

---

## 2. Core Tech Stack & Justification

| Component | Role | Why It Was Chosen |
|---|---|---|
| **Azure SQL Database** | Control Plane | Lightweight metadata repository — stores pipeline configurations, active source mappings, and incremental watermark values to keep orchestration decoupled from hardcoded logic. |
| **Azure Data Factory** | Orchestration Engine | Drives metadata-driven, loop-based orchestration (Lookup + ForEach + Copy Activity), eliminating hardcoded pipeline logic so the platform scales effortlessly as new sources are added. |
| **Azure Data Lake Storage Gen2** | Storage Layer | Provides secure, hierarchical namespace (HNS) storage, separating data into logical containers (raw, bronze, silver, gold). |
| **Azure Databricks & Apache Spark** | Processing Engine | Executes distributed compute, parses raw multi-format streams, enforces schema validation, and writes ACID-compliant Delta Lake tables. |
| **Azure Key Vault** | Security & Governance | Manages enterprise secrets via Databricks Secret Scopes using the OAuth client-credentials flow (`fs.azure.account.auth.type = OAuth`). |

---

## 3. Architecture & Data Flow Diagram
## 3. Architecture & Data Flow Diagram

```
┌────────────────────────┐
│   Source Systems       │  (CSV Employee Files & API JSON Responses)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Azure SQL Database      │  (Control Plane & Metadata Control Tables)
└───────────┬────────────┘
            │  (Metadata Lookup: Container & Directory Path Injection)
            ▼
┌────────────────────────┐
│ Azure Data Factory      │  (Orchestration Layer: Lookup → ForEach → Copy Activity)
└───────────┬────────────┘
            │  (Secure Transport via ABFSS protocol)
            ▼
┌────────────────────────┐
│ ADLS Gen2: RAW Zone     │  (Landing Zone: Immutable, Untouched Files)
└───────────┬────────────┘
            │  (Triggered Databricks Job & Key Vault OAuth Authentication)
            ▼
┌────────────────────────┐
│ Azure Databricks        │  (Compute Engine: Apache Spark & PySpark Notebooks)
├────────────────────────┤
│ • Bronze Layer          │  (Append-only Delta tables with file path metadata)
│ • Silver Layer          │  (Cleansed, typed, and structured Delta tables)
│ • Gold Layer            │  (Aggregated and unified analytics-ready Delta tables)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ GitHub Version Control  │  (Codebase, Databricks Notebooks, and SQL Scripts synced via Git)
└────────────────────────┘
```



---

## 4. End-to-End Data Flow & Ingestion Mechanics

1. **Metadata Lookup** — ADF queries the Azure SQL control table to fetch active datasets (e.g., `employees.csv`, `api_responses.json`) along with their target container and directory paths.
2. **Dynamic Ingestion** — A ForEach loop dynamically passes parameters (`TargetContainer`, `TargetDirectory`) to a generic ADF Copy Activity, landing untouched files securely into the ADLS Gen2 `raw` zone.
3. **Cluster Boot & Security Initialization** — Azure Data Factory triggers a Databricks job run. Databricks authenticates against ADLS Gen2 using OAuth credentials fetched dynamically from Azure Key Vault.
4. **Medallion Transformations:**
   - **Raw → Bronze:** Ingests raw files, adds system metadata (`_metadata.file_path`, `_ingestion_time`), and lands them into an append-only Bronze Delta table.
   - **Bronze → Silver:** Cleanses data, handles type casting, parses nested fields, and applies dynamic regex filtering.
   - **Silver → Gold:** Aggregates record counts from both Silver tables (employees and API responses) into a unified daily audit table, tracking ingestion volume by source and date.

---

## 5. Data Dictionary

Foundational metadata tables that drive the Azure Data Factory ingestion engine. All tables reside in the default `dbo` schema to prioritize architectural simplicity.

### Lookup Tables
Static reference data used to enforce normalization and prevent data-entry errors.

| Table Name | Description | Primary Key |
|---|---|---|
| `dbo.Languages` | Supported document languages (e.g., en, hi) | `LanguageID` |
| `dbo.DocumentTypes` | Allowed file formats (e.g., CSV, PDF, JSON) | `DocumentTypeID` |
| `dbo.SourceSystems` | Origin systems of the data (e.g., Local Upload) | `SourceSystemID` |

### Orchestration & Tracking Tables
Tables that actively control the pipeline and log its activity.

| Table Name | Description | Primary Key |
|---|---|---|
| `dbo.ControlTable` | Read by ADF Lookup to dynamically generate ingestion pipelines | `ControlID` |
| `dbo.Documents` | Core metadata catalog tracking every ingested file | `DocumentID` |
| `dbo.PipelineExecutionLog` | Tracks ADF pipeline execution status (Success/Fail) | `LogID` |
| `dbo.ValidationErrors` | Captures schema mismatches or corrupt file logs | `ErrorID` |

> **Architecture Note:** Storing configuration in `dbo.ControlTable` prevents hardcoding file paths in Azure Data Factory.

> **Note:** PDF, DOCX, and HTML ingestion are catalogued in the metadata schema but not yet processed by the Databricks pipeline — current notebooks handle CSV and JSON sources only.

---

## 6. Design Q&A

**Q1: Why a metadata-driven architecture instead of hardcoding pipelines in Azure Data Factory?**
Hardcoding pipelines creates a maintenance bottleneck — with hundreds of sources, hundreds of individual copy activities quickly becomes technical debt. Using Azure SQL as a control table, combined with ADF Lookup and ForEach activities, makes the orchestration layer dynamic. Onboarding a new source is just a new row in the SQL control table — the pipeline scales without touching the ADF canvas.

**Q2: How is security and credential management handled between Databricks and ADLS Gen2?**
Storage keys and service principal secrets are never hardcoded in notebooks. Azure Key Vault, backed by Databricks Secret Scopes, is used instead — Databricks authenticates to ADLS Gen2 via OAuth 2.0 Client Credentials (`ClientCredsTokenProvider`), passing scoped client IDs and secrets securely at runtime.

**Q3: Why Delta Lake over standard Parquet in the Silver and Gold layers?**
Parquet is great for immutable, columnar storage, but lacks transactional guarantees. Delta Lake sits on top of Parquet and adds ACID transactions, time travel (data versioning), schema enforcement, and optimized file compaction (`OPTIMIZE`/`VACUUM`) — essential for production data quality and audit compliance.