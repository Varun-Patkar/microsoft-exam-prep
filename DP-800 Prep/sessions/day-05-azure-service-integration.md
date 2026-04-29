# Day 5: Integrate SQL Solutions with Azure Services (2.4)

**Date**: 2026-04-30
**Domain**: 2 — Secure, Optimize, and Deploy Database Solutions (35–40%)
**Subtopics**: Data API Builder (DAB), REST & GraphQL endpoints, DAB deployment on Azure Container Apps, Azure Monitor + App Insights, Change Tracking vs CDC vs CES, Azure Functions SQL trigger binding, Logic Apps, embedding maintenance

---

## 1. Data API Builder (DAB)

### What Is DAB?

- **Open-source engine** that sits in front of Azure SQL (or Fabric SQL, Cosmos DB, MySQL, PostgreSQL) and auto-generates REST + GraphQL APIs from your database schema
- Zero custom code needed — all configuration is in a single JSON file: `dab-config.json`
- Deployable as a container → runs on Azure Container Apps (ACA), Azure App Service, or locally via `dotnet tool`

### URL Patterns (Exam Favorite!)

| Endpoint type | Pattern |
|--------------|---------|
| **REST** | `https://<host>/data-api/api/{EntityName}` |
| **GraphQL** | `https://<host>/data-api/graphql` |
| **Health check** | `https://<host>/data-api/health` |

- **Trap**: `/api/{EntityName}` without the `/data-api` prefix is wrong. The `/data-api` segment is always required.
- GraphQL is a single endpoint — you send queries in the POST body, not via `/graphql/{EntityName}`

### Installing and Initialising DAB

```bash
# Install DAB CLI as a global .NET tool
dotnet tool install --global microsoft.dataapibuilder

# Initialise a config file targeting Azure SQL Database
dab init --database-type mssql --connection-string "Server=...;Database=...;..."

# Add an entity (maps table dbo.todos → REST/GraphQL entity named Todo)
dab add Todo --source dbo.todos --permissions "anonymous:read"

# Start DAB locally
dab start
```

### dab-config.json Structure

```json
{
  "$schema": "https://...",
  "data-source": {
    "database-type": "mssql",
    "connection-string": "@env('DATABASE_CONNECTION_STRING')"
  },
  "runtime": {
    "rest": { "enabled": true, "path": "/api" },
    "graphql": { "enabled": true, "path": "/graphql" },
    "host": { "mode": "production", "authentication": { "provider": "StaticWebApps" } }
  },
  "entities": {
    "Todo": {
      "source": "dbo.todos",
      "permissions": [
        { "role": "anonymous", "actions": ["read"] },
        { "role": "authenticated", "actions": ["create", "read", "update", "delete"] }
      ]
    }
  }
}
```

- **Connection strings in config must reference environment variables** — never hardcoded in production
- `@env('VAR_NAME')` syntax tells DAB to read from the container's environment at runtime

---

## 2. DAB Entities — REST, GraphQL, Stored Procedures

### Entity Permissions

| Field | Values | Notes |
|-------|--------|-------|
| `role` | `anonymous`, `authenticated`, or custom role name | `anonymous` = no token required |
| `actions` | `read`, `create`, `update`, `delete`, `execute` | `execute` is for stored procedures |

- **Trap**: If a table entity has `["read", "create"]` as actions — that is **not** the same as `update`. Exam questions check this precisely.
- A stored procedure entity uses `"execute"` as the action, not `"read"` or `"update"`

### Exposing Views and Stored Procedures

```json
"entities": {
  "ActiveProducts": {
    "source": { "type": "view", "object": "dbo.vw_ActiveProducts", "key-fields": ["ProductId"] },
    "permissions": [{ "role": "authenticated", "actions": ["read"] }]
  },
  "UpdateInventory": {
    "source": { "type": "stored-procedure", "object": "dbo.usp_UpdateInventory" },
    "permissions": [{ "role": "authenticated", "actions": ["execute"] }]
  }
}
```

- Views require `key-fields` (no natural PK) — DAB needs a unique field to construct REST responses
- Stored procedures exposed as REST endpoint: `POST /data-api/api/UpdateInventory`

### GraphQL Relationships

```json
"Book": {
  "source": "dbo.Books",
  "relationships": {
    "Author": {
      "target.entity": "Author",
      "source.fields": ["AuthorId"],
      "target.fields": ["Id"]
    }
  },
  "permissions": [{ "role": "anonymous", "actions": ["read"] }]
}
```

- Relationships let a GraphQL query navigate joins: `{ Book { title Author { name } } }`

### Pagination, Filtering, and Caching

| Feature | REST | GraphQL |
|---------|------|---------|
| **Filtering** | `?$filter=name eq 'Alice'` (OData syntax) | `filter:` argument |
| **Pagination** | `?$first=10&$after=<cursor>` | `first:` / `after:` arguments |
| **Sorting** | `?$orderby=name asc` | `orderBy:` argument |
| **Caching** | Set `cache.enabled: true` + `ttl-seconds` in entity config | Same config |

