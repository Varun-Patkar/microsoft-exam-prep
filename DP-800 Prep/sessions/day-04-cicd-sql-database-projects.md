# Day 4: Implement CI/CD by Using SQL Database Projects (2.3)

**Date**: 2026-04-29
**Domain**: 2 — Secure, Optimize, and Deploy Database Solutions (35–40%)
**Subtopics**: SQL Database Projects (SDK-style), dacpac, dotnet build, SqlPackage, testing (unit + integration), source control, branching, schema drift, secrets management, deployment pipelines

---

## 1. SQL Database Projects

### What Is a SQL Database Project?

- Your database **in file form** — every table, view, stored procedure, function lives in its own `.sql` file
- **Declarative model**: you define the desired end state, not a chain of migration scripts
- Build output = `.dacpac` (compiled model of entire database schema)
- The `.dacpac` is the **single deployable artifact** that flows through your CI/CD pipeline

### Original vs SDK-Style Projects

| Feature | Original (.NET Framework / SSDT) | SDK-Style (Microsoft.Build.Sql) |
|---------|--------------------------------|-------------------------------|
| Build runtime | MSBuild (.NET Framework) | .NET 8+ (cross-platform) |
| OS support | Windows only | Windows, Linux, macOS |
| IDE | Visual Studio (full SSDT) | VS Code (SQL Database Projects extension) |
| DB references | Project references | **NuGet package references** |
| File inclusion | Manual file entries in .sqlproj | **Default globbing** — drop .sql file in folder, auto-included |
| Create command | `dotnet new sqlproj -n MyProject` | Same |

### Key Commands

```bash
# Create new SDK-style project
dotnet new sqlproj -n MyDatabaseProject

# Build → produces .dacpac in bin/Debug/
dotnet build MyDatabaseProject.sqlproj

# Build Release → .dacpac in bin/Release/
dotnet build MyDatabaseProject.sqlproj -c Release

# Install SqlPackage (cross-platform .NET global tool)
dotnet tool install --global microsoft.sqlpackage

# Publish dacpac to target database
sqlpackage /Action:Publish /SourceFile:bin/Debug/MyProject.dacpac /TargetConnectionString:"..."

# Preview deployment script (without executing)
sqlpackage /Action:Script /SourceFile:bin/Debug/MyProject.dacpac /TargetConnectionString:"..." /DeployScriptPath:Deployment.sql

# Preview deployment report (XML summary of planned CREATE/ALTER/DROP)
sqlpackage /Action:DeployReport /SourceFile:bin/Debug/MyProject.dacpac /TargetConnectionString:"..." /OutputPath:report.xml
```

### How Deployment Works

- **New database**: SqlPackage navigates the object dependency graph, creates each object in correct order
- **Existing database**: calculates the **diff** between `.dacpac` and live schema, generates only the `ALTER` statements needed
- **Idempotent**: deploy same `.dacpac` 5 times → 5th run changes nothing
- Can fan out a single `.dacpac` across a fleet of databases (multi-tenant)

### System Database References (Exam Favorite!)

- SDK-style projects need NuGet packages to reference system databases (`master`, `msdb`)
- **Azure SQL Database target**: use `Microsoft.SqlServer.Dacpacs.Azure.Master`
- **On-premises SQL Server target**: use `Microsoft.SqlServer.Dacpacs.Master`
- **Wrong package = build failure** — if your project targets Azure SQL DB and you add the on-prem `Master` package, it won't resolve Azure-specific system objects

---

## 2. Source Control & Reference Data

### Project Structure

```
MyDatabaseProject/
├── MyDatabaseProject.sqlproj
├── Tables/
│   ├── Customers.sql
│   └── Orders.sql
├── Views/
│   └── vw_ActiveCustomers.sql
├── StoredProcedures/
│   └── usp_GetCustomerOrders.sql
├── Scripts/
│   ├── PostDeployment/
│   │   └── seed-data.sql
│   └── PreDeployment/
│       └── prep-db.sql
└── PostDeploy.sql
```

### .gitignore Essentials

```
bin/
obj/
*.dacpac
*.user
```

- `.dacpac` gets recreated on every CI build — don't track it in Git

### Pre-Deployment & Post-Deployment Scripts

- **Pre-deployment**: runs BEFORE the deployment plan (drop constraints, migrate data)
- **Post-deployment**: runs AFTER the deployment plan (seed reference data, lookup tables)
- Project supports exactly **one** pre-deployment script and **one** post-deployment script
- Declared in `.sqlproj`:

```xml
<ItemGroup>
    <PreDeploy Include="prep-db.sql" />
</ItemGroup>
<ItemGroup>
    <PostDeploy Include="PostDeploy.sql" />
</ItemGroup>
```

### SQLCMD Includes for Multiple Data Files

