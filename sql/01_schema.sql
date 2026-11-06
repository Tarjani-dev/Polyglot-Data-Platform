-- sql/01_schema.sql
-- PolyglotAI metadata control-plane schema
-- Defines lookup tables, the Documents catalog, versioning,
-- orchestration control table, and execution/error logging.
-- Run in order: parent tables are created before dependent foreign keys.

-- ===========================================================
-- 1. Lookup Tables
-- ===========================================================

CREATE TABLE Languages (
    LanguageID   INT IDENTITY(1,1) PRIMARY KEY,
    LanguageCode NVARCHAR(10)  NOT NULL,
    LanguageName NVARCHAR(100) NOT NULL
);

CREATE TABLE DocumentTypes (
    DocumentTypeID INT IDENTITY(1,1) PRIMARY KEY,
    TypeName       NVARCHAR(50) NOT NULL
);

CREATE TABLE SourceSystems (
    SourceSystemID INT IDENTITY(1,1) PRIMARY KEY,
    SystemName     NVARCHAR(100) NOT NULL
);

-- ===========================================================
-- 2. Orchestration & Tracking Tables
-- ===========================================================

CREATE TABLE ControlTable (
    ControlID INT IDENTITY(1,1) PRIMARY KEY,
    TableName NVARCHAR(100) NOT NULL,
    LoadType  NVARCHAR(20)  NOT NULL,
    IsActive  BIT           NOT NULL DEFAULT 1
);

CREATE TABLE PipelineExecutionLog (
    ExecutionID      INT IDENTITY(1,1) PRIMARY KEY,
    PipelineName     NVARCHAR(100) NOT NULL,
    StartTime        DATETIME      NOT NULL,
    EndTime          DATETIME      NULL,
    Status           NVARCHAR(20)  NOT NULL,
    RecordsProcessed INT           NOT NULL DEFAULT 0
);

-- ===========================================================
-- 3. Document Catalog
-- ===========================================================

CREATE TABLE Documents (
    DocumentID     INT IDENTITY(1,1) PRIMARY KEY,
    DocumentName   NVARCHAR(255) NOT NULL,
    LanguageID     INT           NOT NULL,
    DocumentTypeID INT           NOT NULL,
    SourceSystemID INT           NOT NULL,
    FilePath       NVARCHAR(500) NOT NULL,
    UploadDate     DATETIME      NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_Documents_Languages
        FOREIGN KEY (LanguageID) REFERENCES Languages(LanguageID),

    CONSTRAINT FK_Documents_DocumentTypes
        FOREIGN KEY (DocumentTypeID) REFERENCES DocumentTypes(DocumentTypeID),

    CONSTRAINT FK_Documents_SourceSystems
        FOREIGN KEY (SourceSystemID) REFERENCES SourceSystems(SourceSystemID)
);

CREATE TABLE DocumentVersions (
    VersionID     INT IDENTITY(1,1) PRIMARY KEY,
    DocumentID    INT      NOT NULL,
    VersionNumber INT      NOT NULL,
    VersionDate   DATETIME NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_DocumentVersions_Documents
        FOREIGN KEY (DocumentID) REFERENCES Documents(DocumentID)
);

CREATE TABLE ValidationErrors (
    ErrorID      INT IDENTITY(1,1) PRIMARY KEY,
    DocumentID   INT           NOT NULL,
    ErrorMessage NVARCHAR(500) NOT NULL,
    ErrorDate    DATETIME      NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_ValidationErrors_Documents
        FOREIGN KEY (DocumentID) REFERENCES Documents(DocumentID)
);