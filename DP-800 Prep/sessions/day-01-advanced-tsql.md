# Day 1, Session 2: Advanced T-SQL (1.3)
**Date**: 2026-04-26
**Domain**: Design and Develop Database Solutions (40-45%)
**Subtopics**: CTEs, Window Functions, JSON Functions, Regular Expressions, Fuzzy Matching, Graph Queries, Correlated Subqueries, Error Handling

---

## 1. Common Table Expressions (CTEs)

### Non-Recursive CTE
- Named subquery defined with `WITH ... AS (SELECT ...)`
- Improves readability, allows multiple references in same query
- Exists only for duration of single statement
- Can define multiple CTEs: `WITH cte1 AS (...), cte2 AS (...)`

```sql
WITH TopCustomers AS (
    SELECT CustomerId, SUM(Amount) AS Total
    FROM Orders
    GROUP BY CustomerId
    HAVING SUM(Amount) > 10000
)
SELECT c.Name, tc.Total
FROM Customers c
JOIN TopCustomers tc ON c.Id = tc.CustomerId;
```

### Recursive CTE
- Two parts: **anchor member** + **recursive member** joined by `UNION ALL`
- Anchor = base case (no self-reference)
- Recursive = references CTE itself
- Terminates when recursive member returns empty set
- Default MAXRECURSION = 100 (set with OPTION)

```sql
-- Org chart: find all subordinates of ManagerId = 1
WITH OrgTree AS (
    -- Anchor: start with the manager
    SELECT EmployeeId, Name, ManagerId, 0 AS Level
    FROM Employees
    WHERE EmployeeId = 1

    UNION ALL

    -- Recursive: find direct reports
    SELECT e.EmployeeId, e.Name, e.ManagerId, ot.Level + 1
    FROM Employees e
    JOIN OrgTree ot ON e.ManagerId = ot.EmployeeId
)
SELECT * FROM OrgTree
OPTION (MAXRECURSION 50);
```

### Exam Patterns
- "Traverse hierarchy" or "find all subordinates" → **recursive CTE**
- "BOM explosion" (Bill of Materials) → recursive CTE
- MAXRECURSION 0 = unlimited (dangerous, possible infinite loop)

---

## 2. Window Functions

### Ranking Functions

| Function | Ties | Gaps | Example (scores: 90,90,80,70) |
|----------|------|------|-------------------------------|
| ROW_NUMBER() | Always unique | N/A | 1, 2, 3, 4 |
| RANK() | Same rank for ties | Yes, gaps after ties | 1, 1, 3, 4 |
| DENSE_RANK() | Same rank for ties | No gaps | 1, 1, 2, 3 |

```sql
SELECT Name, Score,
    ROW_NUMBER() OVER (ORDER BY Score DESC) AS RowNum,
    RANK()       OVER (ORDER BY Score DESC) AS Rnk,
    DENSE_RANK() OVER (ORDER BY Score DESC) AS DenseRnk
FROM Students;
```

**EXAM TIP**: When question says "exactly one row per group" → ROW_NUMBER (always unique). When "handle ties without gaps" → DENSE_RANK.

### Offset Functions: LAG / LEAD

```sql
-- LAG: previous row value; LEAD: next row value
SELECT OrderDate, Amount,
    LAG(Amount, 1, 0)  OVER (ORDER BY OrderDate) AS PrevAmount,
    LEAD(Amount, 1, 0) OVER (ORDER BY OrderDate) AS NextAmount
FROM Orders;
```
- LAG(col, offset, default) — offset=1 by default, default=NULL by default
- LEAD same signature but looks forward

### Aggregate Window Functions

```sql
-- Running total
SELECT OrderDate, Amount,
    SUM(Amount) OVER (ORDER BY OrderDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS RunningTotal
FROM Orders;

-- Moving average (3-day)
SELECT OrderDate, Amount,
    AVG(Amount) OVER (ORDER BY OrderDate
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS MovingAvg3
FROM Orders;
```

### PARTITION BY vs ORDER BY
- **PARTITION BY**: resets window per group (like GROUP BY within window)
- **ORDER BY**: defines row ordering within partition
- Both can be used together: `OVER (PARTITION BY CustId ORDER BY OrderDate)`

### Frame Specifications
- `ROWS BETWEEN`: physical rows
- `RANGE BETWEEN`: logical range (based on value)
- Default when ORDER BY present: `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`
- **EXAM TRAP**: Default frame with `SUM() OVER (ORDER BY ...)` is RANGE not ROWS — can give unexpected results with ties

---