---

## 3. DAB Roles and Authentication (Exam Trap Zone)

### Role Resolution

DAB uses a two-layer auth model:

1. **Token** — client presents a Microsoft Entra JWT
2. **Role claim** — DAB checks the `x-MS-API-ROLE` header to determine which role context to apply

| Scenario | Role DAB uses |
|----------|--------------|
| No token | `anonymous` |
| Token only, no `x-MS-API-ROLE` header | `authenticated` (built-in) |
| Token + `x-MS-API-ROLE: operations` | `operations` (custom) |

**Critical exam trap** (q072):
- If an entity grants `read` to `authenticated` but NOT to `operations` — a request with token + `x-MS-API-ROLE: operations` will **FAIL** for that entity (wrong role)
- Without the `x-MS-API-ROLE` header, DAB falls back to `authenticated` → **succeeds**

### Database Policies

- Fine-grained row-level filters applied server-side by DAB when a role accesses an entity
- Defined inside the entity's permission block:

```json
"permissions": [
  {
    "role": "operations",
    "actions": ["execute"],
    "policy": { "database": "@claims.userId eq item.OwnerId" }
  }
]
```

- Enforced by DAB before executing the query — adds a WHERE clause automatically

---

## 4. DAB Deployment on Azure Container Apps

### Deployment Steps

1. Build / pull the DAB Docker image: `mcr.microsoft.com/azure-databases/data-api-builder`
2. Push `dab-config.json` as a configuration mount or bake into the image
3. Deploy to Azure Container Apps (ACA)
4. Set **ingress** to **External** (port 80 or 443) so clients can reach it from the internet
5. Set Azure SQL **firewall rule `0.0.0.0` to `0.0.0.0`** to allow Azure services to connect

### Firewall Rule: 0.0.0.0 — 0.0.0.0

- This special rule means: **allow connections from any Azure service** (not from the entire internet)
- The container app's outbound IPs count as "Azure services" — this is the intended way to allow ACA → Azure SQL
- **Trap**: This does NOT open the database to the public internet — it only allows Azure-originated traffic

### Container Apps Ingress Settings

| Setting | Meaning |
|---------|---------|
| **External** | Accepts inbound traffic from the public internet |
| **Internal** | Only accessible within the VNet / Container Apps Environment |
| **Disabled** | No inbound HTTP traffic at all |

- DAB serving public API clients → must be **External**

---

## 5. Azure Monitor, Application Insights, Log Analytics

### Monitoring Stack for Azure SQL + DAB

| Layer | Tool | What It Monitors |
|-------|------|-----------------|
| Infrastructure metrics | **Azure Monitor** | CPU, DTU/vCore, storage, connections |
| Application telemetry | **Application Insights** | Request traces, dependency calls, exceptions, latency |
| Log querying | **Log Analytics Workspace** | KQL queries across all diagnostic logs |
| SQL-specific | **Query Performance Insight** | Top CPU/IO queries, wait stats |
| Alerts | **Azure Monitor Alerts** | Threshold-based (metric) or log-based |

### Key Diagnostic Log Categories for Azure SQL

| Category | What It Contains |
|----------|-----------------|
| `SQLSecurityAuditEvents` | Audit log entries |
| `QueryStoreRuntimeStatistics` | Query Store runtime data |
| `Errors` | Database errors and exceptions |
| `Deadlocks` | Deadlock graphs |
| `Blocks` | Blocking chain information |

- Enable via: Azure Portal → SQL DB → Diagnostic Settings → Send to Log Analytics Workspace
- Query logs with KQL: `AzureDiagnostics | where Category == "Errors"`

### Application Insights for DAB

- Add App Insights connection string to ACA environment variables
- DAB emits traces for each REST/GraphQL request: latency, status codes, entity accessed
- Use **Live Metrics** for real-time request monitoring
- Use **Application Map** to see DAB → Azure SQL dependency latency

---

## 6. Change Handling — CDC vs Change Tracking vs CES vs Triggers

### Comparison Table

| Method | Granularity | What It Captures | Overhead | Best For |
|--------|------------|-----------------|----------|---------|
| **Change Tracking** | Row-level (changed row IDs only) | Which rows changed (no old values) | Low | Azure Functions SQL trigger binding, sync scenarios |
| **CDC (Change Data Capture)** | Column-level | Old + new values, operation type (I/U/D) | Medium | Audit trails, data pipelines, embedding updates offloaded to Functions |
| **CES (Change Event Streaming)** | Fabric SQL only | Real-time event stream from Fabric SQL | Low | Event-driven architectures in Microsoft Fabric |
| **DML Triggers** | Row/statement | Inline with transaction | Varies | Simple cascades, inline validation — NOT for calling external services |
| **Logic Apps** | Polling-based | REST/webhook integrations | Low-Medium | Low-throughput integrations, no-code scenarios |

