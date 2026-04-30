# Day 6 Session 1: AI Capabilities in SQL (3.1 + 3.2 + 3.3 review)

**Date**: 2026-05-01
**Domain**: 3 — Implement AI Capabilities in Database Solutions (25–30%)
**Subtopics**: CREATE EXTERNAL MODEL, AI_GENERATE_EMBEDDINGS, AI_GENERATE_CHUNKS, embedding maintenance (CDC/Change Tracking/triggers), VECTOR data type, DiskANN vector indexes, VECTOR_DISTANCE, VECTOR_SEARCH, VECTOR_NORMALIZE, VECTORPROPERTY, ANN vs ENN, full-text search, hybrid search, RRF, sp_invoke_external_rest_endpoint, FOR JSON PATH, JSON_VALUE

---

## 1. CREATE EXTERNAL MODEL — Registering AI Models in SQL

### What Is It?

`CREATE EXTERNAL MODEL` is a new T-SQL DDL statement (SQL Server 2025, Azure SQL DB, Azure SQL MI, Fabric SQL) that registers an AI model inference endpoint inside the database as a named object. It does **not** host the model — it just stores the connection details so T-SQL functions like `AI_GENERATE_EMBEDDINGS` can call it by name.

**Applies to**: SQL Server 2025 (17.x) | Azure SQL Database | Azure SQL Managed Instance (Always-up-to-date) | SQL database in Microsoft Fabric

### Full Syntax

```sql
CREATE EXTERNAL MODEL external_model_name
[ AUTHORIZATION owner_name ]
WITH (
    LOCATION     = '<protocol>://<path>[:<port>]',
    API_FORMAT   = { 'Azure OpenAI' | 'OpenAI' | 'Ollama' | 'ONNX Runtime' },
    MODEL_TYPE   = EMBEDDINGS,
    MODEL        = 'model-deployment-name',
    [ CREDENTIAL = <database_scoped_credential_name>, ]
    [ PARAMETERS = '{"valid":"JSON"}', ]
    [ LOCAL_RUNTIME_PATH = 'path_to_onnx_runtime_files' ]
);
```

**Critical details**:
- `MODEL_TYPE` currently only supports `EMBEDDINGS` — no chat completion model type yet in this statement
- `LOCATION` must use **HTTPS** with TLS — HTTP not supported
- `CREDENTIAL` references a `DATABASE SCOPED CREDENTIAL`; the credential name must match the URL prefix (protocol + FQDN)
- `PARAMETERS` is a JSON string for endpoint-level defaults (e.g., `'{"dimensions": 1536}'`)
- `LOCAL_RUNTIME_PATH` is only used for `ONNX Runtime` format (local ONNX models)

### API_FORMAT Values and Their URL Patterns

| API_FORMAT | URL Pattern |
|-----------|-------------|
| `Azure OpenAI` | `https://{endpoint}/openai/deployments/{deployment-id}/embeddings?api-version={date}` |
| `OpenAI` | `https://api.openai.com/v1/embeddings` |
| `Ollama` | `https://localhost:{port}/api/embed` |
| `ONNX Runtime` | Local file path to model directory |

### Credential Types

| Auth Method | IDENTITY | SECRET |
|------------|---------|--------|
| API Key (Azure OpenAI) | `'HTTPEndpointHeaders'` | `'{"api-key":"YOUR_KEY"}'` |
| API Key (OpenAI) | `'HTTPEndpointHeaders'` | `'{"Bearer":"YOUR_KEY"}'` |
| Managed Identity | `'Managed Identity'` | `'{"resourceid":"https://cognitiveservices.azure.com"}'` |

**Managed Identity on SQL Server 2025**: must connect SQL Server to Azure Arc first and enable the option:

```sql
EXECUTE sp_configure 'allow server scoped db credentials', 1;
RECONFIGURE WITH OVERRIDE;
```

### Permissions

| Action | Permission Required |
|--------|-------------------|
| Create/alter external model | `ALTER ANY EXTERNAL MODEL` or `CREATE EXTERNAL MODEL` |
| Use an external model in a function | `EXECUTE ON EXTERNAL MODEL::<ModelName>` |

```sql
-- Grant a user the ability to use a specific model
GRANT EXECUTE ON EXTERNAL MODEL::MyAzureOpenAIModel TO [AIApplicationUser];
```

### Catalog View

```sql
-- View all external model registrations
SELECT * FROM sys.external_models;
```

### Full Example — Azure OpenAI with API Key

