# Study Plan: Developing AI-Enabled Database Solutions (DP-800)

## Summary
- **Start Date:** 2026-04-26 (Sunday)
- **Exam Date:** 2026-05-04 (Monday)
- **Total Study Days:** 6 active + 2 revision
- **Daily Commitment:** 4 hrs Sunday & Friday (2 × 2hr sessions) | 1 hr Mon–Thu
- **Total Study Hours:** 12 hrs active + weekend revision
- **Strategy:** Heavy focus on SQL-specific skills (Domains 1 & 2 = 70–80% of exam). Light review on strengths (MCP, Copilot, RAG). SQL-specific AI features (vector search, embeddings in T-SQL) need moderate attention.

## Proficiency Profile
- **Confident (light review):** 1.4 AI-Assisted Tools, 3.3 RAG
- **Rusty (focused refresh):** 1.1 Database Objects, 1.2 Programmability, 1.3 Advanced T-SQL
- **Weak (full study):** 2.1 Security, 2.2 Performance, 2.3 CI/CD, 2.4 Azure Integration, 3.1 Embeddings (SQL-specific), 3.2 Intelligent Search (SQL-specific)

---

## Daily Schedule

### Day 1 — Sunday, Apr 26 (4 hrs) — Domain 1: Core SQL Refresh

**Session 1 (2 hrs): Database Objects + Programmability**
- [ ] Study: 1.1 — Tables, data types, indexes, columnstore indexes
- [ ] Study: 1.1 — Specialized tables: in-memory, temporal, external, ledger, graph
- [ ] Study: 1.1 — JSON columns/indexes, constraints (PK, FK, UNIQUE, CHECK, DEFAULT), SEQUENCES, partitioning
- [ ] Study: 1.2 — Views (standard + indexed), scalar functions (inline vs traditional), table-valued functions
- [ ] Study: 1.2 — Stored procedures (TVPs, error handling), triggers (AFTER vs INSTEAD OF, DML vs DDL)
- [ ] Practice: 10 questions (q001–q005 from 1.1, q006–q008 from 1.2, q056–q057 bonus)
- Estimated time: 2 hrs

**Session 2 (2 hrs): Advanced T-SQL**
- [ ] Study: 1.3 — CTEs (recursive + non-recursive), window functions (ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, SUM OVER)
- [ ] Study: 1.3 — JSON functions: JSON_OBJECT, JSON_ARRAY, JSON_ARRAYAGG, JSON_CONTAINS, OPENJSON, JSON_VALUE
- [ ] Study: 1.3 — Regular expressions: REGEXP_LIKE, REGEXP_REPLACE, REGEXP_SUBSTR, REGEXP_INSTR, REGEXP_COUNT
- [ ] Study: 1.3 — Fuzzy matching: EDIT_DISTANCE, EDIT_DISTANCE_SIMILARITY, JARO_WINKLER_DISTANCE
- [ ] Study: 1.3 — Graph queries with MATCH, correlated subqueries, error handling (TRY/CATCH, THROW, XACT_STATE)
- [ ] Practice: 10 questions (q009–q014, q060–q064, q066–q067)
- Estimated time: 2 hrs

---

### Day 2 — Monday, Apr 27 (1 hr) — 2.1 Data Security & Compliance

- [ ] Study: Always Encrypted (standard vs with enclaves, deterministic vs randomized)
- [ ] Study: Dynamic Data Masking (default, partial, email, random masking functions)
- [ ] Study: Row-Level Security (filter predicates + block predicates)
- [ ] Study: Object-level permissions (schema-level grants), passwordless access (Managed Identity)
- [ ] Study: Auditing (Azure SQL Auditing → Log Analytics), securing model/GraphQL/REST/MCP endpoints
- [ ] Practice: 8 questions (q019–q023, q071–q075)
- Estimated time: 1 hr

---

### Day 3 — Tuesday, Apr 28 (1 hr) — 2.2 Performance Optimization

- [ ] Study: Transaction isolation levels (READ UNCOMMITTED → SERIALIZABLE, SNAPSHOT, RCSI)
- [ ] Study: Execution plans (scans vs seeks, estimated vs actual rows, key lookups)
- [ ] Study: DMVs (sys.dm_exec_query_stats, sys.dm_exec_requests, sys.dm_tran_locks)
- [ ] Study: Query Store (plan regression detection, forced plans) + Query Performance Insight
- [ ] Study: Blocking & deadlocks (identification, head blocker, consistent access ordering, tempdb contention)
- [ ] Practice: 8 questions (q024–q027, q076–q080)
- Estimated time: 1 hr

---

### Day 4 — Wednesday, Apr 29 (1 hr) — 2.3 CI/CD with SQL Database Projects

- [ ] Study: SQL Database Projects (SDK-style, .sqlproj, dacpac, dotnet build, sqlpackage)
- [ ] Study: Testing strategy (tSQLt unit tests, integration tests with ephemeral DBs)
- [ ] Study: Source control (branching, PRs, merge conflicts, CODEOWNERS, reference data via post-deploy MERGE scripts)
- [ ] Study: Schema drift detection, secrets management (Key Vault, GitHub Secrets)
- [ ] Study: Deployment pipelines (multi-stage, approval gates, triggers, environment-specific controls)
- [ ] Practice: 8 questions (q028–q031, q036, q081–q085)
- Estimated time: 1 hr

