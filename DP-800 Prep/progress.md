# Progress Tracker: DP-800 (Developing AI-Enabled Database Solutions)

## Overall
- **Sessions Completed:** 6 / 8
- **Questions Answered:** 52 / 88
- **Accuracy:** 94.2% (49/52)
- **MS Learn Course:** Completed

## Daily Log

### Day 1, Session 1 — Sun Apr 26 (Database Objects + Programmability)
- **Topics:** 1.1 Database Objects, 1.2 Programmability
- **Questions:** 8 answered, 2 skipped (Domain 3 — not yet studied)
- **Result:** 8/8 correct (100%)
- **Time:** ~13 min
- **Skipped:** q056, q057 (Domain 3 material not yet covered)
- **Weak areas:** None

### Day 1, Session 2 — Sun Apr 26 (Advanced T-SQL)
- **Topics:** 1.3 Advanced T-SQL (CTEs, window functions, JSON, regex, fuzzy matching, graph, error handling)
- **Questions:** 11 answered, 0 skipped
- **Result:** 11/11 correct (100%)
- **Time:** ~1.3 min
- **Weak areas:** None

### Day 2, Session 1 — Sun Apr 27 (Data Security & Compliance)
- **Topics:** 2.1 Data Security & Compliance (Always Encrypted, DDM, RLS, Object Permissions, Managed Identity, Auditing)
- **Questions:** 9 answered, 0 skipped
- **Result:** 9/9 correct (100%)
- **Time:** ~8 min
- **Key questions nailed:** q028 (Ledger + AE ordering), q077 (DDM + RLS interaction), q029 (user-assigned MI for migration)
- **Weak areas:** None

### Day 3, Session 1 — Tue Apr 28 (Performance Optimization)
- **Topics:** 2.2 Optimize Database Performance (isolation levels, execution plans, DMVs, Query Store, blocking & deadlocks)
- **Questions:** 8 answered, 0 skipped
- **Result:** 6/8 correct (75%)
- **Time:** ~10 min
- **Wrong:** q030 (Query Store CPU query — picked `sys.dm_exec_query_stats` instead of `sys.query_store_runtime_stats_interval`), q034 (isolation level — picked REPEATABLE READ instead of SERIALIZABLE)
- **Key lesson:** "Query Store data" → all joins use `sys.query_store_*` views, not `sys.dm_exec_*` DMVs. SERIALIZABLE = prevents both modifications AND inserts (phantom protection).
- **Weak areas:** Query Store catalog views, SERIALIZABLE vs REPEATABLE READ distinction

### Day 4, Session 1 — Wed Apr 29 (CI/CD with SQL Database Projects)
- **Topics:** 2.3 CI/CD — SQL Database Projects (SDK-style, dacpac, sqlpackage, source control, schema drift, pipelines)
- **Questions:** 8 answered, 0 skipped
- **Result:** 8/8 correct (100%)
- **Time:** ~1 session
- **Key questions nailed:** q035 (GitHub Actions auth vs Release config), q036 (MERGE for idempotent reference data), q039/q040 (Azure.Master vs on-prem Master NuGet package distinction)
- **Weak areas:** None

### Day 5, Session 1 — Thu Apr 30 (Azure Service Integration)
- **Topics:** 2.4 — DAB (config, entities, REST/GraphQL, roles, deployment), Azure Monitor, Change Tracking vs CDC vs CES, Azure Functions SQL trigger binding
- **Questions:** 8 answered, 0 skipped
- **Result:** 7/8 correct (87.5%)
- **Time:** ~1 min
- **Wrong:** q046 (DAB Fabrikam case study — Procedures table anonymous read = Yes, Transactions table read+update = No, SP execute = Yes; answered S1=No, S2=Yes, S3=No)
- **Key lesson:** Anonymous role in DAB entity permissions = no auth required → anonymous read IS allowed. `read`+`create` ≠ `update` — must be explicitly listed. SP with `execute` for authenticated = Yes.
- **Weak areas:** DAB entity permission evaluation (anonymous role, read vs update distinction)

## Question Accuracy by Domain
| Domain | Attempted | Correct | Accuracy |
|--------|-----------|---------|----------|
| 1. Design & Develop | 20 | 20 | 100% |
| 2. Secure, Optimize, Deploy | 32 | 29 | 90.6% |
| 3. AI Capabilities | 0 | 0 | — |

## Weak Topics (to revisit)
- **2.2 Query Store catalog views** — know the difference between `sys.query_store_*` views and `sys.dm_exec_*` DMVs
- **2.2 Isolation levels** — SERIALIZABLE prevents phantom inserts (key-range locks), REPEATABLE READ only prevents modification of already-read rows
- **2.4 DAB entity permissions** — `anonymous` role = no auth required (read IS allowed); `read`+`create` ≠ `update`; SP needs `execute` not `read`
