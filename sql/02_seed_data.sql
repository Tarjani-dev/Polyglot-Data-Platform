-- sql/02_seed_data.sql
-- Sample data for PolyglotAI control-plane tables.
-- Run after 01_schema.sql. Lookup tables are seeded first,
-- followed by the control table, document catalog, versions,
-- and a handful of representative validation errors.

-- ===========================================================
-- 1. Lookup Tables
-- ===========================================================

INSERT INTO Languages (LanguageCode, LanguageName) VALUES
    ('en', 'English'),
    ('hi', 'Hindi');

INSERT INTO DocumentTypes (TypeName) VALUES
    ('PDF'),
    ('DOCX'),
    ('TXT'),
    ('HTML'),
    ('CSV'),
    ('JSON');

INSERT INTO SourceSystems (SystemName) VALUES
    ('Local Upload'),
    ('SharePoint'),
    ('Intranet Portal');

-- ===========================================================
-- 2. Control Table
-- ===========================================================

INSERT INTO ControlTable (TableName, LoadType, IsActive) VALUES
    ('Documents', 'Full', 1);

-- ===========================================================
-- 3. Document Catalog
-- ===========================================================
-- Note: DocumentTypeID/SourceSystemID values below assume the
-- lookup inserts above ran first and generated IDs in that order
-- (1=PDF, 2=DOCX, 3=TXT, 4=HTML, 5=CSV, 6=JSON;
--  1=Local Upload, 2=SharePoint, 3=Intranet Portal).

INSERT INTO Documents (DocumentName, LanguageID, DocumentTypeID, SourceSystemID, FilePath) VALUES
    ('Employee_Handbook.pdf',  1, 1, 2, 'raw/pdf/Employee_Handbook.pdf'),
    ('HR_Policy.docx',         1, 2, 3, 'raw/docx/HR_Policy.docx'),
    ('Welcome_Message.txt',    2, 3, 1, 'raw/txt/Welcome_Message.txt'),
    ('Product_Catalog.html',   1, 4, 2, 'raw/html/Product_Catalog.html'),
    ('Sales_Report.csv',       1, 5, 1, 'raw/csv/Sales_Report.csv'),
    ('Customer_Data.json',     1, 6, 1, 'raw/json/Customer_Data.json'),
    ('Training_Manual.pdf',    2, 1, 2, 'raw/pdf/Training_Manual.pdf'),
    ('Financial_Report.csv',   1, 5, 1, 'raw/csv/Financial_Report.csv'),
    ('API_Response.json',      1, 6, 1, 'raw/json/API_Response.json'),
    ('User_Guide.docx',        1, 2, 3, 'raw/docx/User_Guide.docx');

-- ===========================================================
-- 4. Document Versions
-- ===========================================================

INSERT INTO DocumentVersions (DocumentID, VersionNumber) VALUES
    (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
    (6, 1), (7, 1), (8, 1), (9, 1), (10, 1),
    (1, 2), (2, 2), (1, 3);

-- ===========================================================
-- 5. Validation Errors (sample)
-- ===========================================================

INSERT INTO ValidationErrors (DocumentID, ErrorMessage) VALUES
    (6, 'Missing required field: CustomerEmail'),
    (9, 'Invalid JSON format'),
    (5, 'CSV contains inconsistent number of columns'),
    (4, 'Unsupported HTML encoding');