# Day 3: Optimize Database Performance (2.2)

**Date**: 2026-04-28
**Domain**: 2 — Secure, Optimize, and Deploy Database Solutions (35–40%)
**Subtopics**: Transaction isolation levels, execution plans, DMVs, Query Store, Query Performance Insight, blocking & deadlocks

---

## 1. Transaction Isolation Levels

### The Spectrum (Low → High Isolation)

| Level                    | Dirty Reads | Non-Repeatable Reads | Phantoms | Lock Behavior                                          |
| ------------------------ | ----------- | -------------------- | -------- | ------------------------------------------------------ |
| READ UNCOMMITTED         | ✅ Yes      | ✅ Yes               | ✅ Yes   | No shared locks on reads                               |
| READ COMMITTED (default) | ❌ No       | ✅ Yes               | ✅ Yes   | Shared locks released after each read                  |
| REPEATABLE READ          | ❌ No       | ❌ No                | ✅ Yes   | Shared locks held until end of transaction             |
| SERIALIZABLE             | ❌ No       | ❌ No                | ❌ No    | Range locks (key-range locks) prevent inserts in range |
| SNAPSHOT                 | ❌ No       | ❌ No                | ❌ No    | Row versioning — transaction-level consistency         |

### Row-Versioning Isolation Levels

**RCSI (Read Committed Snapshot Isolation)**

- Database-level setting: `ALTER DATABASE ... SET READ_COMMITTED_SNAPSHOT ON`
- Default ON in Azure SQL Database; default OFF in SQL Server / Azure SQL MI
- Readers see **statement-level** snapshot — the committed data at start of each statement
- Readers don't block writers, writers don't block readers
- No shared locks for reads — only Sch-S (schema stability) locks
- Uses tempdb version store (or PVS with ADR)

**SNAPSHOT Isolation**

- Database-level setting: `ALTER DATABASE ... SET ALLOW_SNAPSHOT_ISOLATION ON`
- Session-level: `SET TRANSACTION ISOLATION LEVEL SNAPSHOT` (must be set BEFORE BEGIN TRAN)
- Readers see **transaction-level** snapshot — committed data at start of the transaction
- Update conflicts: if another transaction committed a change to a row after the snapshot transaction started, trying to modify that row raises error 3960 and terminates the transaction
- Uses row versioning in tempdb (or PVS)

### Key Exam Distinctions

| Feature               | RCSI                                  | SNAPSHOT                   |
| --------------------- | ------------------------------------- | -------------------------- |
| Consistency level     | Statement                             | Transaction                |
| DB option             | READ_COMMITTED_SNAPSHOT               | ALLOW_SNAPSHOT_ISOLATION   |
| Session SET needed?   | No (transparent)                      | Yes, before BEGIN TRAN     |
| Update conflicts?     | Auto-handled (with optimized locking) | App must handle error 3960 |
| Azure SQL DB default  | ON                                    | ON                         |
| Writes block writers? | Yes (X locks still taken)             | Yes (X locks still taken)  |

### Common Exam Traps

- **RCSI is transparent** — existing apps using READ COMMITTED automatically benefit. SNAPSHOT requires session-level SET.
- **Both still acquire exclusive locks for writes** — isolation level only affects READ behavior.
- **SERIALIZABLE uses key-range locks**, not just row locks — prevents phantom inserts.
- **SNAPSHOT sees data as of transaction start**, RCSI sees data as of **each statement's** start.
- An uncommitted explicit transaction (BEGIN TRAN + UPDATE without COMMIT) holds X locks under ALL isolation levels and blocks other writers and readers (except NOLOCK / READ UNCOMMITTED / row-versioning readers).

---

## 2. Execution Plans

### Scan vs Seek

| Operator                 | Description                            | When Used                                           |
| ------------------------ | -------------------------------------- | --------------------------------------------------- |
| **Index Seek**           | Navigates B-tree to find specific rows | Selective predicate on indexed column (SARGable)    |
| **Index Scan**           | Reads entire index leaf level          | Non-selective predicate, or non-SARGable expression |
| **Clustered Index Seek** | Seek on clustered index                | Predicate on clustering key                         |
| **Clustered Index Scan** | Full table scan via clustered index    | No useful index for the query                       |
| **Table Scan**           | Full scan of a heap                    | Heap table, no useful index                         |

### SARGable vs Non-SARGable

