---
name: youtrack-rest-api-calls
description: "Use when: building integrations with YouTrack, making REST API calls to YouTrack, scripting issue operations, automating issue management tasks, or working with YouTrack data programmatically."
---

# YouTrack REST API Integration Skill

## Overview

This skill provides a structured workflow for making REST API calls to YouTrack. Use it when writing scripts, integrations, or automation that interacts with YouTrack data.

## Workflow Steps

### 1. **Setup Authentication**

**Purpose**: Establish secure access to YouTrack API

- Generate a permanent token in YouTrack user profile (recommended over OAuth for scripts/automation)
  - Profile → Account Security tab → New Token button
  - Select scope: `YouTrack` (basic operations) or `YouTrack Administration` (project/user management)
  - Copy token immediately (cannot be retrieved again)
- Store token securely (environment variable, secrets manager, not hardcoded)
- Use `Authorization: Bearer <token>` header for all API requests

**Key Endpoints by Scope**:
- `YouTrack` scope: `/youtrack/rest/...`, `/youtrack/api/...`
- `YouTrack Administration` scope: `/hub/api/...`, `/hub/rest/...`

### 2. **Determine API Endpoint and Method**

**Purpose**: Identify the correct resource for your operation

- Review [REST API Reference](https://www.jetbrains.com/help/youtrack/devportal/rest-api-reference.html) for available resources and methods
- Check [REST API Use Cases](https://www.jetbrains.com/help/youtrack/devportal/api-use-cases.html) for common operations:
  - **Issues**: Create, retrieve, update, delete
  - **Custom Fields**: Get/set values, manage field sets
  - **Tags**: Add/remove tags from issues
  - **Attachments**: Upload, download, delete files
  - **Links**: Link/unlink issues
  - **Projects**: Create/manage projects and teams
  - **Users/Groups**: Manage permissions and access

### 3. **Construct Request Headers**

**Purpose**: Ensure proper data formatting and authentication

**Required headers for all requests**:
```
Authorization: Bearer <permanent-token>
Accept: application/json
Content-Type: application/json (for POST/PUT requests)
```

**Optional headers**:
- `If-Match`: For conflict avoidance when updating (use entity version)

### 4. **Build Query Parameters and Request Body**

**Purpose**: Filter, paginate, and shape API responses

**Query Parameters**:
- `fields=<field-list>`: Specify which entity fields to return (comma-separated or parenthetical notation)
  - Example: `?fields=id,summary,reporter(name)`
  - Use OpenAPI spec or reference docs to find available fields
- `query=<search-query>`: Filter issues using YouTrack query syntax
  - Example: `?query=project:PROJ AND state:Open`
  - Syntax: [Query Syntax Guide](https://www.jetbrains.com/help/youtrack/devportal/api-query-syntax.html)
- `$skip=<number>`: Pagination offset (default 0)
- `$top=<number>`: Limit results (default varies, check endpoint docs)

**Request Body** (POST/PUT):
- Always send JSON format
- Use entity field names from API reference
- For custom fields, use field name with schema prefix (e.g., `customFields[0].name`, `customFields[0].value`)
- Example:
```json
{
  "summary": "Issue title",
  "description": "Issue description",
  "customFields": [
    {"name": "Priority", "value": "High"}
  ]
}
```

### 5. **Make the API Call**

**Purpose**: Execute the request and handle the response

**URL Format**:
```
https://<youtrack-url>/youtrack/api/issues?<query-params>
```

**Tools**:
- cURL: `curl -H "Authorization: Bearer <token>" -H "Accept: application/json" "https://..."` 
- Python `requests`: Set headers dict and use `requests.get()`, `requests.post()`
- JavaScript `fetch()`: Set headers in options object
- Postman: Use [YouTrack Postman Collection](https://www.jetbrains.com/help/youtrack/devportal/youtrack-postman-collection.html)

**Handle Responses**:
- `200/201`: Success — parse response JSON
- `400`: Bad request — check query syntax and field names
- `401`: Unauthorized — verify token and scope
- `403`: Forbidden — check user permissions for operation
- `404`: Not found — verify entity ID or resource path
- `409`: Conflict — retry with `If-Match` header or refresh entity state

### 6. **Process Results and Handle Pagination**

**Purpose**: Retrieve all data when results exceed limit

- Check response structure (typically array under `issues`, `projects`, etc. key)
- For paginated results: compare returned count to `$top` limit
- To get next batch: increment `$skip` parameter by previous `$top` value
- Repeat API call until no results returned

**Example pagination loop**:
```
skip = 0
top = 50
all_items = []
while True:
  response = call_api(f"?$skip={skip}&$top={top}")
  all_items.extend(response['issues'])
  if len(response['issues']) < top:
    break
  skip += top
```

## Common Use Cases Reference

| Task | Key Endpoint | Method | Notes |
|------|--------------|--------|-------|
| List all issues in project | `/youtrack/api/issues` | GET | Use `query=project:KEY` filter |
| Create issue | `/youtrack/api/issues` | POST | Set summary in body |
| Get issue details | `/youtrack/api/issues/{id}` | GET | Use `fields` to specify custom fields |
| Update issue | `/youtrack/api/issues/{id}` | POST | Include `fields` you're updating |
| Add comment | `/youtrack/api/issues/{id}/comments` | POST | Body: `{"text": "..."}` |
| Add tag | `/youtrack/api/issues/{id}/tags` | POST | Body: `{"name": "tagname"}` |
| Attach file | `/youtrack/api/issues/{id}/attachments` | POST | Use multipart form-data |
| Get custom field value | `/youtrack/api/issues/{id}` | GET | Use `fields=customFields(name,value)` |
| Update custom field | `/youtrack/api/issues/{id}` | POST | Include in `customFields` array |

## Key Concepts

### Fields Syntax
- Simple fields: `id`, `summary`, `created`
- Nested fields: `reporter(name,email)`, `customFields(name,value(name))`
- Use OpenAPI spec as authoritative source for available fields

### Query Syntax
- Boolean operators: `AND`, `OR`, `NOT`
- Comparisons: `=`, `!=`, `>`, `<`, `>=`, `<=`
- Text search: Use field name or full-text search
- Examples: `state:Open`, `assignee:me`, `created:2024-01-01..2024-12-31`

### Pagination
- Default limit varies by endpoint (check docs)
- Always use `$skip` and `$top` for large result sets
- Combine with specific query filters to reduce data transfer

## Troubleshooting

**Common Issues**:
- **"Unauthorized" (401)**: Token missing, expired, or wrong scope
- **"Field not found"**: Check field name casing and custom field naming convention
- **Slow responses**: Add `fields` parameter to request only needed fields
- **Partial results**: Implement pagination loop
- **Version mismatches**: Check [REST API Changelog](https://www.jetbrains.com/help/youtrack/devportal/api-changelog.html) for version-specific changes

## Resources

- **[YouTrack Developer Portal](https://www.jetbrains.com/help/youtrack/devportal/youtrack-dev-portal.html)**
- **[REST API Overview](https://www.jetbrains.com/help/youtrack/devportal/youtrack-rest-api.html)**
- **[REST API Reference](https://www.jetbrains.com/help/youtrack/devportal/rest-api-reference.html)**
- **[OpenAPI Specification](https://www.jetbrains.com/help/youtrack/devportal/youtrack-openapi-specification.html)**
- **[Postman Collection](https://www.jetbrains.com/help/youtrack/devportal/youtrack-postman-collection.html)**
- **[REST API Troubleshooting](https://www.jetbrains.com/help/youtrack/devportal/api-troubleshooting.html)**