## 3. JSON Functions

### Building JSON

| Function | Purpose | Example |
|----------|---------|---------|
| `JSON_OBJECT()` | Build JSON object from key:value pairs | `JSON_OBJECT('name':'John', 'age':30)` → `{"name":"John","age":30}` |
| `JSON_ARRAY()` | Build JSON array | `JSON_ARRAY(1, 2, 'a')` → `[1,2,"a"]` |
| `JSON_ARRAYAGG()` | Aggregate rows into JSON array | `SELECT JSON_ARRAYAGG(Name ORDER BY Name) FROM ...` |

- `JSON_OBJECT` supports `NULL ON NULL` (default) and `ABSENT ON NULL`
- `JSON_ARRAYAGG` supports ORDER BY clause and `ABSENT ON NULL`
- `JSON_ARRAYAGG` is SQL Server 2025 — like STRING_AGG but for JSON

### Querying JSON

| Function | Purpose | Returns |
|----------|---------|---------|
| `JSON_VALUE(json, path)` | Extract **scalar** value | nvarchar(4000) |
| `JSON_QUERY(json, path)` | Extract **object or array** | nvarchar(max) |
| `OPENJSON(json)` | Shred JSON into rows (TVF) | Table (key, value, type) |
| `ISJSON(string)` | Check if valid JSON | 1 or 0 |

```sql
-- Extract scalar
SELECT JSON_VALUE('{"name":"John","age":30}', '$.name'); -- 'John'

-- Extract object/array
SELECT JSON_QUERY('{"addr":{"city":"NYC"}}', '$.addr'); -- {"city":"NYC"}

-- OPENJSON with explicit schema (CROSS APPLY pattern)
SELECT o.OrderId, j.ProductName, j.Qty
FROM Orders o
CROSS APPLY OPENJSON(o.LineItems)
    WITH (
        ProductName nvarchar(100) '$.product',
        Qty int '$.quantity'
    ) j;
```

### Converting to JSON

```sql
-- FOR JSON PATH: full control over structure
SELECT OrderId, CustomerName
FROM Orders
FOR JSON PATH;
-- [{"OrderId":1,"CustomerName":"John"}, ...]

-- FOR JSON AUTO: auto-nests based on table structure
SELECT o.OrderId, l.Product
FROM Orders o JOIN Lines l ON o.Id = l.OrderId
FOR JSON AUTO;
```

**EXAM TRAP**: `JSON_VALUE` = scalar. `JSON_QUERY` = object/array. Mixing them up returns NULL.

---

## 4. Regular Expressions (NEW — SQL Server 2025)

Requires **compatibility level 170** (except REGEXP_LIKE which needs 170, others work at all levels).

| Function | Purpose | Returns |
|----------|---------|---------|
| `REGEXP_LIKE(str, pattern, flags)` | Boolean match | bit (true/false) |
| `REGEXP_COUNT(str, pattern, start, flags)` | Count matches | int |
| `REGEXP_INSTR(str, pattern, start, occurrence, option, flags)` | Position of match | int |
| `REGEXP_REPLACE(str, pattern, replacement, start, occurrence, flags)` | Replace matches | string |
| `REGEXP_SUBSTR(str, pattern, start, occurrence, flags)` | Extract matching substring | string |

### Flags
| Flag | Meaning |
|------|---------|
| `c` | Case-sensitive (default) |
| `i` | Case-insensitive |
| `m` | Multi-line (^ and $ match line boundaries) |
| `s` | Dot matches newline |

```sql
-- Validate email format
SELECT * FROM Users
WHERE REGEXP_LIKE(Email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Strip non-digits from phone
SELECT REGEXP_REPLACE(Phone, '[^\d]', '') AS DigitsOnly FROM Customers;

-- Count vowels
SELECT REGEXP_COUNT(Name, '[aeiou]', 1, 'i') FROM Products;

-- CHECK constraint with regex
CREATE TABLE Emp (
    Email VARCHAR(320) CHECK (REGEXP_LIKE(Email, '^[A-Za-z0-9._%+-]+@.*$'))
);
```

### Backreferences in REGEXP_REPLACE
- `\1` through `\9` reference capture groups
- `&` references entire match
```sql
-- Reformat phone: 123-456-7890 → (123) 456-7890
SELECT REGEXP_REPLACE('123-456-7890', '(\d{3})-(\d{3})-(\d{4})', '(\1) \2-\3');
```

**EXAM TIP**: Regex functions are NEW in SQL Server 2025 — expect heavy testing. Know which returns boolean (REGEXP_LIKE) vs string (REGEXP_REPLACE/SUBSTR) vs int (REGEXP_COUNT/INSTR).