- **SARGable** (Search ARGument able): `WHERE col = @val`, `WHERE col > 5`, `WHERE col LIKE 'abc%'`
- **Non-SARGable**: `WHERE YEAR(DateCol) = 2024` — wrapping a column in a function prevents seek
- **Fix**: Rewrite as `WHERE DateCol >= '2024-01-01' AND DateCol < '2025-01-01'`
- Similarly: `WHERE UPPER(Name) = 'JOHN'` prevents seek → use case-insensitive collation or computed column

### Key Lookup

- Occurs when a nonclustered index satisfies the WHERE clause (seek) but the SELECT list requires columns not in the index
- Engine must do a **Key Lookup** (bookmark lookup) into the clustered index to fetch remaining columns
- **Fix**: Add INCLUDE columns to the nonclustered index (covering index) to eliminate the lookup
- High key lookup count = performance problem — each lookup is a random I/O

### Estimated vs Actual Rows

- **Estimated rows**: Based on statistics — what the optimizer predicted
- **Actual rows**: Real number from execution
- Large discrepancy → stale statistics or parameter sniffing → poor plan choice
- Check with actual execution plans (Ctrl+M in SSMS), not estimated plans

---

## 3. Dynamic Management Views (DMVs)

### Key DMVs for Performance

| DMV                                   | Purpose                                     | Key Columns                                                                       |
| ------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------- |
| `sys.dm_exec_query_stats`             | Cumulative execution stats for cached plans | total_worker_time (CPU), total_elapsed_time, execution_count, total_logical_reads |
| `sys.dm_exec_requests`                | Currently executing requests                | session_id, status, blocking_session_id, wait_type, command                       |
| `sys.dm_exec_sql_text(sql_handle)`    | Get SQL text from a plan handle             | text                                                                              |
| `sys.dm_exec_query_plan(plan_handle)` | Get XML execution plan                      | query_plan                                                                        |
| `sys.dm_tran_locks`                   | Current locks held/requested                | resource_type, request_mode, request_status (GRANT/WAIT)                          |
| `sys.dm_os_wait_stats`                | Aggregate wait stats for the instance       | wait_type, waiting_tasks_count, wait_time_ms                                      |
| `sys.dm_exec_sessions`                | Active sessions                             | session_id, login_name, status, host_name                                         |

### Finding Top CPU-Consuming Queries

```sql
SELECT TOP 10
    qs.total_worker_time / qs.execution_count AS avg_cpu_time,
    qs.execution_count,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text)
          ELSE qs.statement_end_offset END - qs.statement_start_offset)/2)+1) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY qs.total_worker_time DESC;
```

### Finding Blocking

```sql
SELECT
    r.session_id,
    r.blocking_session_id,
    r.wait_type,
    r.wait_time,
    t.text AS sql_text
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE r.blocking_session_id <> 0;
```

---

## 4. Query Store + Query Performance Insight

### Query Store

- **What it is**: A flight recorder for query performance — captures queries, execution plans, and runtime stats over time
- **Enabled by default**: SQL Server 2022+, Azure SQL DB, Fabric SQL DB
- **Three internal stores**: plan store, runtime stats store, wait stats store
- **Key capability**: **Plan forcing** — pin a known-good execution plan to a query to prevent regression

### Query Store Architecture

- Stores **multiple plans per query** (unlike plan cache which only keeps the latest)
- Separates data by **time windows** — see how performance changed over time
- Key catalog views:
  - `sys.query_store_query` — queries
  - `sys.query_store_plan` — plans
  - `sys.query_store_runtime_stats` — execution stats (CPU, duration, reads, etc.)
  - `sys.query_store_query_text` — SQL text
  - `sys.query_store_wait_stats` — per-query wait stats (SQL 2017+)

### Plan Regression Detection

1. Query Store detects when a query switches to a worse plan
2. **Regressed Queries** report in SSMS shows queries whose performance degraded
3. You can **force** the previous (better) plan: `EXEC sp_query_store_force_plan @query_id, @plan_id`
4. You can also unforce: `EXEC sp_query_store_unforce_plan @query_id, @plan_id`

### Query Store Configuration

```sql
ALTER DATABASE [MyDB] SET QUERY_STORE = ON (
    OPERATION_MODE = READ_WRITE,
    MAX_STORAGE_SIZE_MB = 1024,
    QUERY_CAPTURE_MODE = AUTO,           -- ignore trivial queries
    WAIT_STATS_CAPTURE_MODE = ON,        -- capture per-query waits
    STALE_QUERY_THRESHOLD_DAYS = 30
);
```