### Azure Functions SQL Trigger Binding

- Uses **Change Tracking** under the hood (NOT CDC)
- Fires when rows are inserted, updated, or deleted in a tracked table
- Setup:
  1. **Enable Change Tracking on the database**: `ALTER DATABASE MyDB SET CHANGE_TRACKING = ON`
  2. **Enable Change Tracking on the table**: `ALTER TABLE dbo.MyTable ENABLE CHANGE_TRACKING`
  3. Configure the Azure Functions binding with `SqlTrigger` attribute

```csharp
[Function("ProcessTodoChanges")]
public static void Run(
    [SqlTrigger("[dbo].[ToDo]", "SqlConnectionString")] 
    IReadOnlyList<SqlChange<ToDoItem>> changes,
    FunctionContext context)
{
    foreach (var change in changes)
    {
        // change.Operation = Insert | Update | Delete
        // change.Item = the row data
    }
}
```

- **Trap**: The exam often offers CDC as a distractor. Azure SQL trigger binding requires **Change Tracking** — CDC will NOT work with this binding.

### CDC (Change Data Capture)

- Captures the **full before/after values** of changed columns — richer than Change Tracking
- Stores change records in system tables: `cdc.dbo_<table>_CT`
- Enable:

```sql
-- Enable CDC on the database
EXEC sys.sp_cdc_enable_db;

-- Enable CDC on a specific table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name = N'Articles',
    @role_name = NULL;
```

- Use case: embed an Azure Functions app that reads CDC tables, regenerates embeddings only for changed rows → minimises CPU on the source DB

### Choosing the Right Method

| Scenario | Use |
|----------|-----|
| Azure Functions SQL trigger binding | **Change Tracking** |
| Audit trail / full old+new values | **CDC** |
| Minimise DB CPU for embedding updates | **CDC** + external Azure Functions |
| Real-time event stream in Fabric | **CES** |
| No-code / low-throughput integration | **Logic Apps** |
| Transactional inline logic | **DML trigger** (not for external calls) |

---

## 7. Fabric GraphQL API (Bonus — q076)

### Permission Model

Fabric GraphQL APIs have two separate permission layers:

| Permission | What It Controls |
|------------|-----------------|
| **Run Queries and Mutations** | Execute data queries/mutations through the API |
| **View and Edit GraphQL item** | Edit the API definition (field mappings, schema) |

- A user can have "View and Edit" but NOT "Run Queries" → they can **change field mappings but cannot read data**
- SSO means the user's Entra identity is passed through — Fabric SQL respects the Viewer workspace role for data access
- **Trap**: Viewer workspace role + "View and Edit GraphQL item" ≠ ability to read or modify data via the API

---

## Common Exam Traps

| Trap | Reality |
|------|---------|
| DAB REST URL is `/api/{Entity}` | Correct pattern is `/data-api/api/{Entity}` |
| Azure Functions SQL trigger binding uses CDC | It uses **Change Tracking** — CDC is a distractor |
| Firewall 0.0.0.0–0.0.0.0 opens DB to internet | It only allows **Azure services** — not public internet |
| Entity has `["read","create"]` → implies update | `update` must be explicitly listed — `create` ≠ `update` |
| `x-MS-API-ROLE: operations` activates all permissions | Only activates permissions granted to `operations` role specifically |
| Omitting `x-MS-API-ROLE` uses anonymous | Without token → anonymous; with token → `authenticated` |
| "View and Edit GraphQL item" allows data reads | Only `Run Queries and Mutations` enables data access |
| Trigger is best for embedding updates at scale | Triggers run inline — offload AI work to CDC + Azure Functions |

---

## Quick Reference

### DAB Decision Flow

- Need anonymous public read? → `"role": "anonymous", "actions": ["read"]`
- Need to expose a stored procedure? → `"type": "stored-procedure"` + `"execute"` action
- Need GraphQL relationships? → `relationships` block in entity config
- Need to allow ACA to connect to Azure SQL? → Firewall rule `0.0.0.0` to `0.0.0.0`
- Need internet clients to reach ACA-hosted DAB? → External ingress
- Connection string in config file? → Use `@env('VAR_NAME')` — never hardcode

### Change Handling Decision Flow

- Azure Functions SQL trigger binding? → **Enable Change Tracking** (not CDC)
- Need old + new values captured? → **CDC**
- Minimise DB CPU for embedding regeneration? → **CDC** + Azure Functions (offloaded)
- No-code integration? → **Logic Apps**
- Fabric SQL real-time streaming? → **CES**

---

## Related Questions

q042, q043, q044, q045, q046, q072, q074, q076

```powershell
python quiz_runner.py --ids q042,q043,q044,q045,q046,q072,q074,q076 questions.json
```
