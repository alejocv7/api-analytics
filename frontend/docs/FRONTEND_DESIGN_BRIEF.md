# API Analytics Platform - Frontend Design Brief

**Project**: API Analytics SaaS Platform
**Purpose**: Multi-tenant web application for tracking, analyzing, and visualizing API performance metrics
**Tech Stack**: Python/FastAPI backend, multi-tenant data architecture

---

## 1. Platform Overview

The API Analytics platform helps teams track real-time performance of their APIs. Users:
- **Create projects** to organize APIs they want to monitor
- **Generate API keys** that their applications/SDKs use to send metrics
- **View analytics dashboards** showing request counts, response times, error rates, and per-endpoint performance
- **Manage team access** by inviting members with different permission levels

**Core Value**: A centralized dashboard to understand API health and performance without complex infrastructure.

---

## 2. Key Entities & Relationships

### **User**
- Represents an individual account holder
- **Fields**: email, full_name, password, is_active, created_at
- **Can**: Register, login, view their own profile, manage owned projects

### **Project**
- Represents an API/service being monitored
- **Fields**: name, description, auto-generated project_key (unique slug), is_active
- **Owned by**: Exactly one user (the owner)
- **Shared with**: Other users as members (owner, member, viewer roles)
- **Contains**: API keys, metrics, and member list

### **API Key**
- Credentials that SDKs/applications use to submit metrics to the platform
- **Fields**: name, plain key (shown only once!), prefix, expiration date, is_active, last_used_at, total_requests
- **Security**: Key never shown again after creation; only owner can rotate/delete
- **Properties**: Can expire, can be revoked, tracks usage (last_used, request count)

### **Metric**
- Individual API request record (response time, status, endpoint, timestamp, etc.)
- **Fields**: url_path, HTTP method, status_code, response_time_ms, timestamp, ip_hash, user_agent
- **Volume**: Projects accumulate thousands/millions of metrics over time
- **Display**: Aggregated in analytics views (not usually individual records to end-user)

### **Member**
- User access to a project
- **Roles**:
  - **Owner**: Full control (settings, members, API keys, metrics)
  - **Member**: Can record metrics and read analytics (cannot manage)
  - **Viewer**: Read-only access to analytics

---

## 3. Main User Workflows

### **A. Authentication Flow**

```
Landing Page → Sign Up / Login → [Email verification if needed] → Dashboard
```

**Sign Up:**
- Collect: Email, password (validated for strength), full name
- Validates: Email unique, password complexity (entropy-based)
- Creates account, auto-logs in

**Login:**
- Collect: Email, password
- Features: Account lockout after 5 failed attempts (15 min timeout)
- Issues: JWT tokens (access + refresh token)

**Session Management:**
- Access tokens expire (short-lived, ~15 min)
- Refresh tokens are long-lived (~7 days)
- "Keep me logged in" / "Remember this device" = use longer refresh window
- Logout = invalidate tokens server-side

---

### **B. Project Management Workflow**

```
Dashboard → Create Project → Get API Key → Configure SDK → View Metrics
```

**Create Project:**
- Form: Name (required, 1-100 chars), description (optional)
- Result: Project gets auto-generated key (e.g., `production-api-a1b2`)
- User becomes owner automatically

**List Projects:**
- Dashboard shows all owned/shared projects
- Filter: Active/inactive toggle
- Sort: By creation date or custom order
- Each project card: name, creation date, member count, API key count

**Project Settings (Owner Only):**
- Update name, description
- Toggle active/inactive
- Delete project (irreversible)

**Invite Members (Owner Only):**
- Form: Email + role selector (member or viewer, not owner)
- If email doesn't exist: User gets invitation email
- If exists: Member added immediately
- Can later change role or remove member

---

### **C. API Key Management Workflow**

```
Project Settings → Generate New Key → [Display once, copy to clipboard] → Manage Keys
```

**Generate API Key:**
- Form: Key name (e.g., "Prod Server", "Staging"), expiration (optional, default 90 days)
- Result: Plain key shown only once with copy button + warning
- User must copy/save it; not shown again
- No way to recover lost key (security design)

**List API Keys:**
- Table: Name, status (active/inactive), created date, last used date, total requests, expiration
- Owner actions: Deactivate, rotate (create new + deactivate old), delete
- Members: Can view but not manage

**Rotate Key:**
- Creates new key (shown once)
- Deactivates old key
- Useful if compromised

---

### **D. Metrics & Analytics Workflow**

```
SDK sends metrics → Accumulate in DB → View in Analytics Dashboard
```

**Metrics Dashboard:**
- **Summary Statistics**: Total requests, avg response time, error rate, slowest/fastest requests, requests per minute
- **Time Series Chart**:
  - X-axis: Time (minute/hour/day granularity selectable)
  - Y-axis: Request count OR avg response time (toggleable)
  - Shows trends over selected date range
- **Date Range Filter**: Picker for start/end date (max 60 days, min 1 minute)
- **Endpoint Performance Table**:
  - Per-endpoint breakdown (grouped by path + HTTP method)
  - Columns: URL path, method, request count, avg response time, error count, error rate, slowest/fastest requests
  - Sortable, paginated
