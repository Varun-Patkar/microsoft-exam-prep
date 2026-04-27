# Day 2: Implement Data Security and Compliance

**Date**: 2026-04-27
**Domain**: 2 — Secure, Optimize, and Deploy Database Solutions (40–45%)
**Subtopics**: Always Encrypted, Dynamic Data Masking, Row-Level Security, Object-Level Permissions, Passwordless Access, Auditing, Securing Endpoints

## Key Concepts

### 1. Always Encrypted

**What it is:** Client-side encryption that ensures sensitive data is never exposed in plaintext to the Database Engine. Encryption/decryption happens in the client driver.

**Key Hierarchy:**

- **Column Master Key (CMK):** Stored externally (Azure Key Vault, Windows Certificate Store, HSM). Protects CEKs.
- **Column Encryption Key (CEK):** Encrypts actual column data. Stored encrypted in database metadata.

**T-SQL:**

```sql
CREATE COLUMN MASTER KEY MyCMK
WITH (KEY_STORE_PROVIDER_NAME = 'AZURE_KEY_VAULT',
      KEY_PATH = 'https://myvault.vault.azure.net/keys/MyCMK/...');

CREATE COLUMN ENCRYPTION KEY MyCEK
WITH VALUES (COLUMN_MASTER_KEY = MyCMK,
             ALGORITHM = 'RSA_OAEP',
             ENCRYPTED_VALUE = 0x01BA...);

-- Encrypt a column (done via SSMS wizard or sqlpackage, not plain T-SQL at runtime)
ALTER TABLE dbo.Customers
ALTER COLUMN SSN NVARCHAR(11)
ENCRYPTED WITH (ENCRYPTION_TYPE = DETERMINISTIC,
                ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256',
                COLUMN_ENCRYPTION_KEY = MyCEK);
```

**Deterministic vs Randomized Encryption:**

| Feature                           | Deterministic                         | Randomized                              |
| --------------------------------- | ------------------------------------- | --------------------------------------- |
| Same plaintext → same ciphertext? | Yes                                   | No (different each time)                |
| Point lookups (= , IN)            | Supported                             | NOT supported                           |
| GROUP BY, DISTINCT                | Supported                             | NOT supported                           |
| Indexing                          | Supported                             | NOT supported                           |
| Pattern matching, range queries   | NOT supported (without enclaves)      | NOT supported (without enclaves)        |
| Security level                    | Lower (patterns visible)              | Higher (no patterns leaked)             |
| Use when                          | Column is used in WHERE/JOIN/GROUP BY | Column is only returned, never filtered |

**Always Encrypted with Secure Enclaves:**

- Enables server-side computation on encrypted data inside a trusted memory enclave
- Supports: range comparisons (>, <, BETWEEN), LIKE pattern matching, sorting, indexing on randomized columns
- Key benefit: you can use randomized encryption AND still do rich queries
- Encryption/re-encryption happens in-place (no data movement to client)

### 2. Dynamic Data Masking (DDM)

**What it is:** Presentation-layer masking that hides sensitive data in query results. Data at rest is NOT changed. NOT encryption.

**Masking Functions:**

| Function                               | Syntax                                          | Example Input → Output                         |
| -------------------------------------- | ----------------------------------------------- | ---------------------------------------------- |
| default()                              | `MASKED WITH (FUNCTION = 'default()')`          | "Hello" → "XXXX", 12345 → 0, date → 1900-01-01 |
| email()                                | `MASKED WITH (FUNCTION = 'email()')`            | "john@contoso.com" → "jXXX@XXXX.com"           |
| partial(prefix, padding, suffix)       | `MASKED WITH (FUNCTION = 'partial(1,"XXX",1)')` | "Roberto" → "RXXXO"                            |
| random(start, end)                     | `MASKED WITH (FUNCTION = 'random(1,100)')`      | 42 → random number 1-100                       |
| datetime("Y"\|"M"\|"D"\|"h"\|"m"\|"s") | `MASKED WITH (FUNCTION = 'datetime("Y")')`      | Masks year portion (SQL Server 2022+)          |

**T-SQL:**

