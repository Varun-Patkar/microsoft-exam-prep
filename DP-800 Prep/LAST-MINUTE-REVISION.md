# DP-800 Last-Minute Revision Guide

> Final review before exam day. All traps, major concepts, and deep dives on your weak areas.

---

## 🚨 CRITICAL TRAPS (Organized by Domain)

### Domain 1: Design & Develop

#### T-SQL Traps

| Trap | Why It's Wrong | Correct Answer |
|------|----------------|-----------------|
| Default frame in window functions with ORDER BY is ROWS | Default is actually RANGE when ORDER BY is present. Can cause wrong results with tied values | Check execution plan: `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` is default, not ROWS |
| `JSON_VALUE` can extract objects/arrays | `JSON_VALUE` only returns **scalar** values as nvarchar(4000) | Use `JSON_QUERY` for objects/arrays |
| Recursive CTE without MAXRECURSION limit | MAXRECURSION 0 = unlimited, allows infinite loops | Always set reasonable MAXRECURSION, typically 50-100 |
| REGEXP functions work at all compatibility levels | REGEXP_LIKE needs 170, REGEXP_* family needs 170 but exceptions exist | Check SQL Server 2025 docs; default is level 170 |
| RANK/DENSE_RANK both skip row numbers the same way | RANK creates gaps (1,1,3), DENSE_RANK doesn't (1,1,2) | Use ROW_NUMBER for unique, DENSE_RANK for no gaps, RANK for standard ranking |

#### Database Objects Traps

| Trap | Why It's Wrong | Correct Answer |
|------|----------------|-----------------|
| Columnstore indexes can be used on all column types | BLOB types (FILESTREAM, etc.) incompatible | Check data types before suggesting columnstore |
| VECTOR columns can use PK, FK, or DEFAULT constraints | VECTOR only supports NULL/NOT NULL | Cannot enforce uniqueness on VECTOR columns |
| Graph tables work the same as regular tables | NODE tables have special node properties, EDGE tables have edge semantics | Treat graph queries differently: use MATCH for relationships |

### Domain 2: Secure, Optimize, Deploy

#### 2.1 Security Traps

| Trap | Why It's Wrong | Correct Answer |
|------|----------------|-----------------|
| Ledger + Always Encrypted: create table first, then encrypt | Tables with LEDGER clause are immutable, encryption must be planned upfront | CREATE CEK → CREATE ledger table → THEN copy data → encrypt |
| DDM + RLS together: both apply independently | If RLS filters a row OUT, DDM never runs (row was already filtered) | RLS happens first, DDM is presentation layer only |
| `GRANT UNMASK` alone gives access to unmasked data | UNMASK is a **permission**, not standalone. User needs SELECT + UNMASK | Always grant both SELECT and UNMASK |
| Deterministic Always Encrypted supports all queries | Deterministic supports EQ/IN/GROUP BY but NOT range queries or LIKE | Use randomized for high security, deterministic for query compatibility |

#### 2.2 Performance Traps (YOUR WEAK AREA)

| Trap | Why It's Wrong | Correct Answer |
|------|----------------|-----------------|
| Query Store and DMVs store the same data | Query Store is **persisted history by time windows**; DMVs are **current cache state** | Use Query Store for trends/regression, DMVs for live diagnostics |
| `sys.dm_exec_query_stats` has historical CPU data over days | DMVs only keep current session data, cleared on restart | For historical CPU analysis, use `sys.query_store_runtime_stats` |
| REPEATABLE READ prevents phantoms | REPEATABLE READ only locks existing rows; SERIALIZABLE adds key-range locks | If question says "prevent inserts in range", you need SERIALIZABLE |
| SERIALIZABLE uses just row locks | SERIALIZABLE uses key-range locks (gap locks) to block new inserts | This is what makes it prevent phantoms |
| RCSI and SNAPSHOT isolation work identically | RCSI is **statement**-level snapshot; SNAPSHOT is **transaction**-level. Different consistency guarantees | Check if question asks for transaction-wide consistency (SNAPSHOT) or statement-by-statement (RCSI) |

#### 2.3 CI/CD Traps