- Use `:r` syntax in the main post-deploy script to include multiple files:

```sql
:r .\Scripts\PostDeployment\seed-statuses.sql
:r .\Scripts\PostDeployment\seed-regions.sql
```

- Each referenced file must be **excluded from build** (otherwise build tries to compile it as a schema object):

```xml
<ItemGroup>
    <Build Remove="Scripts\PostDeployment\seed-statuses.sql" />
    <None Include="Scripts\PostDeployment\seed-statuses.sql" />
</ItemGroup>
```

### Idempotent Reference Data Scripts

- Post-deployment scripts run on **every** deployment, not just the first
- Plain `INSERT` → duplicate key violation on second deploy
- **Use MERGE** for idempotent inserts:

```sql
MERGE INTO [dbo].[OrderStatuses] AS target
USING (VALUES
    (1, N'Pending'),
    (2, N'Processing'),
    (3, N'Shipped'),
    (4, N'Delivered'),
    (5, N'Cancelled')
) AS source ([StatusID], [StatusName])
ON target.[StatusID] = source.[StatusID]
WHEN MATCHED THEN
    UPDATE SET [StatusName] = source.[StatusName]
WHEN NOT MATCHED THEN
    INSERT ([StatusID], [StatusName])
    VALUES (source.[StatusID], source.[StatusName]);
```

- Alternative: `IF NOT EXISTS` + `INSERT` (also acceptable in exam)

---

## 3. Branching, PRs, and Conflict Resolution

### Feature Branch Workflow

1. Branch off `main` for every change
2. Merge back through **pull requests**
3. Keep `main` in a deployable state at all times
4. Keep branches **short-lived** — reduces merge conflicts

### PR Best Practices for Database Projects

- Configure CI build as a **PR check** (build validation)
- `pull_request` trigger in GitHub Actions → validates before merge
- Reviewers check: does the schema change break existing queries? Naming conventions? Data loss? Need post-deploy script update?

### Merge Conflict Resolution

1. Pull latest `main` into feature branch
2. Resolve conflicts in the `.sql` files (usually straightforward — one object per file)
3. **Always rebuild after resolving**: `dotnet build MyDatabaseProject.sqlproj`
4. A clean text merge ≠ valid schema (e.g., one branch renames a column, another adds a proc referencing old name)

---

## 4. Schema Drift Detection

### What Is Schema Drift?

- Gap between what the **project defines** and what **exists in the live database**
- Causes: manual `ALTER TABLE` in SSMS, emergency hotfixes, ORM frameworks, third-party tools
- **Danger**: next dacpac deployment calculates diff → unrecognized objects get **dropped**

### Detection Methods

| Method | Tool | Use Case |
|--------|------|----------|
| **Schema Compare** | VS Code / Visual Studio | Interactive, visual diff between database ↔ project |
| **SqlPackage /Action:DriftReport** | CLI | Generate report of differences between deployed DB and source |
| **SqlPackage /Action:Extract** + `git status` | CLI + Git | Automated: extract live schema, compare with repo to count changed files |
| **SqlPackage /Action:DeployReport** | CLI | Preview planned CREATE/ALTER/DROP as XML before deploying |
| **SqlPackage /Action:Script** | CLI | Generate exact T-SQL that deployment would execute |

### Schema Comparison Options

- Ignore whitespace, ignore column order
- **Block on possible data loss** — flag destructive operations
- Save settings as `.scmp` file, commit to repo for team consistency

### DacpacVerify Tool

- Compares two `.dacpac` files (useful when converting SSDT → SDK-style)
- `dotnet tool install -g microsoft.dacpacverify`
- `dacpacverify before.dacpac after.dacpac`

---

## 5. Deployment Pipelines

### GitHub Actions Pipeline Structure

```yaml
# Build stage
- name: Build SQL project
  run: dotnet build ./Database.sqlproj -o ./output

- name: Upload dacpac artifact
  uses: actions/upload-artifact@v4
  with:
    name: dacpac
    path: ./output/Database.dacpac

# Deploy stage
- uses: azure/sql-action@v2.3
  with:
    connection-string: ${{ secrets.AZURE_SQL_CONNECTION_STRING }}
    path: './Database.dacpac'
    action: 'publish'
```

### Azure DevOps Pipeline

- Uses `SqlAzureDacpacDeployment@1` task
- Or install SqlPackage directly on Linux agents

### Key Action Types (azure/sql-action)

| Action | What It Does |
|--------|-------------|
| `publish` | Deploy `.dacpac` TO a database |
| `extract` | Create `.dacpac` FROM a database |

- **Exam trap**: `extract` pulls schema FROM db → does NOT deploy. `publish` deploys TO db.

### Secrets Management

