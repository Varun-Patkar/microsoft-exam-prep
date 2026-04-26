# Day 1 Session 1: Database Objects + Programmability
**Date**: 2026-04-26
**Domain**: 1. Design and Develop Database Solutions (35–40%)
**Subtopics**: 1.1 Database Objects, 1.2 Programmability Objects

---

## 1.1 Design and Implement Database Objects

### Tables, Data Types, Indexes

**Core Index Types:**
| Index Type | Best For | Storage | Key Trait |
|---|---|---|---|
| Clustered Rowstore | OLTP, point lookups, small tables | Row-wise | 1 per table, IS the table |
| Nonclustered Rowstore | Selective queries, lookups | Separate B-tree | Multiple per table |
| Clustered Columnstore | Large analytics/DW, batch loads | Column-wise compressed | 10x compression, batch mode |
| Nonclustered Columnstore | Real-time analytics on OLTP table | Column copy on rowstore | HTAP pattern — analytics + OLTP coexist |
| Filtered Nonclustered | Subset indexing (e.g., Active=1) | B-tree with WHERE | Smaller, targeted index |
| HASH (in-memory only) | Point lookups on memory-optimized tables | Hash buckets | Must specify BUCKET_COUNT |

**Exam Traps:**
- Clustered columnstore = DW/analytics workloads with large scans + aggregations
- Nonclustered columnstore on rowstore = NRT (near-real-time) analytics ON TOP of OLTP
- Both NRT analytics AND reduce read time → same answer: nonclustered columnstore on rowstore
- Filtered nonclustered = only index rows matching a predicate (e.g., WHERE Active = 1)
- HASH index = in-memory tables ONLY, optimal for equality/point lookups

**Ordered Columnstore:**
- Available SQL Server 2022+, Azure SQL DB, Fabric SQL DB
- Enables segment elimination → skips data that doesn't match query predicate
- Slower to load (sort overhead), faster to query

### Specialized Tables

#### In-Memory (Memory-Optimized) Tables
- `MEMORY_OPTIMIZED = ON` in CREATE TABLE
- Two durability modes:
  - `SCHEMA_AND_DATA` (default) — survives restart, fully durable
  - `SCHEMA_ONLY` — data lost on restart, zero IO, great for temp/cache/transient data
- Indexes: HASH (point lookups) or NONCLUSTERED (range scans)
- Up to 30x faster for OLTP
- Requires MEMORY_OPTIMIZED_DATA filegroup
- **Exam pattern**: "reduce write latency" + "doesn't need to persist" → SCHEMA_ONLY + HASH

#### Temporal Tables (System-Versioned)
- Auto-track history of all changes
- Two period columns: `ValidFrom` (datetime2), `ValidTo` (datetime2)
- Syntax: `PERIOD FOR SYSTEM_TIME (ValidFrom, ValidTo)` + `SYSTEM_VERSIONING = ON`
- History table stores previous versions automatically
- Query with `FOR SYSTEM_TIME AS OF / BETWEEN / CONTAINED IN / ALL`
- Use cases: audit, point-in-time recovery, slowly changing dimensions
- **Exam pattern**: "track changes over time" or "audit" → temporal table

#### External Tables
- Reference data outside SQL Server (Azure Blob, ADLS, other SQL DBs)
- Schema defined locally, data lives externally
- Requires EXTERNAL DATA SOURCE + EXTERNAL FILE FORMAT
- Read-only (mostly) — used for data virtualization / PolyBase

#### Ledger Tables
- Tamper-evidence via cryptographic hashing (blockchain-like)
- Two types:
  - **Updatable** — tracks history like temporal, with crypto hashing
  - **Append-only** — INSERT only, no UPDATE/DELETE allowed
- Ledger database = all tables are ledger tables by default
- Database digests stored in tamper-proof storage (Azure Blob immutable / Confidential Ledger)
- Use cases: financial records, audit trails, compliance
- **Exam pattern**: "tamper-proof" or "cryptographic verification" → ledger

#### Graph Tables
- NODE tables (entities) and EDGE tables (relationships)
- Query with `MATCH` clause: `MATCH (person-(friendOf)->friend)`
- Good for: social networks, fraud detection, hierarchical relationships
- Stored in same SQL database, queryable with T-SQL + MATCH

### JSON Columns and Indexes
- Store JSON in `nvarchar(max)` columns
- Validate with `ISJSON()`
- Extract values: `JSON_VALUE()` (scalar), `JSON_QUERY()` (object/array)
- Computed columns + indexes on JSON paths for performance
- Example: `ALTER TABLE ADD col AS JSON_VALUE(JsonCol, '$.path') PERSISTED`
- Index the computed column for fast lookups

### Constraints
| Constraint | Purpose | Key Detail |
|---|---|---|
| PRIMARY KEY | Unique row identity | Creates clustered index by default, NOT NULL enforced |
| FOREIGN KEY | Referential integrity | Points to PK/UNIQUE of another table |
| UNIQUE | No duplicate values | Allows ONE null (unlike PK) |
| CHECK | Custom validation rules | Can enforce `CHECK (Owner IS NOT NULL)` |
| DEFAULT | Auto-fill value | Applied when no value provided on INSERT |

**Exam trap**: "ensure future records have a value for field" → CHECK constraint (not UNIQUE, not FK)

### SEQUENCES
- Standalone number generator — not tied to a single table
- `CREATE SEQUENCE ... AS INT START WITH X INCREMENT BY Y`
- Get next: `NEXT VALUE FOR SequenceName`
- Can be shared across multiple tables (unlike IDENTITY)
- Can get next value WITHOUT inserting a row
- **Exam pattern**: "same number series across tables" + "without inserting" → SEQUENCE + NEXT VALUE FOR