| Trap | Why It's Wrong | Correct Answer |
|------|----------------|-----------------|
| Microsoft.SqlServer.Dacpacs.Master works for Azure SQL DB | Wrong package—Azure SQL DB needs **Azure.Master** | For Azure targets: `Microsoft.SqlServer.Dacpacs.Azure.Master` |
| `-bl` and `-flp:vdiag` flags fix missing system references | These only control logging verbosity | Add the correct NuGet package for system DB references |
| Using plain INSERT in post-deployment scripts | INSERT fails on second deployment (duplicate key). Post-deploy runs **every** deployment | Use MERGE or IF NOT EXISTS for idempotency |
| `dotnet build -c Release` with unchanged publish step | Dacpac moves to `bin/Release/`, but publish still points to `bin/Debug/` | Update dacpac path in publish step when changing build config |
| `extract` action in azure/sql-action deploys a dacpac | `extract` creates a dacpac FROM a database. `publish` deploys TO a database. Opposite directions | Use `publish` for deployment, `extract` for reverse-engineering |
| `workflow_dispatch` prevents manual triggering | `workflow_dispatch` **enables** manual triggering via UI | This allows ad-hoc deployments |

#### 2.4 DAB + Azure Integration Traps (YOUR WEAK AREA)

| Trap | Why It's Wrong | Correct Answer |
|------|----------------|-----------------|
| DAB REST URL is `/api/{Entity}` | Missing the `/data-api` prefix. Correct: `/data-api/api/{Entity}` | All DAB endpoints start with `/data-api` |
| Firewall rule 0.0.0.0–0.0.0.0 opens database to internet | This rule **only allows Azure services**, not public internet | Container Apps count as "Azure services" → this is the intended setup |
| Container Apps with "Internal" ingress can reach from internet | "Internal" = only VNet access. Must be "External" for public API | DAB serving public clients needs External ingress |
| `anonymous` role requires a token to read | `anonymous` = no auth required. Explicit grant → public read allowed | If table has `"role":"anonymous", "actions":["read"]`, anyone can read |
| `read` + `create` actions = can also update | Each action is separate. `create` ≠ `update`. Must list explicitly | If only `["read","create"]` → cannot update. If question says "update", answer is No |
| Stored procedure entity has `read` action | Stored procedures use `execute` action, not `read`/`write` | Proc entity must have `"actions":["execute"]` |
| Request without `X-MS-API-ROLE` header uses `anonymous` role | No header + valid token → defaults to `authenticated` role | Only truly unauthenticated requests use `anonymous` |
| Azure Functions SQL trigger binding uses CDC | Azure Functions SQL binding uses **Change Tracking**, not CDC | If question says "Azure Functions SQL trigger binding", answer is Change Tracking |
| CDC is lighter overhead than Change Tracking | Change Tracking is lighter. CDC captures old+new values (more overhead) | Use Change Tracking for Azure Functions, CDC when you need before/after values |

### Domain 3: AI Capabilities

| Trap | Why It's Wrong | Correct Answer |
|------|----------------|-----------------|
| `MODEL_TYPE = COMPLETIONS` is a valid option | Only `EMBEDDINGS` exists as MODEL_TYPE | CREATE EXTERNAL MODEL only registers embedding models |
| Switching embedding models = just update the model endpoint | Different models produce different vector spaces. All vectors must be regenerated | When switching models: 1) Regenerate all embeddings first 2) Then update endpoint |
| VECTOR_DISTANCE is fast on large tables | VECTOR_DISTANCE = exact k-NN, full scan every query. Slow at scale | Use VECTOR_SEARCH with vector indexes (DiskANN) for > 50k vectors |
| VECTOR_SEARCH works without a vector index | Without index, it falls back to exact k-NN (slow). Index is required for ANN performance | Create vector index: `CREATE VECTOR INDEX idx_embedding ON table(column)` |
| `ORDER BY distance DESC` works in VECTOR_SEARCH | Only `ASC` allowed, only on distance column. DESC → error | Use subquery wrapper if you need multi-column sort |
| `TOP N` without `WITH APPROXIMATE` uses ANN | Without APPROXIMATE, falls back to exact k-NN | Always add `WITH APPROXIMATE` for ANN on indexed vectors |
| All distance metrics give the same results | Metrics measure differently: cosine = angle, euclidean = distance, dot = product | Cosine is best for variable-size text chunks (ignores magnitude) |
| Chunking just reduces file size | Chunking reduces token count per retrieval AND improves RAG precision | Answer when Q says "reduce tokens" or "improve RAG performance" |

