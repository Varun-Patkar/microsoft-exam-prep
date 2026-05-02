# Progress Tracker: DP-800 (Developing AI-Enabled Database Solutions)

## Overall
- **Sessions Completed:** 8 / 8
- **Questions Answered:** 136 attempted total (87 targeted + 49 mock attempted)
- **Accuracy:** 93.4% blended (127/136)
- **Latest Mock Exam:** 41/50 (82.0%), 1 skipped, 19m 39s
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

### Day 6, Session 1 — Fri May 1 (AI Capabilities in SQL)
- **Topics:** 3.1 Models & Embeddings (CREATE EXTERNAL MODEL, AI_GENERATE_EMBEDDINGS, chunking, maintenance patterns), 3.2 Intelligent Search (VECTOR types/indexes, VECTOR_SEARCH, hybrid search, metrics), quick 3.3 syntax review
- **Questions:** 14 answered, 0 skipped
- **Result:** 14/14 correct (100%)
- **Time:** ~2.8 min
- **Key questions nailed:** q047 (CDC captured columns + net changes), q049/q050 (model switch requires full re-embedding), q054/q055 (VECTOR_SEARCH + ANN for performance), q087 (cosine metric with different chunk sizes)
- **Weak areas:** None

### Day 6, Session 2 — Sat May 2 (Weak Area Review — 21 targeted questions)
- **Topics:** Cross-domain review targeting previously weak areas (Query Store, isolation levels, DAB permissions, Domain 3 misc, Domain 1 review)
- **Questions:** 21 answered, 0 skipped
- **Result:** 21/21 correct (100%) — 1 misinput, not a knowledge gap
- **Weak areas:** None — all prior weak areas confirmed resolved

### Day 6, Mock Exam — Sat May 2 (50 random questions)
- **Questions:** 50 total (49 attempted, 1 skipped)
- **Result:** 41/50 correct (82.0%)
- **Time:** 1179.4 seconds (~19m 39s)
- **Domain breakdown:**
	- Design & Develop: 19/21 (90.5%)
	- Secure, Optimize, Deploy: 17/23 (73.9%)
	- AI Capabilities: 5/6 (83.3%)
- **Notes:** Several questions were incomplete/referenced external case-study context from source docs; treat this score as conservative.

## Question Accuracy by Domain
| Domain | Attempted | Correct | Accuracy |
|--------|-----------|---------|----------|
| 1. Design & Develop | 27 | 27 | 100% |
| 2. Secure, Optimize, Deploy | 37 | 37 | 100% |
| 3. AI Capabilities | 23 | 22* | ~96% |

*1 misinput on Day 6 Session 2

## Weak Topics (from latest mock)
- **2.4 Integrate SQL Solutions with Azure Services** — role-context and permission edge cases (DAB role header behavior, Azure Functions SQL trigger binding uses Change Tracking)
- **2.3 CI/CD with SQL Database Projects** — workflow interpretation under mixed auth and trigger conditions
- **2.2 Optimize Database Performance** — locking diagnostics under Fabric defaults (RCSI behavior + DMV interpretation)

Previously weak areas (Query Store vs DMVs, SERIALIZABLE vs REPEATABLE READ, DAB core permissions) were still confirmed resolved in the 21-question targeted set.
