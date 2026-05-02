# Day 6 Session 2: Weak-Area Review + Mock Exam

**Date**: 2026-05-01
**Domain**: Cross-domain reinforcement (DP-800)
**Subtopics**: Query Store views, isolation levels, Data API Builder permissions, mixed-domain timed practice

## Brief Weak-Area Recap

### 1) Query Store views vs DMVs
- Query Store catalog views (`sys.query_store_*`) store persisted history across time windows.
- Execution DMVs (`sys.dm_exec_*`) show current or recent runtime cache state, not long-term persisted performance history.
- Quick split:
  - Need historical plan/runtime comparison over intervals: use `sys.query_store_*`.
  - Need current cache/session/request diagnostics: use `sys.dm_exec_*`.

Memory hook: **"Store = history shelf, DMV = live dashboard."**

### 2) SERIALIZABLE vs REPEATABLE READ
- `REPEATABLE READ`:
  - Prevents dirty reads and non-repeatable reads.
  - Holds shared locks on rows read until transaction end.
  - Still allows phantom rows (new qualifying inserts).
- `SERIALIZABLE`:
  - Includes all protections of `REPEATABLE READ`.
  - Adds key-range locks, blocking inserts into scanned key ranges.
  - Prevents phantom reads.

Memory hook: **"Repeatable locks rows; Serializable locks rows + gaps."**

### 3) DAB permissions (anonymous/read vs create/update/execute)
- DAB is secure-by-default: no permission block means no access.
- Actions are entity-type based:
  - Table/view entities: `create`, `read`, `update`, `delete`
  - Stored procedures: `execute`
- `anonymous` must be explicitly granted for unauthenticated access.
- If request is authenticated and no `X-MS-API-ROLE` is passed, evaluation defaults to `authenticated` role.

Memory hook: **"No permission, no party. Anonymous must be invited."**

## Session 2 Checklist

- [x] Run targeted 21-question set.
- [x] Log incorrect IDs immediately after run.
- [x] Re-read weak topics notes (Query Store, isolation levels, DAB permissions).
- [x] Run timed random 50-question mock (100 minutes).
- [x] Capture weak-spot patterns for weekend review.

## Related Question IDs

### Targeted Session 2 set (remaining 21)
- q017, q018, q019, q020, q021, q022, q069
- q057, q058, q059, q060, q061, q088
- q065, q068, q070
- q079, q080, q081, q082, q083

### Weak-topic reinforcement IDs from prior misses/review
- q084, q085, q086, q087

## Run Order

Run command (a) first, then command (b).

### (a) 21-question run

```powershell
python quiz_runner.py --ids q017,q018,q019,q020,q021,q022,q069,q057,q058,q059,q060,q061,q088,q065,q068,q070,q079,q080,q081,q082,q083 questions.json
```

### (b) Timed random mock exam (50 q, 100 min)

```powershell
python quiz_runner.py questions.json --all --shuffle --limit 50
```

### Mock result (latest run)

- Score: **41/50 (82.0%)**
- Skipped: **1**
- Time: **1179.4s (~19m 39s)**
- Weakest domain in this run: **Domain 2 (17/23, 73.9%)**

## No-Spoiler Rule

Do not reveal answer keys during these runs unless explicitly requested.