```sql
-- Step 1: Create credential
CREATE DATABASE SCOPED CREDENTIAL [https://myopenai.cognitiveservices.azure.com/]
    WITH IDENTITY = 'HTTPEndpointHeaders',
         SECRET = '{"api-key":"YOUR_KEY"}';
GO

-- Step 2: Register the model
CREATE EXTERNAL MODEL MyEmbeddingModel
WITH (
    LOCATION   = 'https://myopenai.cognitiveservices.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-01',
    API_FORMAT = 'Azure OpenAI',
    MODEL_TYPE = EMBEDDINGS,
    MODEL      = 'text-embedding-ada-002',
    CREDENTIAL = [https://myopenai.cognitiveservices.azure.com/]
);
GO

-- Step 3: Grant usage
GRANT EXECUTE ON EXTERNAL MODEL::MyEmbeddingModel TO [AppUser];
```

### Local ONNX Runtime Example (No Outbound Connectivity)

```sql
-- Enables external AI runtimes
EXECUTE sp_configure 'external AI runtimes enabled', 1;
RECONFIGURE WITH OVERRIDE;

CREATE EXTERNAL MODEL myLocalOnnxModel
WITH (
    LOCATION          = 'C:\onnx_runtime\model\all-MiniLM-L6-v2-onnx',
    API_FORMAT        = 'ONNX Runtime',
    MODEL_TYPE        = EMBEDDINGS,
    MODEL             = 'allMiniLM',
    PARAMETERS        = '{"valid":"JSON"}',
    LOCAL_RUNTIME_PATH = 'C:\onnx_runtime\'
);
```

**Use case for ONNX Runtime**: SQL Server with no outbound internet connectivity. Must install SQL Server Machine Learning Services.

---

## 2. AI_GENERATE_EMBEDDINGS — Generating Embeddings in T-SQL

### Syntax

```sql
AI_GENERATE_EMBEDDINGS ( source USE MODEL model_identifier
    [ PARAMETERS optional_json_parameters ] )
```

- `source`: any character expression (nvarchar, varchar, etc.)
- `model_identifier`: name of a registered `EXTERNAL MODEL` of type EMBEDDINGS
- Returns a `VECTOR` value (array of floats as JSON internally)

### Prerequisite

```sql
-- Must be enabled on the server
EXECUTE sp_configure 'external rest endpoint enabled', 1;
RECONFIGURE WITH OVERRIDE;
```

### Examples

```sql
-- Inline embedding for a query
DECLARE @qv VECTOR(1536) = AI_GENERATE_EMBEDDINGS(N'machine learning' USE MODEL MyEmbeddingModel);

-- Batch generate and store embeddings
UPDATE t
SET embedding = AI_GENERATE_EMBEDDINGS(t.description USE MODEL MyEmbeddingModel)
FROM dbo.Products AS t;

-- With chunking (AI_GENERATE_CHUNKS)
INSERT INTO dbo.text_embeddings (chunk, vector_col)
SELECT c.chunk_text,
       AI_GENERATE_EMBEDDINGS(c.chunk_text USE MODEL MyEmbeddingModel)
FROM dbo.RawDocs AS d
CROSS APPLY AI_GENERATE_CHUNKS(
    SOURCE     = d.body,
    CHUNK_TYPE = FIXED,
    CHUNK_SIZE = 100
) AS c;

-- Override dimensions at runtime
DECLARE @params JSON = N'{"dimensions": 768}';
SELECT AI_GENERATE_EMBEDDINGS(title USE MODEL MyEmbeddingModel PARAMETERS @params)
FROM dbo.Articles;
```

---

## 3. Embedding Maintenance — Keeping Embeddings Fresh

### The Problem

Embeddings are snapshots — they go stale when the source text changes. You need a strategy to regenerate them when rows are modified.

### Method Comparison

| Method | Trigger Event | Use Case | Key Detail |
|--------|--------------|----------|-----------|
| **DML Trigger** | Every INSERT/UPDATE on the table | Real-time, low-volume, simple | Runs inline — avoid heavy AI calls here; better for flagging |
| **Change Tracking** | Polling for changes since last sync | Azure Functions SQL trigger binding | Lightweight — only tracks which rows changed (not what changed) |
| **CDC (Change Data Capture)** | Captures full old + new row data | Audit trail; AI Functions offloaded | Heavier — full before/after snapshots stored in CT tables |
| **Azure Functions SQL trigger binding** | Automatically uses Change Tracking | Serverless embedding updates | Must enable Change Tracking (NOT CDC) |
| **CES (Change Event Stream)** | Real-time event stream to Fabric | Fabric SQL → streaming pipelines | Only for Fabric SQL |