### Partitioning
- Split large table into segments by a column (e.g., date)
- Components: PARTITION FUNCTION → PARTITION SCHEME → table ON scheme
- **RANGE LEFT**: boundary value belongs to LEFT partition (<=)
- **RANGE RIGHT**: boundary value belongs to RIGHT partition (>=, start of next)
- `TRUNCATE TABLE ... WITH (PARTITIONS (N))` — fast, minimal logging, partition-specific delete
- **Exam traps**:
  - RANGE RIGHT with boundaries '2020-01-01', '2021-01-01' → partitions: <2020, [2020,2021), [2021,...)
  - TRUNCATE TABLE (no partition spec) = deletes ALL data
  - DELETE with WHERE = fully logged, heavy locks, NOT minimal impact
  - TRUNCATE WITH (PARTITIONS (N)) = correct answer for "remove oldest month, minimize impact"

---

## 1.2 Implement Programmability Objects

### Views
- **Standard View**: virtual table, `CREATE VIEW ... AS SELECT ...`
  - No parameters allowed
  - Can be used in joins
  - Good for simplifying complex queries, security (expose subset of columns)
- **Indexed (Materialized) View**: `WITH SCHEMABINDING` + `CREATE UNIQUE CLUSTERED INDEX`
  - Physically stores data — improves read performance
  - Must use SCHEMABINDING (view can't break if underlying table changes)
  - Restrictions: no outer joins, no subqueries in SELECT, no UNION, etc.
  - Auto-maintained by engine on DML operations

### Scalar Functions
- Return single value
- `CREATE FUNCTION ... RETURNS INT AS BEGIN ... RETURN @val END`
- Two styles:
  - **Traditional**: multi-statement, BEGIN/END block
  - **Inline**: single expression (SQL Server 2019+ can inline traditional ones too)
- Historically poor performance (row-by-row execution)
- SQL Server 2019+: Scalar UDF Inlining → compiler inlines function into query plan
- `DATEDIFF(day, @start, @end)` — common exam pattern for "days between"

### Table-Valued Functions (TVFs)
- **Inline TVF**: `RETURNS TABLE AS RETURN (SELECT ...)` — single SELECT, best performance
  - Optimizer treats like a view — can be optimized
  - Supports joins — this is a key exam point
  - Accepts parameters (unlike views)
- **Multi-statement TVF**: `RETURNS @t TABLE (...) AS BEGIN INSERT @t ... RETURN END`
  - Declare table variable, populate with logic, return
  - Worse performance (optimizer can't see inside)
- **Exam pattern**: "support joins" + "accept parameter" + "return table" → inline TVF
- Inline TVF body pattern: `RETURNS TABLE AS RETURN` followed by SELECT

### Stored Procedures
- `CREATE PROCEDURE ... AS BEGIN ... END`
- Can use TVPs (Table-Valued Parameters):
  - First: `CREATE TYPE dbo.MyType AS TABLE (...)`
  - Then: `@param dbo.MyType READONLY` in proc signature
  - Pass structured data as parameter
- Error handling: `TRY/CATCH`, `THROW`, `XACT_STATE()`, `@@TRANCOUNT`
- Can return multiple result sets
- Can have OUTPUT parameters

### Triggers
- **DML Triggers**: fire on INSERT/UPDATE/DELETE
  - `AFTER` (default): fires after the DML completes
  - `INSTEAD OF`: replaces the DML action (can be on views!)
  - Access `INSERTED` and `DELETED` virtual tables inside trigger
- **DDL Triggers**: fire on CREATE/ALTER/DROP statements
  - Scope: DATABASE or SERVER level
  - Use cases: auditing schema changes, preventing drops
- **Exam pattern**: "prevent deletion" or "validate before insert on a view" → INSTEAD OF trigger

---

## Common Exam Patterns

1. **"reduce write latency, doesn't need to persist"** → SCHEMA_ONLY in-memory + HASH index
2. **"large table, analytics, aggregations"** → clustered columnstore
3. **"analytics on OLTP table without affecting throughput"** → nonclustered columnstore
4. **"index only rows matching predicate"** → filtered nonclustered index
5. **"track data changes over time"** → temporal table
6. **"tamper-proof, cryptographic"** → ledger table
7. **"shared number series across tables"** → SEQUENCE + NEXT VALUE FOR
8. **"remove oldest partition data, minimize impact"** → TRUNCATE TABLE WITH (PARTITIONS)
9. **"accept parameter + return table + support joins"** → inline TVF
10. **"ensure field has value in future records"** → CHECK constraint

---

## Related Questions
- q001: In-memory table type + HASH index (SCHEMA_ONLY)
- q002: Columnstore vs rowstore index selection
- q003: Nonclustered columnstore + filtered index for HTAP
- q004: Partition function (RANGE RIGHT + boundary values)
- q005: CHECK constraint to ensure non-null values
- q006: SEQUENCE + NEXT VALUE FOR across tables
- q007: TRUNCATE TABLE (no partition) = wrong answer
- q008: DELETE with WHERE = wrong answer (heavy logging)
- q009: TRUNCATE WITH PARTITIONS = correct answer
- q010: Inline TVF (returns table, accepts param, joinable)
- q011: Scalar UDF (RETURNS INT, DATEDIFF)
- q012: TVF with window function (running total)
- q056–q057: Bonus questions