---

## 5. Fuzzy String Matching (NEW — SQL Server 2025, Preview)

| Function | Returns | Range | Algorithm |
|----------|---------|-------|-----------|
| `EDIT_DISTANCE(s1, s2)` | int (number of edits) | 0 to max(len) | Damerau-Levenshtein |
| `EDIT_DISTANCE_SIMILARITY(s1, s2)` | int (% similar) | 0–100 | Damerau-Levenshtein |
| `JARO_WINKLER_DISTANCE(s1, s2)` | float (distance) | 0.0–1.0 | Jaro-Winkler |
| `JARO_WINKLER_SIMILARITY(s1, s2)` | float (similarity) | 0.0–1.0 | Jaro-Winkler |

```sql
-- Find similar customer names (deduplication)
SELECT a.Name, b.Name,
    EDIT_DISTANCE(a.Name, b.Name) AS EditDist,
    EDIT_DISTANCE_SIMILARITY(a.Name, b.Name) AS Pct
FROM Customers a, Customers b
WHERE a.Id < b.Id
    AND EDIT_DISTANCE_SIMILARITY(a.Name, b.Name) > 80;

-- Jaro-Winkler favors prefix matches
SELECT JARO_WINKLER_DISTANCE('Colour', 'Color');  -- 0.0333 (very close)
SELECT JARO_WINKLER_DISTANCE('abc', 'xyz');        -- ~1.0 (very different)
```

### Key Distinctions
- EDIT_DISTANCE = raw count of edits needed → lower = more similar
- EDIT_DISTANCE_SIMILARITY = percentage → higher = more similar (formula: `(1 - dist/max_len) * 100`)
- JARO_WINKLER_DISTANCE → lower = more similar (0 = identical)
- JARO_WINKLER gives bonus for matching **prefixes** → good for names
- Neither supports varchar(max) or nvarchar(max)

**EXAM PATTERN**: "Find similar customer names", "deduplicate records" → fuzzy matching functions

---

## 6. Graph Queries with MATCH

### Setup
```sql
-- NODE tables
CREATE TABLE Person (PersonId INT, Name NVARCHAR(100)) AS NODE;
CREATE TABLE Restaurant (Name NVARCHAR(100)) AS NODE;

-- EDGE tables
CREATE TABLE Knows (Since DATE) AS EDGE;
CREATE TABLE Likes (Rating INT) AS EDGE;
```

### Basic MATCH
```sql
-- Single hop: who does Alice know?
SELECT p2.Name
FROM Person p1, Knows k, Person p2
WHERE MATCH(p1-(k)->p2)
AND p1.Name = 'Alice';
```

### Chained MATCH (multi-hop)
```sql
-- Two hops: friends of friends
SELECT p3.PersonId, p3.Name
FROM Person p1, Knows k1, Person p2, Knows k2, Person p3
WHERE p1.PersonId = @StartId
AND MATCH(p1-(k1)->p2-(k2)->p3);
```

### SHORTEST_PATH
```sql
-- Find shortest path from Jacob to all connected people
SELECT Person1.Name,
    STRING_AGG(Person2.Name, '->') WITHIN GROUP (GRAPH PATH) AS Path
FROM Person AS Person1,
    Knows FOR PATH AS k,
    Person FOR PATH AS Person2
WHERE MATCH(SHORTEST_PATH(Person1(-(k)->Person2)+))
AND Person1.Name = 'Jacob';
```

- `FOR PATH` = marks tables participating in arbitrary-length pattern
- `+` = one or more hops
- `{1,3}` = one to three hops
- `WITHIN GROUP (GRAPH PATH)` = required for aggregates in SHORTEST_PATH
- `LAST_NODE()` = get terminal node for chaining

**EXAM TIP**: MATCH uses comma-separated FROM (no explicit JOINs). Arrow direction matters: `(node-(edge)->node)`.

---

## 7. Correlated Subqueries

Subquery references columns from outer query. Executes once per outer row.

```sql
-- Employees earning more than department average
SELECT e.Name, e.Salary
FROM Employees e
WHERE e.Salary > (
    SELECT AVG(e2.Salary)
    FROM Employees e2
    WHERE e2.DeptId = e.DeptId  -- correlation
);

-- EXISTS pattern (common exam pattern)
SELECT c.Name
FROM Customers c
WHERE EXISTS (
    SELECT 1 FROM Orders o
    WHERE o.CustomerId = c.Id
    AND o.OrderDate > '2025-01-01'
);

-- NOT EXISTS (find customers with NO orders)
SELECT c.Name
FROM Customers c
WHERE NOT EXISTS (
    SELECT 1 FROM Orders o WHERE o.CustomerId = c.Id
);
```