### Column Selection for Embeddings (Exam Favorite!)

Only capture the **columns that contribute to the semantic content** of the embedding — not metadata columns:

- **Good columns to embed**: `title`, `description`, `body`, `notes`, `summary` — free-text narrative
- **Bad columns for embeddings**: `id`, `price`, `date`, `status`, `embedding` (don't embed the embedding!)
- **Rule**: If changing the column doesn't change the *meaning* of the document, don't include it

**Exam example (q047)**: For a CDC capture on `dbo.Articles`, capture `ArticleId, Title, Body` — **not** `LastModifiedUtc` or `EmbeddingVector`

### CDC Setup for Embedding Maintenance

```sql
-- Step 1: Enable CDC on the database
EXEC sys.sp_cdc_enable_db;

-- Step 2: Enable CDC on the table with specific columns and net changes support
EXEC sys.sp_cdc_enable_table
    @source_schema     = N'dbo',
    @source_name       = N'Articles',
    @role_name         = NULL,
    @captured_column_list = N'ArticleId, Title, Body',  -- only columns needed for embeddings
    @supports_net_changes = 1;                           -- enables net change queries
```

- `supports_net_changes = 1` → can query `cdc.fn_cdc_get_net_changes_*` — returns only the latest state per row (ideal for embedding regeneration — avoids re-processing intermediate states)
- `supports_net_changes = 0` → only `fn_cdc_get_all_changes_*` available

### Change Tracking Setup (for Azure Functions SQL binding)

```sql
-- Enable at database level
ALTER DATABASE MyDB SET CHANGE_TRACKING = ON (CHANGE_RETENTION = 2 DAYS, AUTO_CLEANUP = ON);

-- Enable on specific table
ALTER TABLE dbo.Articles ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
```

### When to Use What (Exam Decision Tree)

| Scenario | Answer |
|----------|--------|
| Azure Functions SQL trigger binding | **Change Tracking** (not CDC!) |
| Need old + new column values captured | **CDC** |
| Minimize DB CPU for AI embedding calls | **CDC** + external Azure Functions |
| Embedding updated immediately on every row change | **DML trigger** |
| No-code / low-throughput integration | **Logic Apps** |

### Chunk Design Principles

- **Fixed-size chunking**: consistent token windows, good for dense text
- **Semantic chunking**: preserves meaning boundaries (paragraphs, sentences)
- **Why it matters for embeddings**: chunk size affects token count → cost and retrieval precision
- **Exam tip (q052)**: Chunking reduces tokens per retrieval AND improves RAG performance — it's the answer when the question mentions "reduce tokens per retrieval"

### Model Switching — Critical Trap!

When switching embedding models (e.g., `text-embedding-ada-002` → `text-embedding-3-small`):
- **The new model produces vectors in a DIFFERENT vector space** — old and new vectors are NOT comparable
- **You MUST regenerate ALL existing embeddings** with the new model before switching queries
- **You MUST update the EXTERNAL MODEL LOCATION** — the deployment endpoint changes too
- **Failure to regenerate = runtime errors or meaningless search results** in `VECTOR_SEARCH`

**Exam example (q049)**: What to do FIRST when switching models? → **Regenerate embeddings for existing rows (C)**
**Exam example (q050)**: Two actions needed when switching? → **Change the endpoint (B) + Regenerate all embeddings (C)**

### Column Selection for Embeddings — Semantic vs. Numeric/Categorical

| Column Type | Embed? | Why |
|-------------|--------|-----|
| Free-text description / notes / body | ✅ Yes | Rich semantic meaning |
| ID, price, date, score (numeric) | ❌ No | No semantic similarity |
| Categorical (status, type, flag) | ❌ No | Use as filter predicates instead |
| The embedding vector column itself | ❌ Never | Self-referential nonsense |

**Exam example (q084)**: Which column to embed for "similar vehicle incidents"? → `incidentDescription` (free text), NOT `vehicleLocation` (geo), `incidentType` (categorical), or `SeverityScore` (numeric)

---

## 4. VECTOR Data Type

### What Is It?

A native SQL data type for storing arrays of floating-point numbers. Used for embedding vectors.

```sql
-- Syntax
column_name VECTOR ( dimensions ) [ NOT NULL | NULL ]
column_name VECTOR ( dimensions , float16 )  -- half-precision (preview, requires PREVIEW_FEATURES = ON)
```

- Maximum dimensions: **1998**
- Default base type: `float32` (4 bytes per element)
- `float16` is available in SQL Server 2025 preview only
- Stored in **optimized binary format** but exposed as **JSON arrays** (`[0.1, -0.2, 30.0]`)

### Creating and Casting Vectors

```sql
-- Implicit cast from JSON string
DECLARE @v VECTOR(3) = '[1.0, -0.2, 30]';

-- Explicit cast
SELECT CAST('[1.0, -0.2, 30]' AS VECTOR(3));
SELECT CAST(JSON_ARRAY(1.0, -0.2, 30) AS VECTOR(3));

-- Convert back to JSON/string
DECLARE @v VECTOR(3) = '[1.0, -0.2, 30]';
SELECT CAST(@v AS NVARCHAR(MAX));  -- Returns JSON array string
SELECT CAST(@v AS JSON);
```

### Key Limitations (Exam Favorite!)

| Limitation | Detail |
|------------|--------|
| No B-tree or columnstore indexes | Use `CREATE VECTOR INDEX` instead |
| No comparison operators | Can't do `WHERE v1 = v2` — use `VECTOR_DISTANCE` |
| No DEFAULT or CHECK constraints | Only NULL/NOT NULL constraints allowed |
| No PRIMARY KEY / FOREIGN KEY on vector col | Keys require equality comparison, not applicable |
| Can't be used in memory-optimized tables | In-memory OLTP not supported |
| Can't be used in Always Encrypted | Not supported |
| Can't use TRUNCATE on vector-indexed tables | Drop index first, truncate, re-insert ≥100 rows, recreate |
| Vector indexes require ≥100 rows | Error Msg 42266 if fewer rows exist |

---

## 5. Vector Functions

### VECTOR_DISTANCE — Exact (ENN) Search

```sql
VECTOR_DISTANCE ( distance_metric , vector1 , vector2 )
```

- Returns a **scalar float** — the distance between two vectors
- **Always exact** — never uses vector index even if one exists
- Use for: exact kNN when dataset is small (< ~50,000 vectors)

```sql
-- Find top 10 most similar articles (exact kNN)
DECLARE @qv VECTOR(1536) = AI_GENERATE_EMBEDDINGS(N'Pink Floyd music style' USE MODEL MyModel);
SELECT TOP (10) id, title,
       VECTOR_DISTANCE('cosine', @qv, content_vector) AS distance
FROM dbo.wikipedia_articles
ORDER BY distance;
```

### Distance Metrics

| Metric | Range | Meaning | When to Use |
|--------|-------|---------|-------------|
| `cosine` | [0, 2] | Angular distance; 0 = identical direction | Text embeddings (most common) |
| `euclidean` | [0, ∞] | Straight-line distance; 0 = identical | Image embeddings, spatial data |
| `dot` | (−∞, +∞) | Negative dot product; smaller = more similar | When vectors are already normalized |

**Key rule**: Lower distance = more similar for ALL three metrics.

**Cosine advantage**: Measures **direction** (angle) not magnitude — makes it robust when chunk sizes vary (different text lengths produce vectors of different magnitudes, but cosine ignores that).

**Exam trap (q087)**: When comparing vectors from documents with different chunk sizes → use `cosine` distance because it's insensitive to magnitude differences.

### VECTOR_NORMALIZE

```sql
VECTOR_NORMALIZE ( vector , norm_type )
-- norm_type: 'norm2' (L2 / Euclidean norm), 'norm1' (L1 / Manhattan norm)
```

- Returns a vector scaled to have a **length of 1** under the specified norm
- Useful before using dot product (normalized dot product = cosine similarity)
- **Exam trap**: `VECTOR_NORMALIZE` alone doesn't fix slow queries — you still need a `VECTOR_INDEX` with `VECTOR_SEARCH` to get ANN performance

### VECTOR_NORM

```sql
VECTOR_NORM ( vector , norm_type )
-- Returns the scalar magnitude (length) of the vector
```

### VECTORPROPERTY

```sql
VECTORPROPERTY ( vector , 'property_name' )
-- Returns metadata properties of a vector (e.g., dimensionality)
```

---

## 6. CREATE VECTOR INDEX — Approximate (ANN) Search

### What Is DiskANN?

- DiskANN (Disk Approximate Nearest Neighbor) is a **graph-based** index algorithm from Microsoft Research
- Builds a navigable graph over all vectors, allowing fast traversal to find approximate nearest neighbors
- Efficiently uses **SSD + minimal RAM** → handles billions of vectors on a single node
- Key trade-off: **speed vs. recall** — ANN returns approximate results faster than exact kNN

### Syntax

```sql
CREATE VECTOR INDEX index_name
ON table_name ( vector_column )
WITH (
    METRIC = { 'cosine' | 'dot' | 'euclidean' },
    [ TYPE  = 'DiskANN', ]                         -- only DiskANN supported
    [ MAXDOP = max_degree_of_parallelism ]
);
```

**Permissions**: `ALTER` on the table.

```sql
-- Example
CREATE VECTOR INDEX vec_idx
ON dbo.Articles (embedding)
WITH (METRIC = 'cosine', TYPE = 'DiskANN');
```

### Requirements

| Requirement | Detail |
|------------|--------|
| Minimum rows | ≥ 100 rows with non-NULL vectors before creation |
| Table type | Base tables only — no views, temp tables |
| Clustered primary key | Must exist on the table |
| Metric must match query metric | Index on 'cosine' won't accelerate a 'euclidean' query |
| ≥ 100 rows to CREATE | Fewer rows → Msg 42266 error |

### VECTOR_SEARCH — ANN Query (Latest Syntax)

```sql
-- Latest version (vector index v3+) — use SELECT TOP WITH APPROXIMATE
DECLARE @qv VECTOR(1536) = AI_GENERATE_EMBEDDINGS(N'search term' USE MODEL MyModel);

SELECT TOP (10) WITH APPROXIMATE
    t.id,
    t.title,
    r.distance
FROM VECTOR_SEARCH(
    TABLE     = dbo.Articles AS t,
    COLUMN    = embedding,
    SIMILAR_TO = @qv,
    METRIC    = 'cosine'
) AS r
ORDER BY r.distance;
```

### Legacy Syntax (Deprecated — Earlier Vector Index Versions)

```sql
-- OLD: TOP_N parameter in VECTOR_SEARCH — deprecated, raises Msg 42274 with v3 indexes
SELECT TOP (10) t.id, t.title, r.distance
FROM VECTOR_SEARCH(
    TABLE     = dbo.Articles AS t,
    COLUMN    = embedding,
    SIMILAR_TO = @qv,
    METRIC    = 'cosine',
    TOP_N     = 10  -- DEPRECATED: Error Msg 42274 with latest indexes
) AS r
ORDER BY r.distance;
```

### VECTOR_SEARCH Rules (Exam Critical!)

| Rule | Detail |
|------|--------|
| `ORDER BY` required | `SELECT TOP WITH APPROXIMATE` fails without ORDER BY |
| ORDER BY must be on `distance` only | Can't ORDER BY multiple columns directly — use subquery |
| `distance` column is ASC only | DESC order not supported |
| `VECTOR_SEARCH` can't be in view body | General limitation |
| `WITH APPROXIMATE` requires `VECTOR_SEARCH` | Can't use `WITH APPROXIMATE` with `VECTOR_DISTANCE` |
| Result column named `distance` | Always present in VECTOR_SEARCH output |
| TRUNCATE not allowed on vector-indexed tables | Drop index → truncate → repopulate ≥100 rows → recreate |

### ANN vs ENN — Decision Guide

| Scenario | Use |
|----------|-----|
| Dataset < ~50,000 vectors | `VECTOR_DISTANCE` (exact kNN) — no index needed |
| Dataset > 50,000 vectors, latency sensitive | `CREATE VECTOR INDEX` + `VECTOR_SEARCH` (ANN) |
| Accuracy paramount, speed secondary | `VECTOR_DISTANCE` (exact) |
| AI/RAG production workloads | ANN — small recall trade-off, massive speed gain |

**Recall**: Proportion of true nearest neighbors that ANN correctly identifies. Perfect recall = 1 (equivalent to exact kNN). In practice, high recall (≈ 0.95+) is acceptable for text embeddings because the embeddings themselves are already approximate representations.

### DML Support in Latest Vector Index (v3+)

- Latest version: INSERT, UPDATE, DELETE, MERGE fully supported while index is maintained automatically
- Earlier version: tables were **read-only** after index creation (use `ALLOW_STALE_VECTOR_INDEX` database scoped config to allow DML on older indexes)
- Latest version supports **iterative filtering**: WHERE predicates applied DURING search (not post-filter)

### sys.vector_indexes Catalog View

```sql
-- Check vector index version
SELECT i.name AS index_name,
       t.name AS table_name,
       JSON_VALUE(v.build_parameters, '$.Version') AS index_version
FROM sys.vector_indexes AS v
INNER JOIN sys.indexes AS i ON v.object_id = i.object_id AND v.index_id = i.index_id
INNER JOIN sys.tables AS t ON v.object_id = t.object_id;
-- Version >= 3 = latest; Version < 3 = needs migration
```

---

## 7. Full-Text Search — Quick Refresh (3.2)

### Functions

| Function | Returns | Use Case |
|----------|---------|---------|
| `CONTAINS(col, 'word')` | Rows matching term | Exact/prefix/thesaurus searches |
| `FREETEXT(col, 'phrase')` | Rows semantically matching phrase | Natural language queries |
| `CONTAINSTABLE(table, col, 'term')` | Ranked result set (with KEY, RANK) | Join with ranking score |
| `FREETEXTTABLE(table, col, 'phrase')` | Ranked result set | Natural language + ranking |

```sql
-- CONTAINSTABLE returns a table with KEY and RANK (0–1000)
SELECT p.ProductName, ft.RANK
FROM dbo.Products AS p
INNER JOIN CONTAINSTABLE(dbo.Products, Description, '"machine learning"') AS ft
    ON p.ProductID = ft.[KEY]
ORDER BY ft.RANK DESC;
```

### FORMSOF

```sql
-- FORMSOF(INFLECTIONAL, 'run') matches: run, runs, running, ran
-- FORMSOF(THESAURUS, 'car') matches: car, vehicle, automobile (from thesaurus file)
SELECT * FROM dbo.Articles
WHERE CONTAINS(body, 'FORMSOF(INFLECTIONAL, "run")');
```

---

## 8. Hybrid Search — Combining Vector + Full-Text

### What Is Hybrid Search?

Combines semantic (vector) search with keyword (full-text) search to get the best of both:
- **Vector search**: finds semantically similar results (context-aware)
- **Full-text search**: finds exact keyword matches (precision)
- **Re-ranking**: scores are fused together

### SQL-Level Hybrid Search Pattern

```sql
CREATE PROCEDURE dbo.HybridSearch
    @query NVARCHAR(MAX),
    @topN INT = 20
AS
BEGIN
    -- Step 1: Generate query vector
    DECLARE @qv VECTOR(1536) = AI_GENERATE_EMBEDDINGS(@query USE MODEL MyEmbeddingModel);

    -- Step 2: ANN retrieval (approximate, fast)
    -- Step 3: Full-text re-ranking (CONTAINSTABLE)
    SELECT TOP (@topN)
        vs.id,
        vs.title,
        vs.distance AS vector_distance,
        ft.RANK AS fts_rank
    FROM VECTOR_SEARCH(
        TABLE     = dbo.Products AS vs,
        COLUMN    = embedding,
        SIMILAR_TO = @qv,
        METRIC    = 'cosine'
    ) AS r
    INNER JOIN dbo.Products vs ON vs.id = r.id
    INNER JOIN CONTAINSTABLE(dbo.Products, description, @query) AS ft
        ON vs.id = ft.[KEY]
    ORDER BY r.distance;
END;
```

**Exam example (q054)**: The three components for hybrid search stored procedure:
1. `AI_GENERATE_EMBEDDINGS` → generate query vector
2. `VECTOR_SEARCH` → ANN retrieval of top 20 candidates
3. `CONTAINSTABLE` → full-text re-ranking of candidates

### Weighted Hybrid Ranking Formula (q085)

When manually fusing scores:
- `VECTOR_DISTANCE` returns distance [0, 2] where **lower = more similar**
- `CONTAINSTABLE RANK` returns [0, 1000] where **higher = more relevant**
- To combine: normalize RANK → invert it → weight it

```sql
ORDER BY (vector_distance * 0.6) + ((1.0 - RANK/1000.0) * 0.4) ASC
--         60% vector weight          40% FTS weight (inverted, normalized)
```

**Why invert RANK**: RANK is higher-is-better; distance is lower-is-better. Inversion makes them consistent.

### Azure AI Search — Hybrid Search (Semantic Ranking)

For Azure AI Search (separate from SQL):
- `queryType = "semantic"` enables semantic ranking over results
- `semanticConfiguration` = the name of your semantic configuration (typically the **index name**)
- `captions = "extractive"` → extracts highlighted snippets from matching documents
- `answers = "extractive"` → extracts answer-like content from top results
- `k` in vector queries = number of vector candidates to retrieve (higher k = more candidates for reranking)

**Exam example (q053)**: Hybrid search with captions:
- `queryType` → `semantic` (not "hybrid" — it's semantic ranking, not a queryType called hybrid)
- `semanticConfiguration` → `hotels` (the index name)
- `captions` → `extractive`

**Exam example (q056)**: Fewer results + missing captions:
- `k = 50` (retrieve more vector candidates)
- `queryType = semantic`
- `captions = extractive`
- `answers = extractive`

### Reciprocal Rank Fusion (RRF)

Azure AI Search uses **RRF** to automatically fuse keyword and vector rankings:
- Score = `sum(1 / (rank_in_keyword_results + 60))` + `sum(1 / (rank_in_vector_results + 60))`
- 60 is the RRF constant (dampens extreme rank differences)
- Higher RRF score = higher final position
- RRF is the default fusion in Azure AI Search hybrid queries (you don't need to calculate it — the service does it)

---

## 9. sp_invoke_external_rest_endpoint — SQL-to-LLM (RAG Pattern, 3.3)

### RAG in SQL — Core Pattern

```sql
-- 1. Retrieve relevant context from SQL (vector/FTS search)
-- 2. Format as JSON payload
-- 3. Call LLM via sp_invoke_external_rest_endpoint
-- 4. Extract response with JSON_VALUE

DECLARE @contextJson NVARCHAR(MAX);
SELECT @contextJson = (
    SELECT TOP (5) question, answer
    FROM dbo.KnowledgeBase
    ORDER BY VECTOR_DISTANCE('cosine', @qv, embedding)
    FOR JSON PATH
);

-- Build payload
DECLARE @payload NVARCHAR(MAX) = JSON_OBJECT(
    'question': @question,
    'context': JSON_QUERY(@contextJson)
);

-- Call OpenAI
DECLARE @response NVARCHAR(MAX);
EXEC sp_invoke_external_rest_endpoint
    @url     = 'https://myopenai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-02-01',
    @method  = 'POST',
    @payload = @payload,
    @headers = N'{"api-key":"YOUR_KEY"}',
    @response = @response OUTPUT;

-- Extract answer (note the $.result prefix — sp_invoke wraps response in $.result)
SELECT JSON_VALUE(@response, '$.result.choices[0].message.content') AS answer;
```

**Critical**: `sp_invoke_external_rest_endpoint` wraps the actual HTTP response body under `$.result` in the returned JSON. So the path is `$.result.choices[0].message.content` — NOT `$.choices[0].message.content`.

### FOR JSON Options

| Option | Output |
|--------|--------|
| `FOR JSON PATH` | Structured array of JSON objects |
| `FOR JSON AUTO` | Auto-inferred structure from SELECT columns |
| `FOR JSON PATH, WITHOUT_ARRAY_WRAPPER` | Single JSON object (not an array) |
| `FOR XML PATH('')` | XML — wrong for LLM payloads |

**Exam example (q059)**: To build a single-document context: → `FOR JSON PATH, WITHOUT_ARRAY_WRAPPER`

### JSON_VALUE vs JSON_QUERY

| Function | Use |
|----------|-----|
| `JSON_VALUE(json, path)` | Extract **scalar** value (string, number) |
| `JSON_QUERY(json, path)` | Extract **object or array** (preserves structure) |

Use `JSON_VALUE` to extract the LLM answer text. Use `JSON_QUERY` to embed a JSON sub-object into a larger JSON payload.

---

## 10. GitHub Copilot for Azure SQL + MCP (1.4 Quick Skim)

### Copilot Instruction Files in SQL Database Projects

- `.github/copilot-instructions.md` → workspace-level AI instructions (applies to all files)
- `.instructions.md` files → scoped instructions (applyTo pattern)
- Used to tell Copilot about naming conventions, schema standards, query patterns
- These are PLAIN TEXT/MARKDOWN files checked into the repo alongside SQL project files

### MCP (Model Context Protocol) for SQL

- MCP servers expose database context (schema, query history) to AI assistants
- Configured in VS Code's `mcp.json` or `.vscode/mcp.json`
- Azure SQL MCP server: enables AI tools to introspect schema and run queries safely
- Exam framing: "How do you give Copilot knowledge of your database schema?" → MCP server configuration

### Exam Tips

- GitHub Copilot doesn't auto-generate schema without context → need instruction files or MCP
- MCP is about providing AI with **context**, not about executing arbitrary SQL
- Copilot Chat in VS Code with SQL extension = interactive query assistance

---

## Common Exam Traps

| Trap | Reality |
|------|---------|
| `MODEL_TYPE = COMPLETIONS` for chat | Only `EMBEDDINGS` is supported in `CREATE EXTERNAL MODEL` — no chat model type |
| Azure Functions SQL binding uses CDC | **Uses Change Tracking** — CDC is a distractor |
| `VECTOR_NORMALIZE` fixes slow search | Still needs a VECTOR INDEX + VECTOR_SEARCH for ANN performance |
| `VECTOR_DISTANCE` uses the vector index | **Never** — it's always exact, ignores indexes |
| `TOP_N` in VECTOR_SEARCH (legacy) | Raises Msg 42274 with v3+ indexes — use `SELECT TOP (N) WITH APPROXIMATE` |
| `queryType = "hybrid"` in Azure AI Search | No such value — use `queryType = "semantic"` for semantic ranking of hybrid results |
| `semanticConfiguration` = "semantic" | It's the **index name** (e.g., "hotels"), not a generic value |
| Switching models → just update EXTERNAL MODEL | Must also **regenerate all existing embeddings** — different models → different vector spaces |
| `captures_net_changes = 0` supports `fn_cdc_get_net_changes_*` | Only `= 1` enables net change queries |
| `WITH APPROXIMATE` works with `VECTOR_DISTANCE` | Requires `VECTOR_SEARCH`, not `VECTOR_DISTANCE` |
| ORDER BY `r.distance DESC` in VECTOR_SEARCH | Only ASC supported — distance is always lower-is-better |
| VECTOR column can have CHECK constraint | Only NULL/NOT NULL constraints allowed |
| Embed a numeric score column | Embed **free-text** columns — numeric/categorical are filter predicates |
| sp_invoke response path is `$.choices[...]` | It's `$.result.choices[...]` — the response is wrapped in `$.result` |
| TRUNCATE with vector index = drop rows | Must drop index first, then truncate, then reload ≥100 rows, then recreate |
| cosine metric for chunks of different sizes | ✅ Correct — cosine is magnitude-insensitive, ideal for variable-length text |
| captions type = "generative" | Use `"extractive"` for captions in Azure AI Search |

---

## Quick Reference

### EXTERNAL MODEL Setup Checklist

1. `sp_configure 'external rest endpoint enabled', 1` + `RECONFIGURE`
2. `CREATE MASTER KEY` (if not exists)
3. `CREATE DATABASE SCOPED CREDENTIAL [<url_prefix>]`
4. `CREATE EXTERNAL MODEL ... WITH (LOCATION, API_FORMAT, MODEL_TYPE, MODEL, CREDENTIAL)`
5. `GRANT EXECUTE ON EXTERNAL MODEL::<Name> TO [user]`

### Vector Search Pattern Selector

| Situation | Pattern |
|-----------|---------|
| Small dataset, exact results | `VECTOR_DISTANCE` + ORDER BY |
| Large dataset, fast approximate | `CREATE VECTOR INDEX` + `VECTOR_SEARCH` + `SELECT TOP (N) WITH APPROXIMATE` |
| Hybrid: vector + keyword | `VECTOR_SEARCH` joined with `CONTAINSTABLE` |
| No outbound connectivity | ONNX Runtime local model |
| Need old + new values | CDC |
| Azure Functions binding | Change Tracking |

### Key Catalog Views

| View | What It Shows |
|------|--------------|
| `sys.external_models` | Registered external models |
| `sys.vector_indexes` | Vector index metadata + version |
| `sys.dm_db_vector_indexes` | Vector index health + maintenance status |

### Distance Metric Quick Reference

| Metric | For | Lower = |
|--------|-----|---------|
| `cosine` | Text embeddings (most common) | More similar angle |
| `euclidean` | Spatial/image embeddings | Closer in space |
| `dot` | Pre-normalized vectors | More similar direction |

---

## Related Questions

q047, q048, q049, q050, q051, q052, q053, q054, q055, q056, q084, q085, q086, q087

```powershell
python quiz_runner.py --ids q047,q048,q049,q050,q051,q052,q053,q054,q055,q056,q084,q085,q086,q087 questions.json
```