---

## 📚 MAJOR THINGS TO REMEMBER

### Quick Reference by Question Type

#### "Which view/DMV contains..."
- **Query Store data** → `sys.query_store_*` (plan, runtime_stats, query_text, wait_stats)
- **Current execution info** → `sys.dm_exec_*` (query_stats, requests, sql_text)
- **Current locks** → `sys.dm_tran_locks`
- **Top CPU queries** → Query Store (historical) or `sys.dm_exec_query_stats` (current cache)

#### "How to prevent..."
- **Phantom reads** → SERIALIZABLE (not REPEATABLE READ)
- **Plan regression** → Query Store forced plans
- **Duplicate reference data** → MERGE in post-deploy scripts
- **Stale embeddings** → CDC or Change Tracking + Azure Functions

#### "Which authentication method..."
- **Passwordless** → Managed Identity (system or user-assigned)
- **Multi-resource apps** → User-assigned Managed Identity
- **Single resource** → System-assigned or user-assigned
- **DAB to Azure SQL** → Connection string from secrets OR Managed Identity

#### "What indexing strategy..."
- **Text search** → Full-text index + CONTAINS / FREETEXT
- **Fuzzy text** → Fuzzy matching functions (EDIT_DISTANCE)
- **Semantic search** → VECTOR_SEARCH with vector index (DiskANN)
- **Hybrid** → VECTOR_SEARCH + CONTAINSTABLE with weighted combination

#### "Which permission..."
- **Unmasked data** → GRANT UNMASK (+ SELECT)
- **Model execution** → GRANT EXECUTE ON EXTERNAL MODEL
- **Stored procedure execution** → GRANT EXECUTE ON procedure
- **Column-level** → GRANT/DENY on specific columns

---

## 🔥 DEEP DIVES: YOUR WEAK AREAS

### WEAK AREA #1: Query Store vs DMVs (sys.query_store_* vs sys.dm_exec_*)

**The Core Confusion:**
Both seem to store query performance data, but they're fundamentally different. The exam loves tricking you into picking the wrong one.

#### What Is Query Store?

Query Store is a **permanent recorder** of your database's execution history.

- **Scope**: Entire database (server-wide in older versions)
- **Retention**: Days/weeks/months depending on size limits you set
- **What it tracks**: Plans, runtime stats, wait stats, over time windows
- **Purpose**: Detect regressions, force plans, analyze trends
- **Catalog views**: All start with `sys.query_store_*`

**Key catalog views:**
- `sys.query_store_query` — the queries themselves (by query_id)
- `sys.query_store_plan` — multiple plans per query (by plan_id)
- `sys.query_store_runtime_stats` — execution metrics aggregated by time window (avg_duration, avg_cpu_time, total_logical_reads)
- `sys.query_store_query_text` — full SQL text
- `sys.query_store_wait_stats` — per-query wait types over time

**Time-windowed aggregation:**
- Stats are bucketed into **time intervals** (default 1 hour)
- You can see how CPU changed from 9-10am vs 10-11am
- Aggregated stats: `total_worker_time`, `total_elapsed_time`, `execution_count`

**Plan forcing:**
```sql
EXEC sp_query_store_force_plan @query_id=<N>, @plan_id=<M>;
```
This tells SQL Server: "use this specific plan for this query going forward". Prevents regression to worse plans.

#### What Are DMVs (sys.dm_exec_*)?

DMVs are **live dashboards** of what's happening RIGHT NOW.

- **Scope**: Current session + current cache only
- **Retention**: Until server restarts (non-persistent)
- **What they track**: Currently executing queries, their plans in cache, current locks, current waits
- **Purpose**: Real-time troubleshooting, live diagnostics
- **Catalog views**: All start with `sys.dm_*`