```sql
-- Add mask to existing column
ALTER TABLE dbo.Customers
ALTER COLUMN Email ADD MASKED WITH (FUNCTION = 'email()');

-- Remove mask
ALTER TABLE dbo.Customers
ALTER COLUMN Email DROP MASKED;

-- Grant unmasked access
GRANT UNMASK TO SupportUser;

-- Granular UNMASK (SQL Server 2022+): column, table, schema, or database level
GRANT UNMASK ON dbo.Customers(Email) TO SupportUser;
GRANT UNMASK ON SCHEMA::dbo TO ManagerRole;
```

**Key behaviors:**

- sysadmin, db_owner have CONTROL permission → always see unmasked data
- UNMASK alone does nothing without SELECT
- DDM does NOT prevent UPDATE — users can still write to masked columns if they have write permissions
- SELECT INTO / INSERT INTO by non-UNMASK user → masked data copied to target
- Cannot mask: Always Encrypted columns, computed columns, FILESTREAM, COLUMN_SET

### 3. Row-Level Security (RLS)

**What it is:** Transparent row filtering/blocking enforced at the database engine level via security policies.

**Two predicate types:**

| Type             | Purpose                             | Behavior                                                                      |
| ---------------- | ----------------------------------- | ----------------------------------------------------------------------------- |
| Filter predicate | Controls which rows are visible     | Silently filters SELECT, UPDATE, DELETE — app doesn't know rows were filtered |
| Block predicate  | Prevents writes that violate policy | AFTER INSERT, AFTER UPDATE, BEFORE UPDATE, BEFORE DELETE — raises error       |

**T-SQL pattern:**

```sql
-- Step 1: Create predicate function (inline TVF)
CREATE FUNCTION Security.fn_TenantFilter(@TenantId INT)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN SELECT 1 AS result
WHERE @TenantId = CAST(SESSION_CONTEXT(N'TenantId') AS INT);

-- Step 2: Create security policy
CREATE SECURITY POLICY Security.TenantPolicy
ADD FILTER PREDICATE Security.fn_TenantFilter(TenantId) ON dbo.Tickets,
ADD BLOCK PREDICATE Security.fn_TenantFilter(TenantId) ON dbo.Tickets AFTER INSERT
WITH (STATE = ON);
```

**User context functions:**

- `USER_NAME()` / `SUSER_SNAME()` — current user
- `SESSION_CONTEXT(N'key')` — app-set session value (for middle-tier apps)
- `DATABASE_PRINCIPAL_ID()` — current database principal

**Key behaviors:**

- RLS applies to ALL users including dbo/db_owner unless the policy function explicitly exempts them
- SCHEMABINDING = ON (default) → bypasses permission checks on predicate function
- Microsoft Fabric / Azure Synapse: filter predicates only, NO block predicates
- Temporal tables: must add separate predicate to history table

### 4. Object-Level Permissions & Passwordless Access

**Permission hierarchy:**

```
GRANT SELECT ON SCHEMA::Sales TO ReaderRole;         -- schema level
GRANT SELECT ON Sales.Customer TO AppRole;            -- table level
DENY SELECT ON Sales.Customer(TaxID) TO AppRole;      -- column level DENY
GRANT EXECUTE ON Sales.usp_GetCustomer TO AppRole;    -- object level
```

**Key rule: DENY always wins over GRANT** — column-level DENY overrides table-level GRANT.

**Managed Identity types:**

| Feature   | System-assigned                         | User-assigned                                        |
| --------- | --------------------------------------- | ---------------------------------------------------- |
| Lifecycle | Tied to resource, deleted with resource | Independent, survives resource deletion              |
| Sharing   | 1:1 with resource                       | Can be shared across multiple resources              |
| Best for  | Single-resource simple scenarios        | Multi-resource, on-prem migration, portable identity |

**Passwordless connection setup:**

```sql
-- In Azure SQL, create user for the managed identity
CREATE USER [my-app-service] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [my-app-service];
```

### 5. Auditing & Securing Endpoints

**Azure SQL Auditing:**

- Destinations: Azure Storage Account, Log Analytics workspace, Event Hubs
- Captures: SELECT, INSERT, UPDATE, DELETE, EXECUTE, login events
- Server-level vs database-level auditing

**DATABASE SCOPED CREDENTIAL with Managed Identity:**

```sql
CREATE DATABASE SCOPED CREDENTIAL MyAzureCredential
WITH IDENTITY = 'Managed Identity',
SECRET = '{"resourceid": "https://cognitiveservices.azure.com"}';
```

