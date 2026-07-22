# PolyglotAI - Data Dictionary

This document outlines the foundational metadata tables used to drive the Azure Data Factory ingestion engine. All tables reside in the default `dbo` schema to prioritize architectural simplicity.

## 1. Lookup Tables
These tables hold static reference data to enforce normalization and prevent data entry errors.

| Table Name | Description | Primary Key |
|---|---|---|
| `dbo.Languages` | Supported document languages (e.g., en, hi). | `LanguageID` |
| `dbo.DocumentTypes` | Allowed file formats (e.g., CSV, PDF, JSON). | `DocumentTypeID` |
| `dbo.SourceSystems` | Origin systems of the data (e.g., Local Upload). | `SourceSystemID` |

## 2. Orchestration & Tracking Tables
These tables actively control the pipeline and log its activity.

| Table Name | Description | Primary Key |
|---|---|---|
| `dbo.ControlTable` | Read by ADF Lookup to dynamically generate ingestion pipelines. | `ControlID` |
| `dbo.Documents` | The core metadata catalog tracking every ingested file. | `DocumentID` |
| `dbo.PipelineExecutionLog` | Tracks ADF pipeline execution status (Success/Fail). | `LogID` |
| `dbo.ValidationErrors` | Captures schema mismatches or corrupt file logs. | `ErrorID` |

*Architecture Note: Storing configuration in `dbo.ControlTable` prevents hardcoding file paths in Azure Data Factory.*