- **Raw Metrics Feed** (optional, low priority):
  - Individual requests with details
  - Useful for debugging anomalies

---

## 4. Pages & Screens

### **1. Landing Page** (Unauthenticated)
- Call-to-action: Sign Up / Login buttons
- Brief description of product
- Feature highlights
- Pricing (if applicable)

### **2. Authentication Pages**
- **Sign Up**: Email, password, full_name, terms acceptance
- **Login**: Email, password, remember me checkbox
- **Forgot Password** (if implemented): Email form, reset link

### **3. Dashboard** (Authenticated)
- List of user's projects (cards or table)
- "Create Project" button
- Each project card shows:
  - Project name
  - Description
  - Members count
  - API keys count
  - Last activity date
  - Action buttons: View, Settings, Delete

### **4. Project Settings**
- **General Tab**:
  - Name, description (editable)
  - Project key (read-only)
  - Active/inactive toggle
  - Delete project button (with confirmation)
- **Members Tab**:
  - List of members (owner, members, viewers)
  - Add member form (email + role selector)
  - Remove/role-change actions (owner only)
- **API Keys Tab**:
  - List of API keys with status, creation date, last used, requests count
  - Generate new key button
  - Actions per key: Deactivate, rotate, delete (owner only)

### **5. Metrics/Analytics Dashboard**
- Date range picker
- Granularity selector (minute/hour/day) for time series
- **Summary Cards**:
  - Total requests, avg response time, error rate, requests/min, slowest/fastest
- **Time Series Chart**: Configurable (request count or avg response time)
- **Endpoint Performance Table**: Sortable, paginated
- Export option (PDF/CSV if needed)

### **6. API Key Creation Modal/Page**
- Form: Name, expiration date
- Submit → Display key once with copy button
- Warning: "Save securely, won't be shown again"
- Confirmation dialog to proceed

### **7. User Profile** (Simple)
- Display: Email, full name, created_at
- Edit: Full name (optional)
- Logout button
- Possibly: Change password

---

## 5. Key UI Considerations

### **Data Display**

**Pagination:**
- Lists (projects, members, API keys, metrics) are paginated
- Default page size: 20 items
- Show: Current page, total count, next/previous navigation
- Optional: Jump to page input

**Date Ranges:**
- Use calendar picker for intuitive selection
- Defaults: Last 7 days, last 30 days, last 24 hours presets
- Constraint: Max 60 days, min 1 minute
- Show: Date range in readable format (e.g., "Jan 31, 2026 - Feb 26, 2026")

**Time Series Charts:**
- Interactive (hover for values)
- Switchable granularity (minute/hour/day)
- Multiple series (request count + avg response time as overlay or tabs)
- Responsive to date range changes

**Endpoint Table:**
- Sortable columns (request count, avg response time, error rate, etc.)
- Large datasets (100+ endpoints possible)
- Paginated with good sorting UX

---

### **Copy/Paste Interactions**

**API Key Display:**
- Large, monospace font
- Copy to clipboard button (with feedback: "Copied!" confirmation)
- User cannot see key again—reinforce this in UX

**Project Key:**
- Also show with copy button for SDK configuration reference

---

### **Error Handling & Validation**

**Real-Time Validation:**
- Email format, password strength (show meter/requirements)
- Unique project names (per user)
- Date range constraints (min 1 min, max 60 days)

**Error Messages:**
- Friendly, actionable (not technical)
- Examples:
  - "Email already registered"
  - "Project name already exists"
  - "Invalid date range (max 60 days)"
  - "Account locked due to failed login attempts. Try again in 15 minutes."

**Rate Limit Messaging:**
- If user hits rate limit: "Too many requests. Please wait a moment and try again."

---

### **Permission-Based UI**

**Owner Only:**
- Edit project settings (name, description, active/inactive)
- Delete project
- Manage members (add, remove, change role)
- Generate/rotate/delete API keys
- Cannot edit or delete if viewer role

**Member Only:**
- View project and metrics
- Cannot see API keys or members (or see but no actions)
- Cannot edit project settings

**Viewer Only:**
- View metrics dashboard only
- No access to project settings, members, or API keys

**Unauthenticated:**
- Only see landing page, login, signup

---

### **Real-Time & Refresh**

- Metrics dashboard can auto-refresh (e.g., every 5-10 seconds) or manual refresh button
- Summary stats update when date range changes
- No real-time streaming required (polling is sufficient)

---

## 6. API Response Examples (High Level)

### **Project List**
```
[
  {
    id: "uuid",
    name: "Production API",
    project_key: "production-api-a1b2",
    description: "Main production service",
    is_active: true,
    created_at: "2026-01-01T12:00:00Z"
  }
]
```

### **API Key**
```
{
  id: "uuid",
  key: "sk_live_abc123...",  // Shown only on creation
  name: "Prod Server",
  is_active: true,
  created_at: "2026-01-20T10:00:00Z",
  last_used_at: "2026-02-25T15:30:00Z",
  expires_at: "2026-04-30T00:00:00Z",
  total_requests: 15420
}
```