- Used for calling Azure OpenAI, Cognitive Services from SQL Server
- Highest security: no API keys stored, uses managed identity token

**Securing endpoints:**

- Model endpoints: Managed Identity + RBAC, avoid API keys
- GraphQL/REST: Azure AD/Entra ID auth, HTTPS, API Management
- MCP endpoints: Same auth patterns, secure with managed identity

## Important Details for Exam

1. **Always Encrypted order of operations:** CEK must exist before you can encrypt columns
2. **Ledger + Always Encrypted combo (q028):** Create CEK → Create table with LEDGER → Copy data → Encrypt columns
3. **DDM + RLS interaction (q077):**
   - If RLS filters out a row, DDM never applies (row not returned at all)
   - RLS still applies to admins (they can be filtered out) even though they see unmasked data
   - DDM meets PII security requirements
4. **DATABASE SCOPED CREDENTIAL for Azure OpenAI:** Use `IDENTITY = 'Managed Identity'` with `SECRET = '{"resourceid":"..."}'`
5. **User-assigned managed identity** preferred for apps migrating from password-based auth (portable, shareable)
6. **Granular UNMASK** (SQL Server 2022+): Can grant at column, table, schema, or database level

## Common Traps & Misconceptions

| Trap                                      | Reality                                                                                       |
| ----------------------------------------- | --------------------------------------------------------------------------------------------- |
| "DDM encrypts data"                       | DDM is NOT encryption — it's presentation-layer masking only                                  |
| "DDM protects against direct DB access"   | Users can infer values via WHERE clauses                                                      |
| "RLS doesn't apply to db_owner"           | RLS applies to ALL users including db_owner by default                                        |
| "Randomized encryption supports equality" | Only DETERMINISTIC supports = , IN, GROUP BY                                                  |
| "Enclaves decrypt data on the client"     | Enclaves process encrypted data SERVER-side in trusted memory                                 |
| "REVOKE removes DENY"                     | REVOKE removes both GRANT and DENY; DENY must be explicitly revoked                           |
| "System-assigned identity for multi-app"  | Use user-assigned for sharing across multiple resources                                       |
| "TDE protects from DBAs"                  | TDE is transparent to queries — DBAs can still read data. Always Encrypted protects from DBAs |

## Comparisons

### DDM vs Always Encrypted vs TDE

| Feature                | DDM          | Always Encrypted          | TDE              |
| ---------------------- | ------------ | ------------------------- | ---------------- |
| Protects data at rest? | No           | Yes                       | Yes              |
| Protects from DBA?     | No           | Yes                       | No               |
| Encryption?            | No (masking) | Yes (client-side)         | Yes (file-level) |
| Performance impact     | Minimal      | Moderate                  | Minimal          |
| Granularity            | Column       | Column                    | Database         |
| Query impact           | None         | Significant (limited ops) | None             |

### When to Use Each Security Feature

| Scenario                                 | Feature                                       |
| ---------------------------------------- | --------------------------------------------- |
| Hide SSN in support app queries          | DDM (partial masking)                         |
| Encrypt credit card numbers end-to-end   | Always Encrypted                              |
| Multi-tenant row isolation               | Row-Level Security                            |
| Prevent role from seeing specific column | DENY SELECT on column                         |
| Passwordless app-to-DB connection        | Managed Identity                              |
| Call Azure OpenAI from SQL Server        | DATABASE SCOPED CREDENTIAL + Managed Identity |

## Quick Reference

- **CMK:** External key store (Key Vault, cert store). Protects CEKs.
- **CEK:** Encrypts column data. Stored encrypted in DB metadata.
- **Deterministic:** Same input = same output. Supports equality only.
- **Randomized:** Same input = different output each time. No query operations.
- **Enclaves:** Unlock rich queries on encrypted data server-side.
- **DDM functions:** default(), email(), partial(p,pad,s), random(lo,hi), datetime()
- **UNMASK:** Permission to see unmasked data. Granular in SQL 2022+.
- **RLS:** Filter predicate (silent WHERE), Block predicate (prevent writes)
- **DENY > GRANT:** Always. At any level.
- **Managed Identity:** System-assigned (1:1) vs User-assigned (shareable)

## Related Questions

q023, q024, q025, q026, q027, q028, q029, q077, q079