**Key DMVs for performance:**
- `sys.dm_exec_query_stats` — cumulative stats for all cached plans (total_worker_time, total_elapsed_time, execution_count) — **NOT historical**
- `sys.dm_exec_requests` — currently executing queries (session_id, status, blocking_session_id, wait_type)
- `sys.dm_exec_sql_text(sql_handle)` — SQL text of a plan
- `sys.dm_exec_query_plan(plan_handle)` — execution plan XML
- `sys.dm_tran_locks` — current locks and lock requests
- `sys.dm_os_wait_stats` — aggregate wait stats since last restart

**No persistence:**
- Query Store is OFF → no historical data
- Restart SQL Server → DMVs cleared
- Good for "what's slow RIGHT NOW", bad for "was it slow yesterday"

#### The Exam Question Pattern

| Question Asks | Answer |
|---------------|--------|
| "Query had slow CPU yesterday, you want to see if it's still slow" | Query Store — historical data |
| "Identify currently running queries with CPU spikes" | `sys.dm_exec_query_stats` or `sys.dm_exec_requests` |
| "Find top CPU query over past week" | Query Store `sys.query_store_runtime_stats` |
| "See plan execution right now" | `sys.dm_exec_requests` + `sys.dm_exec_query_plan` |
| "Compare two execution plans for same query" | Query Store `sys.query_store_plan` (multiple plans per query) |
| "Force a known-good plan" | Query Store `sp_query_store_force_plan` |

#### Memory Hooks

- **Store = history shelf** (lives on disk, survives restarts)
- **DMV = live dashboard** (current engine state, cleared on restart)
- **Store = trends** (hour-by-hour, day-by-day)
- **DMV = instant** (right-now diagnostics)

**Sentence to remember:**
> "To see what HAPPENED, ask Query Store. To see what's HAPPENING, ask DMVs."

---

### WEAK AREA #2: SERIALIZABLE vs REPEATABLE READ (Isolation Levels)

**The Core Confusion:**
Both prevent dirty reads and non-repeatable reads, so what's the real difference? The exam tests whether you know SERIALIZABLE adds **phantom protection via key-range locks**.

#### REPEATABLE READ in Detail

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN TRAN;
  SELECT * FROM Orders WHERE Status = 'Pending';
  -- ... your code here ...
COMMIT;
```

**What it locks:**
1. Takes **shared locks** on every row you read
2. **Holds those locks until END OF TRANSACTION** (not released after each statement like READ COMMITTED)
3. Blocks other transactions from:
   - Reading with READ UNCOMMITTED (dirty read)
   - Modifying those rows (UPDATE/DELETE)

**What it DOES NOT prevent:**
- **Phantom inserts**: Another transaction can INSERT new rows matching your WHERE clause between your two reads

**Example of phantom under REPEATABLE READ:**

```
Transaction A:                          Transaction B:
SELECT COUNT(*) FROM Orders             
  WHERE Status = 'Pending'              
  → Returns 5 rows, holds shared locks on those 5 rows

                                        INSERT INTO Orders 
                                          (Status = 'Pending')
                                        → SUCCESS! New row not in A's lock range

SELECT COUNT(*) FROM Orders              
  WHERE Status = 'Pending'              
  → Returns 6 rows (phantom!)
COMMIT;
```

B's INSERT succeeded because REPEATABLE READ only locks the **existing rows** it read, not the range of "any future Pending rows".

#### SERIALIZABLE in Detail

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
BEGIN TRAN;
  SELECT * FROM Orders WHERE Status = 'Pending';
  -- ... your code here ...
COMMIT;
```

**What it locks:**
1. Does everything REPEATABLE READ does (shared locks on rows)
2. **PLUS: Key-range locks** on the range `[Status='Pending']`
3. Holds locks until END OF TRANSACTION

**What it prevents:**
- Dirty reads ✓
- Non-repeatable reads ✓
- **Phantom inserts** ✓ (because of key-range locks)

**Example under SERIALIZABLE:**