| Method | Platform | Notes |
|--------|----------|-------|
| Repository secrets | GitHub | Scoped to entire repo |
| Environment secrets | GitHub | Scoped to specific deployment environment (e.g., production) |
| Pipeline variables (secret) | Azure DevOps | Masked in logs |
| Azure Key Vault | Both | Centralized, auto-rotation, pulled at runtime |
| OIDC (federated credentials) | Both | No password stored — uses `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` |

- **Never hardcode connection strings in YAML files**

### Deployment Pipeline Controls

| Control | Purpose |
|---------|---------|
| **Required reviewers** | Must approve before deploy job runs |
| **Wait timers** | Delay between approval and execution |
| **Deployment branches** | Only `main` can deploy to production |
| **Branch policies** | Min reviewers, build validation, comment resolution |
| **CODEOWNERS** | Require DB team review for SQL file changes |
| **Branch control checks** (Azure DevOps) | Only pipelines on `main` can access production service connections |

### CODEOWNERS File

```
# .github/CODEOWNERS
/Database/ @db-team
*.sql @db-team @dba-lead
```

---

## 6. Testing Strategy

### Three Levels of Database Testing

| Level | What It Catches | Speed | Requires DB? |
|-------|----------------|-------|-------------|
| **Build validation** | Syntax errors, broken object references | Fast | No |
| **Unit tests** | Logic errors in stored procs/functions | Medium | Yes (dev instance) |
| **Integration tests** | End-to-end workflow failures across objects | Slow | Yes (test instance) |

### SQL Server Unit Tests (SSDT in Visual Studio)

- Three-phase structure: **Pre-test** (setup data) → **Test** (execute proc) → **Post-test** (cleanup)
- Test conditions: `Row Count`, `Scalar Value`, `Expected Schema`, `Data Checksum`, `Empty ResultSet`, `Execution Time`
- **Negative tests**: use `[ExpectedSqlException(Severity = 16, State = 1)]` attribute — test passes only when procedure raises expected error
- Auto-deploy option: "Automatically deploy the database project before unit tests are run"

### Integration Tests

- Test scenarios spanning multiple operations (sequence of proc calls, trigger behavior, cross-view consistency)
- Need a **dedicated test database** — never test against production
- Reset to known state before each run

### Tests in CI/CD Pipeline

```yaml
# Azure DevOps
- task: VSTest@2
  inputs:
    testAssembly: '**\*Tests.dll'

# GitHub Actions
- name: Run database unit tests
  run: dotnet test ./DatabaseTests/DatabaseTests.csproj
```

- Failing test → pipeline stops → change doesn't reach staging/production

---

## Common Exam Traps

| Trap | Reality |
|------|---------|
| Using `Microsoft.SqlServer.Dacpacs.Master` for Azure SQL DB | Wrong — use `Microsoft.SqlServer.Dacpacs.Azure.Master` for Azure targets |
| Thinking `-bl` and `-flp:vdiag` fix missing system references | They only control logging verbosity, not dependencies |
| Using plain INSERT in post-deploy scripts | Fails on second deployment — use MERGE or IF NOT EXISTS |
| Confusing `extract` and `publish` in azure/sql-action | `extract` = FROM db, `publish` = TO db |
| `dotnet build -c Release` without updating dacpac path in publish step | Dacpac moves to `bin/Release/` — deploy step still points to `bin/Debug/` |
| Thinking `workflow_dispatch` prevents manual triggers | `workflow_dispatch` **enables** manual triggering |
| Thinking a clean text merge = valid schema | Must rebuild after resolving — renamed columns may break proc references |

---

## Key SqlPackage Actions Cheat Sheet

| Action | Command | Purpose |
|--------|---------|---------|
| **Publish** | `/Action:Publish` | Deploy dacpac to target database |
| **Script** | `/Action:Script` | Generate deployment T-SQL without executing |
| **DeployReport** | `/Action:DeployReport` | XML summary of planned changes |
| **DriftReport** | `/Action:DriftReport` | Report schema differences (drift) |
| **Extract** | `/Action:Extract` | Pull live schema into dacpac/files |

---

## Quick Reference

### Pipeline Decision Flow

- Need to validate PR before merge? → `pull_request` trigger + `dotnet build`
- Need to deploy dacpac? → `azure/sql-action@v2` with `action: publish`
- Need to check for schema drift? → `SqlPackage /Action:DriftReport`
- Need to preview deployment changes? → `SqlPackage /Action:Script` or `/Action:DeployReport`
- Need idempotent reference data? → MERGE in post-deployment script
- Need passwordless auth? → OIDC with federated credentials
- Need to ensure DB team reviews SQL changes? → CODEOWNERS file
- System DB ref for Azure SQL DB? → `Microsoft.SqlServer.Dacpacs.Azure.Master` NuGet package

---

## Related Questions

q035, q036, q037, q038, q039, q040, q041, q075
