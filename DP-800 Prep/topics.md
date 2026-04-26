# Developing AI-Enabled Database Solutions (DP-800) - Topics

**Certification:** Microsoft Certified: SQL AI Developer Associate
**Study Guide:** https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800
**Skills Measured As Of:** March 12, 2026
**Passing Score:** 700

---

## Domain 1: Design and Develop Database Solutions (35–40%)

### 1.1 Design and Implement Database Objects
- Design and implement tables, including data types, size, columns, indexes, and column store indexes
- Design and implement specialized tables, including in-memory, temporal, external, ledger, and graph
- Design and implement JSON columns and indexes
- Design and implement database constraints, including PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK, and DEFAULT
- Design and implement SEQUENCES
- Design and implement partitioning for tables and indexes

### 1.2 Implement Programmability Objects
- Create views
- Create scalar functions
- Create table-valued functions
- Create stored procedures
- Create triggers

### 1.3 Write Advanced T-SQL Code
- Write common table expressions (CTEs)
- Write queries that include window functions
- Write queries that include JSON functions, such as JSON_OBJECT, JSON_ARRAY, JSON_ARRAYAGG, JSON_CONTAINS, OPENJSON, and JSON_VALUE
- Write queries that include regular expressions, such as REGEXP_LIKE, REGEXP_REPLACE, REGEXP_SUBSTR, REGEXP_INSTR, REGEXP_COUNT, REGEXP_MATCHES, and REGEXP_SPLIT_TO_TABLE
- Write queries that include fuzzy string matching functions, such as EDIT_DISTANCE, EDIT_DISTANCE_SIMILARITY, and JARO_WINKLER_DISTANCE
- Write graph queries that use the MATCH operator
- Write correlated queries
- Implement error handling

### 1.4 Design and Implement SQL Solutions by Using AI-Assisted Tools
- Interpret security impact of using AI-assisted tools
- Enable GitHub Copilot and Microsoft Copilot in Fabric
- Configure model and Model Context Protocol (MCP) tool options in a GitHub Copilot or Copilot in Fabric chat session
- Create and configure GitHub Copilot instruction files
- Connect to MCP server endpoints, including Microsoft SQL Server and Fabric lakehouse

---

## Domain 2: Secure, Optimize, and Deploy Database Solutions (35–40%)

### 2.1 Implement Data Security and Compliance
- Design and implement data encryption, including Always Encrypted and column-level encryption
- Design and implement Dynamic Data Masking
- Design and implement Row-Level Security (RLS)
- Design and implement object-level permissions
- Implement secure database access, including passwordless
- Implement auditing
- Secure model endpoints, including Managed Identity
- Secure GraphQL, REST, and MCP endpoints

### 2.2 Optimize Database Performance
- Recommend database configurations
- Preserve data integrity and consistency by using transaction isolation levels and concurrency controls
- Evaluate query performance by using query execution plans, dynamic management views (DMVs), Query Store, and Query Performance Insight
- Identify and resolve query performance issues, including blocking and deadlocks

### 2.3 Implement CI/CD by Using SQL Database Projects
- Design and implement a testing strategy, including unit tests and integration tests
- Create and manage reference/static data in source control
- Create, build, and validate database models by using SQL Database Projects, including SDK-style models
- Configure source control for SQL Database Projects
- Manage branching, pull requests, and conflict resolution
- Implement secrets management
- Detect schema drift by using SQL Database Projects
- Update an SQL database project and deploy changes
- Design and implement controls for deployment pipelines, including branching policies, triggers in approvals, authentication tables, and code owners

### 2.4 Integrate SQL Solutions with Azure Services
- Create configuration files for Data API builder (DAB)
- Configure entities for REST and GraphQL, including data caching, pagination, searching, and filtering
- Configure REST or GraphQL endpoints
- Expose database objects, stored procedures, and views, including GraphQL relationships
- Configure and implement DAB deployment
- Recommend Azure Monitor configurations, including Application Insights and Log Analytics
- Handle changes by using change event streaming (CES), change data capture (CDC), Change Tracking, Azure Functions with SQL trigger binding, or Azure Logic Apps

---

## Domain 3: Implement AI Capabilities in Database Solutions (25–30%)

### 3.1 Design and Implement Models and Embeddings
- Evaluate external models, including multimodal, multilanguage, sizes, and structured output
- Create and manage external models
- Choose an embedding maintenance method, including table triggers, Change Tracking, Azure Functions with SQL trigger binding, Azure Logic Apps, CDC, CES, and Microsoft Foundry
- Identify which columns to include in embeddings
- Design and implement chunks for embeddings
- Generate embeddings

### 3.2 Design and Implement Intelligent Search
- Choose from full-text, semantic vector, and hybrid search
- Implement full-text search
- Design for vector data, including vector data type, vector indexes, and size
- Identify when to use vector-related types and functions for semantic searching, including VECTOR_NORMALIZE, VECTOR_DISTANCE, VECTORPROPERTY, and VECTOR_SEARCH
- Choose between using ANN and ENN for vector search
- Evaluate vector index types and metrics
- Implement vector search
- Implement hybrid search
- Implement reciprocal rank fusion (RRF)
- Evaluate performance of vector and hybrid search

### 3.3 Design and Implement Retrieval-Augmented Generation (RAG)
- Identify use cases for RAG
- Create a prompt by using the sp_invoke_external_rest_endpoint stored procedure
- Convert structured data to JSON for language model processing
- Send results to language model
- Extract language model responses

---

## Summary

| Domain | Weight | Subdomains | Total Skills |
|--------|--------|------------|-------------|
| Design and Develop Database Solutions | 35–40% | 4 | 25 |
| Secure, Optimize, and Deploy Database Solutions | 35–40% | 4 | 28 |
| Implement AI Capabilities in Database Solutions | 25–30% | 3 | 21 |
| **Total** | **100%** | **11** | **74** |