### Performance Notes
- Correlated subquery runs once per outer row (can be slow)
- Optimizer often rewrites to JOIN internally
- EXISTS/NOT EXISTS preferred over IN/NOT IN for NULLable columns (NOT IN with NULLs returns empty)

**EXAM TRAP**: `NOT IN` with NULL values in subquery returns no rows. `NOT EXISTS` handles NULLs correctly.

---

## 8. Error Handling

### TRY...CATCH
```sql
BEGIN TRY
    BEGIN TRANSACTION;
    -- do work
    INSERT INTO Orders (...) VALUES (...);
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    -- Log error
    INSERT INTO ErrorLog (Msg, Num, Line, Proc, Severity, State)
    VALUES (
        ERROR_MESSAGE(),
        ERROR_NUMBER(),
        ERROR_LINE(),
        ERROR_PROCEDURE(),
        ERROR_SEVERITY(),
        ERROR_STATE()
    );

    THROW;  -- re-raise
END CATCH;
```

### ERROR Functions (available only in CATCH block)
| Function | Returns |
|----------|---------|
| `ERROR_MESSAGE()` | Error message text |
| `ERROR_NUMBER()` | Error number |
| `ERROR_LINE()` | Line number where error occurred |
| `ERROR_PROCEDURE()` | Name of SP/trigger where error occurred |
| `ERROR_SEVERITY()` | Severity level |
| `ERROR_STATE()` | Error state number |

### THROW vs RAISERROR

| Feature | THROW | RAISERROR |
|---------|-------|-----------|
| Introduced | SQL 2012 | Legacy |
| Severity | Always 16 | Configurable |
| Re-raise original | Yes (no params in CATCH) | No |
| Terminates batch | Yes | Only if severity ≥ 20 |
| Preferred | **Yes** | Legacy only |

```sql
-- THROW with custom message
THROW 50001, 'Custom error message', 1;

-- THROW to re-raise in CATCH (no parameters)
BEGIN CATCH
    THROW;
END CATCH;

-- RAISERROR (legacy)
RAISERROR('Error: %s', 16, 1, @msg);
```

### XACT_STATE() — Classic Exam Pattern

| Value | Meaning | Action |
|-------|---------|--------|
| 1 | Active committable transaction | Can COMMIT or ROLLBACK |
| 0 | No active transaction | Nothing to do |
| -1 | Uncommittable transaction (doomed) | Must ROLLBACK |

```sql
BEGIN CATCH
    IF XACT_STATE() = -1
        ROLLBACK TRANSACTION;  -- doomed, must rollback
    ELSE IF XACT_STATE() = 1
        COMMIT TRANSACTION;    -- can still commit partial work

    THROW;
END CATCH;
```

**EXAM PATTERN**: TRY → work → CATCH → check XACT_STATE() → ROLLBACK if -1. Questions test whether you check XACT_STATE() before ROLLBACK.

---

## Common Traps & Misconceptions

1. **ROW_NUMBER vs RANK vs DENSE_RANK**: Most tested window function distinction. Know the tie-handling behavior.
2. **JSON_VALUE vs JSON_QUERY**: VALUE = scalar, QUERY = object/array. Wrong one returns NULL, not error.
3. **REGEXP_LIKE needs compat level 170**: Other regex functions work at all levels.
4. **NOT IN with NULLs**: Returns empty result set. Use NOT EXISTS instead.
5. **Default window frame**: `SUM() OVER (ORDER BY x)` uses RANGE not ROWS — groups ties together.
6. **THROW without params**: In CATCH block, re-raises original error. With params, throws new error.
7. **XACT_STATE() = -1**: Transaction is doomed, MUST rollback. Cannot commit.
8. **EDIT_DISTANCE vs EDIT_DISTANCE_SIMILARITY**: One returns raw edits (lower=better), other returns percentage (higher=better).
9. **JARO_WINKLER_DISTANCE vs JARO_WINKLER_SIMILARITY**: Distance low=similar, Similarity high=similar.
10. **Graph MATCH**: Uses comma-separated FROM, NOT JOIN syntax.

---

## Related Questions
q013, q014, q015, q066 (direct 1.3 topics)
q009, q010, q011, q012, q062, q063, q064, q067 (cross-topic from 1.1/1.2)