### **Metrics Summary**
```
{
  request_count: 10542,
  avg_response_time_ms: 145.32,
  requests_per_minute: 7.3,
  error_count: 42,
  error_rate: 0.4,
  slowest_request_ms: 2341.5,
  fastest_request_ms: 12.1
}
```

### **Time Series Data**
```
[
  {
    timestamp: "2026-02-26T10:00:00Z",
    request_count: 150,
    avg_response_time_ms: 124.5,
    error_count: 2
  }
]
```

### **Endpoint Stats**
```
[
  {
    url_path: "/api/v1/users",
    method: "GET",
    request_count: 520,
    avg_response_time_ms: 112.4,
    error_count: 5,
    error_rate: 0.96,
    slowest_request_ms: 890.0,
    fastest_request_ms: 45.2
  }
]
```

---

## 7. Important Constraints & Edge Cases

### **Security & Privacy**

- API keys are **never shown after creation** (except during creation flow)
- IPs are **hashed** server-side for privacy (not shown in UI)
- Users can only see projects they own or are members of
- Viewers cannot access project settings or invite members

### **Rate Limits (For UX Awareness)**

- Registration: 5 attempts/minute per IP
- Login: 10 attempts/minute per IP (account lockout after 5 failures, 15 min window)
- Generate API key: 20 per minute
- View metrics: 60 requests/minute per user
- API key recording (SDK side): 100 metrics/minute per project

### **Date Range Constraints**

- Max range: 60 days
- Min range: 1 minute
- End date must be ≥ start date
- Future dates should be blocked

### **Project Key**

- Auto-generated (e.g., `production-api-a1b2`)
- Immutable
- Unique across system
- Show it in UI for copy-paste into SDK config

### **API Key Expiration**

- Default: 90 days
- Can be set to `null` (no expiration)
- Expired keys are rejected at tracking endpoint
- UI should show status (active, inactive, expired)

### **Metrics Volume**

- Projects can accumulate millions of metrics
- Time series/endpoint views are aggregated (not raw records in most views)
- Pagination is essential for scalability

---

## 8. User Personas

### **Persona 1: DevOps Engineer (Project Owner)**
- Creates projects for services
- Generates API keys for different environments (prod, staging)
- Monitors metrics to catch performance regressions
- Invites team members to share dashboards

### **Persona 2: Backend Developer (Member)**
- Has access to project metrics
- Uses to debug slow endpoints
- Cannot generate keys or manage team (owner-only actions)

### **Persona 3: Manager/Team Lead (Viewer)**
- Read-only access to analytics
- Cannot access settings or generate keys
- Views high-level metrics and trends

---

## 9. Success Metrics / KPIs

- **Sign-up to first API key**: < 5 minutes
- **Time to view first metrics**: < 15 minutes (after SDK integration)
- **Dashboard load time**: < 2 seconds
- **Charts responsiveness**: Smooth, no lag on interaction
- **Copy button**: One-click, clear feedback

---

## 10. Technical Notes for Frontend

### **Authentication**

- Store JWT tokens (access + refresh) in secure storage (httpOnly cookies preferred, or secure storage if SPA)
- Refresh tokens automatically when expired (middleware or interceptor pattern)
- Include `Authorization: Bearer <token>` header in all authenticated requests
- Handle 401 responses by redirecting to login

### **API Base URL**

- Typically: `http://localhost:8000/api/v1` (local dev)
- Production: `https://api.yourdomain.com/api/v1`

### **API Key Recording**

- SDK/application sends metrics to: `POST /api/v1/track`
- Header: `X-API-Key: sk_live_...`
- This is NOT a user-facing feature; document for SDK users

### **Async Considerations**

- Backend is fully async; no performance bottlenecks expected
- Network latency will be the constraint (typical RTT 100-500ms)
- Metrics endpoints support pagination; implement lazy-loading/infinite scroll for large datasets

### **Internationalization (i18n)**

- No specific requirements mentioned; assume English for now
- Date formatting: ISO 8601 from backend, localize in frontend per user preference

---

## Summary

This is a **project analytics SaaS platform** with:
- ✅ Multi-tenant project management
- ✅ Secure API key generation & tracking
- ✅ Real-time metrics aggregation
- ✅ Role-based team collaboration
- ✅ Analytics dashboards with charts and tables
- ✅ Production-grade security (Argon2 hashing, JWT, rate limiting, timing attack prevention)

**Core UX**: Intuitive onboarding → Create project → Generate key → Ship SDK → Monitor metrics → Collaborate with team.

**Design Focus Areas**:
1. Clear visual hierarchy for metrics (summary cards → charts → tables)
2. Copy-paste UX for API keys and project keys (critical interaction)
3. Intuitive date/granularity pickers
4. Permission-based UI rendering (owner vs. member vs. viewer)
5. Responsive tables for endpoint performance data
6. Smooth chart interactions for time-series exploration
7. Error messages that guide users to solutions