```
Transaction A:                          Transaction B:
SELECT COUNT(*) FROM Orders             
  WHERE Status = 'Pending'              
  → Takes range locks on [Status='Pending']

                                        INSERT INTO Orders 
                                          (Status = 'Pending')
                                        → BLOCKED! Key-range lock prevents this

SELECT COUNT(*) FROM Orders              
  WHERE Status = 'Pending'              
  → Returns same 5 rows
COMMIT;
```

B's INSERT is blocked because A holds a key-range lock preventing any new 'Pending' rows from being inserted.

#### Performance Implications

| Level | Locks | Blocking | Use Case |
|-------|-------|----------|----------|
| REPEATABLE READ | Row locks | Blocks row updates, allows phantom inserts | General OLTP, acceptable phantom risk |
| SERIALIZABLE | Row + key-range locks | Blocks everything → high contention | Financial transactions, high integrity requirements |

**SERIALIZABLE is slow** because key-range locks are expensive and broad. Avoid unless phantom protection is critical.

#### Exam Decision Tree

1. Question mentions **"prevent inserts into range"** → SERIALIZABLE
2. Question mentions **"prevent modifying rows I already read"** → REPEATABLE READ OK
3. Question asks for **"highest isolation"** → SERIALIZABLE
4. Question says **"minimize locks for performance"** → READ COMMITTED or RCSI
5. Question says **"prevent dirty reads only"** → READ COMMITTED

#### Memory Hooks

- **Repeatable**: "I lock the rows I read, repeatable if I read again"
- **Serializable**: "I lock rows + the gaps between them, serializable means like running sequentially"
- **Phantom**: "A ghost row that appears after I already read — REPEATABLE READ can't see ghosts, SERIALIZABLE can"

**Sentence to remember:**
> "REPEATABLE READ = lock the rows. SERIALIZABLE = lock the rows AND the gaps."

---

### WEAK AREA #3: DAB Entity Permissions (anonymous, read vs update, execute)

**The Core Confusion:**
DAB has a flexible permission system where each action is a separate grant. The exam loves asking subtle permission questions where `read`+`create` ≠ `update`, or testing whether `anonymous` really means "no auth required".

#### DAB Permission Model

DAB is **secure by default**: no permission block = denied access.

Each entity (table, view, stored procedure) has a **permissions array**:

```json
"entities": {
  "TodoItems": {
    "source": "dbo.todos",
    "permissions": [
      {
        "role": "anonymous",
        "actions": ["read"]
      },
      {
        "role": "authenticated",
        "actions": ["create", "read", "update", "delete"]
      },
      {
        "role": "admin",
        "actions": ["create", "read", "update", "delete", "execute"]
      }
    ]
  }
}
```

#### Key Rules

**Rule 1: `anonymous` = no auth required**

- If a role named `anonymous` is granted `read`, then **unauthenticated requests can read that entity**
- **You must explicitly grant `anonymous`** — it doesn't happen automatically
- Without `"role": "anonymous"` block → anonymous requests denied

**Example:**
```json
"permissions": [
  { "role": "anonymous", "actions": ["read"] }  // ✓ Anyone can read
]
```

vs

```json
"permissions": [
  { "role": "authenticated", "actions": ["read"] }  // ✗ Authenticated users only
]
```

**Rule 2: Actions are separate — no grouping**

- **`read`** = SELECT only
- **`create`** = INSERT only
- **`update`** = UPDATE only
- **`delete`** = DELETE only
- **`execute`** = EXEC stored procedure

**You cannot assume `read`+`create` gives you `update`.**

**Example (q046 trap):**
```json
"Transactions": {
  "permissions": [
    { "role": "authenticated", "actions": ["read", "create"] }
  ]
}
```
This allows: SELECT, INSERT  
This does NOT allow: UPDATE, DELETE

**Question:** "Can authenticated users UPDATE rows in Transactions?"  
**Answer:** No (update not in actions)

**Rule 3: Stored procedures use `execute`, not CRUD actions**

```json
"sp_UpdateProcedure": {
  "source": { "type": "stored-procedure", "object": "dbo.usp_Update" },
  "permissions": [
    { "role": "authenticated", "actions": ["execute"] }
  ]
}
```

**You cannot GRANT `read` or `update` to a stored procedure** — only `execute`.