---

### Day 5 — Thursday, Apr 30 (1 hr) — 2.4 Azure Service Integration

- [ ] Study: Data API Builder (DAB) — config files (dab-config.json), entities, REST + GraphQL endpoints
- [ ] Study: DAB — exposing tables/views/stored procedures, GraphQL relationships, pagination, caching
- [ ] Study: DAB deployment (Azure Container Apps), Azure Monitor + Application Insights + Log Analytics
- [ ] Study: Change handling — CDC vs Change Tracking vs CES, Azure Functions SQL trigger binding, Logic Apps
- [ ] Practice: 8 questions (q032–q035, q086–q090)
- Estimated time: 1 hr

---

### Day 6 — Friday, May 1 (4 hrs) — Domain 3 AI + Full Review

**Session 1 (2 hrs): AI Capabilities in SQL (3.1 + 3.2 + quick 3.3 review)**
- [ ] Study: 3.1 — CREATE EXTERNAL MODEL, evaluating models (multimodal, multilanguage, sizes)
- [ ] Study: 3.1 — Embedding maintenance in SQL (Change Tracking, Azure Functions, CDC, triggers), column selection, chunk design
- [ ] Study: 3.2 — Full-text search (CONTAINS, FREETEXT, FORMSOF) — refresh
- [ ] Study: 3.2 — VECTOR data type, vector indexes (DiskANN), VECTOR_NORMALIZE, VECTOR_DISTANCE, VECTORPROPERTY, VECTOR_SEARCH
- [ ] Study: 3.2 — ANN vs ENN, vector index metrics (cosine, dot product, euclidean), hybrid search, RRF
- [ ] Review: 3.3 — Quick skim of sp_invoke_external_rest_endpoint for RAG, FOR JSON PATH, JSON_VALUE on LLM responses (you know RAG well — just learn the SQL-specific syntax)
- [ ] Review: 1.4 — Quick skim of GitHub Copilot instruction files + MCP config (you know this — just review exam-specific framing)
- [ ] Practice: 14 questions (q037–q050 Domain 3 originals)
- Estimated time: 2 hrs

**Session 2 (2 hrs): Weak Area Review + Mock Exam**
- [ ] Review: Go through ALL questions you got wrong during the week
- [ ] Review: Re-read notes on your weakest topics
- [ ] Mock Exam: Run quiz_runner.py in mock exam mode (timed, random, all domains)
- [ ] Analyze: Review mock exam results, identify final weak spots for weekend
- Estimated time: 2 hrs

---

### Day 7 — Saturday, May 2 (Revision)

- [ ] Review: Re-study topics where mock exam accuracy was below 70%
- [ ] Practice: Run quiz_runner.py filtered to weak domains only
- [ ] Review: Skim all topic summaries in topics.md
- [ ] Create: Personal cheat sheet of key facts (functions, syntax, concepts you keep forgetting)

---

### Day 8 — Sunday, May 3 (Revision)

- [ ] Final Mock: Run quiz_runner.py full mock exam (timed, 50 random questions, 100 min)
- [ ] Review: Focus only on missed questions — read explanations carefully
- [ ] Relax: Light review of cheat sheet, then rest. No cramming the night before.
- [ ] Prep: Confirm exam logistics (time, location/link, ID requirements)

---

### Day 9 — Monday, May 4 — EXAM DAY 🎯

- Quick glance at cheat sheet in the morning
- Remember: MS Learn is accessible during the exam for reference
- Focus on concept understanding and elimination of wrong answers
- Manage time: ~2 min per question, flag and revisit uncertain ones

---

## Question Practice Schedule

| Day | Questions | Count |
|-----|-----------|-------|
| Sun (D1) | q001–q008, q051–q067 (Domain 1) | ~20 |
| Mon (D2) | q019–q023, q071–q075 (Security) | ~10 |
| Tue (D3) | q024–q027, q076–q080 (Performance) | ~9 |
| Wed (D4) | q028–q031, q036, q081–q085 (CI/CD) | ~10 |
| Thu (D5) | q032–q035, q086–q090 (Azure Integration) | ~9 |
| Fri (D6) | q037–q050, q091–q104 (Domain 3) + mock exam | ~28 + mock |
| Sat–Sun | Weak area drills + full mock exam | varies |

## Key Exam Tips
- **MS Learn is accessible during the exam** — don't memorize docs, understand concepts
- **Elimination strategy** — usually 2 answers are clearly wrong, narrow to 2 and reason through
- **Time management** — 100 minutes, ~40–60 questions. Don't spend >3 min on any question
- **Flag and return** — mark uncertain questions and revisit after completing all others
- **Read carefully** — Microsoft loves "which should you do FIRST" and "what is the PRIMARY concern" — these have specific best answers