### Query Performance Insight (Azure SQL DB only)

- **Azure portal blade**: Intelligent Performance → Query Performance Insight
- Built on top of Query Store (requires Query Store to be ON)
- Shows **top CPU-consuming queries** with DTU overlay chart
- Can drill into individual queries by CPU, duration, execution count
- Shows performance recommendation annotations from Database Advisor
- Limited to top 5–20 queries — for deeper analysis, use database watcher

### Exam Pattern

- "Which tool shows top resource-consuming queries in Azure portal?" → **Query Performance Insight**
- "How to prevent plan regression?" → **Query Store forced plans**
- "Where are query plans stored over time?" → **Query Store plan store**
- "Which sp forces a plan?" → `sp_query_store_force_plan`

---

## 5. Blocking & Deadlocks

### Blocking

- Occurs when one session holds a lock and another session needs a conflicting lock on the same resource
- **Not a bug** — normal behavior, but excessive blocking hurts performance
- **Head blocker**: The session at the top of the blocking chain (the root cause)

### Identifying Blocking

1. `sys.dm_exec_requests` — check `blocking_session_id` column (non-zero = blocked)
2. `sys.dm_tran_locks` — check `request_status = 'WAIT'` for waiting lock requests
3. `sys.dm_os_waiting_tasks` — shows waiting tasks and what's blocking them
4. Activity Monitor in SSMS — visual blocking chain

### Common Blocking Causes

- Long-running transactions (especially uncommitted explicit transactions)
- Inappropriate isolation levels (e.g., SERIALIZABLE when not needed)
- Missing indexes causing long scans that hold locks longer
- Application not committing/rolling back transactions promptly

### Resolving Blocking

- Use RCSI to eliminate reader-writer blocking
- Keep transactions short
- Add appropriate indexes to reduce lock duration
- Use `KILL <session_id>` for the head blocker (last resort)

### Deadlocks

- **Circular wait**: Session A waits for Session B, and Session B waits for Session A
- SQL Server **automatically detects** deadlocks (lock monitor thread)
- **Deadlock victim**: SQL Server chooses the cheaper transaction to roll back (error 1205)
- **Cannot be completely eliminated** — but can be minimized

### Deadlock Prevention Strategies

1. **Consistent access ordering**: All transactions access tables in the same order (Table A → Table B)
2. **Keep transactions short**: Less time holding locks = less chance of deadlock
3. **Use row-versioning isolation** (RCSI/SNAPSHOT): Eliminates read-write deadlocks
4. **Avoid the "read then update" pattern**: Use UPDLOCK hint to prevent S→X conversion deadlocks
5. **Minimize lock footprint**: Use appropriate indexes, avoid scans

### Capturing Deadlock Information

- **Extended Events**: `sqlserver.xml_deadlock_report` (recommended)
- **Trace Flag 1222**: Logs deadlock graph to error log
- **system_health** session: Captures deadlock graphs by default in SQL Server
- **Azure SQL DB**: Deadlock graphs captured automatically, visible in portal

### tempdb Contention

- Version store (RCSI/SNAPSHOT) lives in tempdb
- Multiple data files recommended (1 per logical CPU, up to 8)
- Trace flag 1118 (pre-2016): Allocate uniform extents to reduce PFS/GAM/SGAM contention
- Azure SQL DB: tempdb contention handled automatically

---

## Quick Reference

### Isolation Level Decision Tree

- Need dirty reads for reporting? → READ UNCOMMITTED
- Default, no special needs? → READ COMMITTED
- Need repeatable reads within transaction? → REPEATABLE READ
- Need to prevent phantom reads? → SERIALIZABLE
- Need non-blocking reads with statement consistency? → RCSI
- Need transaction-level point-in-time consistency? → SNAPSHOT

### Performance Troubleshooting Flow

1. **Identify slow queries** → Query Store / QPI / `sys.dm_exec_query_stats`
2. **Check execution plan** → Index seeks vs scans, key lookups, estimated vs actual rows
3. **Check blocking** → `sys.dm_exec_requests.blocking_session_id`
4. **Check waits** → `sys.dm_os_wait_stats` / Query Store wait stats
5. **Fix** → Add/modify indexes, rewrite non-SARGable predicates, enable RCSI, force good plans

---

## Related Questions

q030, q031, q032, q033, q034, q071 (cross-topic), q073, q078