**Rule 4: Request context defaults**

| Request | Role DAB uses |
|---------|---------------|
| No token, no X-MS-API-ROLE | `anonymous` |
| Token present, no X-MS-API-ROLE | `authenticated` |
| Token present, X-MS-API-ROLE: admin | `admin` (if that role exists) |

**Trap**: If request has a token but no header, DAB uses `authenticated`, NOT `anonymous`.

**Example:**
```
GET /data-api/api/TodoItems
Authorization: Bearer <valid_token>
```
→ DAB evaluates as `authenticated` role

vs

```
GET /data-api/api/TodoItems
(no Authorization header)
```
→ DAB evaluates as `anonymous` role

**Rule 5: If role doesn't have permission, request fails**

```json
"Orders": {
  "permissions": [
    { "role": "authenticated", "actions": ["read"] }
  ]
}
```

**Scenario:** 
- Authenticated user tries to READ → ✓ Success (authenticated has read)
- Authenticated user tries to UPDATE → ✗ Denied (authenticated doesn't have update)
- Anonymous user tries to READ → ✗ Denied (anonymous role not even defined)

#### Common Exam Patterns

| Scenario | Permissions Needed | Question Answer |
|----------|-------------------|-----------------|
| "Can anonymous users read Products?" | `"role":"anonymous", "actions":["read"]` | Only if explicitly granted |
| "Can authenticated users update Inventory?" | `"actions":["update"]` | Only if "update" in actions |
| "Can authenticated users execute usp_Finalize?" | `"actions":["execute"]` | Yes (stored proc action) |
| "If read + create, can they also delete?" | `"actions":["read","create","delete"]` | Only if delete explicitly listed |
| "Request with token + X-MS-API-ROLE: ops, but no ops role exists" | Default to `authenticated` | Fail (ops role doesn't exist) |

#### Real Exam Question Breakdown (q046)

Configuration:
```json
"Procedures": {
  "permissions": [
    { "role": "anonymous", "actions": ["read"] }
  ]
},
"Transactions": {
  "permissions": [
    { "role": "authenticated", "actions": ["read", "create"] }
  ]
},
"sp_UpdateProcedurePatient": {
  "source": { "type": "stored-procedure", "object": "dbo.usp_UpdateProcedure" },
  "permissions": [
    { "role": "authenticated", "actions": ["execute"] }
  ]
}
```

**Statement 1:** "Applications can read data in Procedures table without authentication"  
→ YES (anonymous role has read)

**Statement 2:** "Applications can read AND UPDATE data in Transactions table once authenticated"  
→ NO (Transactions has read+create, NOT update)

**Statement 3:** "Applications can execute sp_UpdateProcedurePatient"  
→ YES (authenticated has execute on the stored proc)

**Answer: S1=Yes, S2=No, S3=Yes**

#### Memory Hooks

- **Anonymous = explicit** — must be in permissions, not implicit
- **Actions are separate** — don't assume read=create=update
- **Stored procs = execute** — not read or write
- **Token + no header = authenticated** — not anonymous

**Sentence to remember:**
> "Secure by default. Grant each action explicitly. Stored procs use execute, not CRUD."

---

## ✅ FINAL CHECKLIST

Before exam day:

- [x] Query Store = history, DMVs = now (memory hook works?)
- [x] SERIALIZABLE adds key-range locks (gap locks)
- [x] REPEATABLE READ can have phantoms
- [x] DAB `anonymous` must be explicit
- [x] DAB actions are separate (`read` ≠ `update`)
- [x] DAB stored procs use `execute`
- [x] VECTOR_SEARCH needs indexes for speed
- [x] Change Tracking = Azure Functions, CDC = more detail
- [x] MERGE in post-deploy for idempotency
- [x] Azure.Master for Azure SQL (not on-prem Master)
- [x] Always Encrypted: CEK → table → encrypt (not reverse)
- [x] `/data-api/api/{Entity}` is correct DAB URL
- [x] Firewall 0.0.0.0 = Azure services only
- [x] Model switch requires full re-embedding
- [x] Cosine metric for variable chunk sizes

---

**Good luck. You've got this. 🎯**
