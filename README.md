<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar" target="_blank" rel="noopener noreferrer">
    <img width="160" height="160" src="docs/assets/marzyar.png" alt="Marzyar Logo">
  </a>
</p>

<h1 align="center">Marzyar</h1>

<p align="center">
  A 100% compatible drop-in fork of <a href="https://github.com/gozargah/marzban">Marzban</a> and <a href="https://github.com/MehrWizard/Marzdar">Marzdar</a> featuring a completed UI plus native reseller quotas, user limits, overselling controls, and inbound restrictions.
</p>

<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar/actions/workflows/build.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/MehrWizard/Marzyar/build.yml?style=flat-square&logo=github" alt="Build Status" />
  </a>
  <a href="https://hub.docker.com/r/mehrwizard/marzyar" target="_blank">
    <img src="https://img.shields.io/docker/pulls/mehrwizard/marzyar?style=flat-square&logo=docker" alt="Docker Pulls" />
  </a>
  <a href="https://github.com/MehrWizard/Marzyar/stargazers">
    <img src="https://img.shields.io/github/stars/MehrWizard/Marzyar?style=flat-square&logo=github" alt="Stars" />
  </a>
  <a href="./LICENSE">
    <img src="https://img.shields.io/github/license/MehrWizard/Marzyar?style=flat-square" alt="License" />
  </a>
  <a href="https://t.me/MehrRoom" target="_blank">
    <img src="https://img.shields.io/badge/Telegram-Group-blue?style=flat-square&logo=telegram" alt="Telegram Group" />
  </a>
  <a href="https://x.com/MehrWizard" target="_blank">
    <img src="https://img.shields.io/badge/X-@MehrWizard-black?style=flat-square&logo=x" alt="X / Twitter" />
  </a>
</p>

<p align="center">
  <a href="./README.md">English</a>
  /
  <a href="./README-fa.md">فارسی</a>
  /
  <a href="./README-zh-cn.md">简体中文</a>
  /
  <a href="./README-ru.md">Русский</a>
</p>

<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar" target="_blank" rel="noopener noreferrer">
    <img src="https://github.com/MehrWizard/Marzyar/raw/master/docs/assets/preview.png" alt="Marzyar Preview" width="800" height="auto">
  </a>
</p>

---

## What is Marzyar?

**Marzyar** is the reseller-ready evolution of **Marzdar** and **Marzban**.

While **Marzdar** focuses on completing the missing user interface elements of upstream Marzban, **Marzyar** integrates native reseller management capabilities directly into the core engine while guaranteeing **zero database schema disruption** and **100% bidirectional migration safety**:

1. **User Account Limits**: Cap the number of user accounts a reseller admin can create.
2. **Bandwidth Quotas & Oversell Controls**:
   - **Unified Consumed Limit**: In *all* modes, total consumed bandwidth (`∑ active_usage + historical_resets_and_deletions`) can never exceed the admin's `traffic_limit`.
   - **Strict Mode (No Oversell)**: *Additionally* limits the sum of allocated user data limits (`∑ user.data_limit ≤ traffic_limit`). Resellers cannot over-allocate or create accounts with unlimited bandwidth.
   - **Oversell Mode**: Removes the allocation limit. Resellers can allocate user plans freely until actual traffic consumed reaches the quota limit.
   - **Non-bypassable Accounting**: Reseller admins cannot reset or delete users to escape their quota; past usage is securely accumulated into the reseller's historical consumption counter.
3. **The "Locked" State Machine**:
   - When an admin exhausts their quota, their active users are non-destructively marked as `locked` and detached from Xray inbounds (traffic blocked immediately).
   - Core `users` table records remain untouched.
   - When Sudo resets or increases the reseller's quota, all locked users are automatically unlocked and restored to Xray in real-time.
4. **Allowed Inbounds**: Restrict each reseller to specific protocols and inbounds (e.g., VMess TCP only).
5. **Dashboard Header Reseller Widget**: Compact live indicators displaying remaining slots and quota for logged-in reseller admins.

---

## Setup & Migration

### Migrating from Marzban or Marzdar

Simply update the image in `docker-compose.yml`:

```yaml
services:  
  marzban:  
    image: mehrwizard/marzyar:latest
```

Then restart:
```bash
marzban update
```

---

## API Endpoints

In addition to standard upstream Marzban APIs, Marzyar provides dedicated REST endpoints under the `/api/marzyar` prefix for managing reseller quotas, user slot limits, overselling modes, allowed inbounds, and locked users.

Interactive Swagger/OpenAPI documentation is also available directly at `/docs` (when enabled via `DOCS=true`).

### Authentication
All Marzyar endpoints require standard Marzban OAuth2 Bearer authentication. Include the access token in the `Authorization` HTTP header:
```http
Authorization: Bearer <your_access_token>
```
To obtain an access token:
```bash
curl -X POST "https://your-panel-domain:8000/api/admin/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

---

### Endpoint Summary

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/marzyar/admins` | Sudo Only | List settings, limits, quota usage, and lock counts for all admins |
| `GET` | `/api/marzyar/admin/{admin_identifier}/settings` | Sudo Only | Retrieve Marzyar settings and real-time usage for a specific admin |
| `PUT` | `/api/marzyar/admin/{admin_identifier}/settings` | Sudo Only | Modify reseller limits, traffic quota, oversell flag, and allowed inbounds |
| `POST` | `/api/marzyar/admin/{admin_identifier}/reset_quota` | Sudo Only | Reset an admin's accumulated consumed quota counter and unlock their users |
| `GET` | `/api/marzyar/my_limits` | All Admins | Retrieve the currently logged-in admin's own limits and quota status |
| `GET` | `/api/marzyar/locked_users` | All Admins | List currently locked users with lock reasons and timestamps |

---

### 1. List All Admins' Settings & Quotas
- **Endpoint**: `GET /api/marzyar/admins`
- **Permission**: Sudo Admin only (`403 Forbidden` if non-sudo).
- **Description**: Returns an array containing the configuration, real-time user counts, allocated bandwidth, cumulative consumed bandwidth, and lock states for every admin.

#### Example Request
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admins" \
  -H "Authorization: Bearer <token>"
```

#### Example Response (`200 OK`)
```json
[
  {
    "admin_id": 2,
    "username": "reseller1",
    "is_sudo": false,
    "users_limit": 50,
    "traffic_limit": 107374182400,
    "oversell_allowed": false,
    "allowed_inbounds": ["VLESS TCP REALITY", "VMess TCP"],
    "quota_used_traffic": 15000000000,
    "current_users_count": 12,
    "current_allocated_traffic": 64424509440,
    "current_consumed_traffic": 21474836480,
    "is_quota_exceeded": false,
    "is_user_limit_exceeded": false,
    "is_allocation_limit_reached": false,
    "locked_users_count": 0
  }
]
```

---

### 2. Get Specific Admin Settings
- **Endpoint**: `GET /api/marzyar/admin/{admin_identifier}/settings`
- **Permission**: Sudo Admin only.
- **Path Parameters**:
  - `admin_identifier` (integer or string): Admin numeric ID (e.g. `2`) or username (e.g. `reseller1`).
- **Response**: `200 OK` with single `MarzyarAdminSettingsResponse` object; `404 Not Found` if admin does not exist.

#### Example Request
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admin/reseller1/settings" \
  -H "Authorization: Bearer <token>"
```

---

### 3. Update Admin Settings & Limits
- **Endpoint**: `PUT /api/marzyar/admin/{admin_identifier}/settings`
- **Permission**: Sudo Admin only.
- **Path Parameters**:
  - `admin_identifier`: Admin numeric ID or username.
- **Request Body** (`application/json`):
  | Field | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `users_limit` | integer \| null | No | Max number of user accounts allowed (`null` for unlimited). |
  | `traffic_limit` | integer \| null | No | Traffic quota in **bytes** (`null` for unlimited). Example: `107374182400` for 100 GB. |
  | `oversell_allowed` | boolean | No | `false` = Strict mode (sum of allocated limits capped by `traffic_limit`); `true` = Oversell mode (only actual consumed traffic capped). |
  | `allowed_inbounds` | array of strings \| null | No | Array of allowed inbound tags (`null` for all inbounds). Existing users are automatically restricted to this list. |

> **Note**: Updating settings immediately re-audits quotas and allowed inbounds: if limits were raised, locked users are automatically unlocked in real-time; if inbounds were modified, users are re-synced in Xray immediately.

#### Example Request
```bash
curl -X PUT "https://your-panel-domain:8000/api/marzyar/admin/reseller1/settings" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "users_limit": 100,
    "traffic_limit": 214748364800,
    "oversell_allowed": true,
    "allowed_inbounds": ["VLESS TCP REALITY"]
  }'
```

#### Example Response (`200 OK`)
Returns the updated `MarzyarAdminSettingsResponse`.

---

### 4. Reset Admin Quota Counter
- **Endpoint**: `POST /api/marzyar/admin/{admin_identifier}/reset_quota`
- **Permission**: Sudo Admin only.
- **Description**: Resets the reseller admin's accumulated consumption counter to zero and automatically unlocks and restores all of their locked users in Xray in real-time.

#### Example Request
```bash
curl -X POST "https://your-panel-domain:8000/api/marzyar/admin/reseller1/reset_quota" \
  -H "Authorization: Bearer <token>"
```

#### Example Response (`200 OK`)
Returns the updated `MarzyarAdminSettingsResponse` with `current_consumed_traffic` reset and `locked_users_count: 0`.

---

### 5. Get Current Admin's Limits (Self-Service)
- **Endpoint**: `GET /api/marzyar/my_limits`
- **Permission**: Any authenticated admin (Sudo or Reseller).
- **Description**: Returns the calling admin's own user slot limits, quota consumption, allocated traffic, oversell setting, allowed inbounds, and whether any limits have been reached. Ideal for reseller client apps and bots.

#### Example Request
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/my_limits" \
  -H "Authorization: Bearer <token>"
```

#### Example Response (`200 OK`)
```json
{
  "username": "reseller1",
  "is_sudo": false,
  "users_limit": 50,
  "traffic_limit": 107374182400,
  "oversell_allowed": false,
  "allowed_inbounds": ["VLESS TCP REALITY"],
  "current_users_count": 12,
  "current_allocated_traffic": 64424509440,
  "current_consumed_traffic": 21474836480,
  "is_quota_exceeded": false,
  "is_user_limit_exceeded": false,
  "is_allocation_limit_reached": false,
  "locked_users_count": 0
}
```

---

### 6. List Locked Users
- **Endpoint**: `GET /api/marzyar/locked_users`
- **Permission**: Any authenticated admin.
  - **Sudo Admin**: Views all locked users across all reseller accounts.
  - **Reseller Admin**: Views only locked users created by their own account.
- **Description**: Lists all user accounts temporarily locked and detached from Xray due to admin quota exhaustion, along with lock timestamps and reasons.

#### Example Request
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/locked_users" \
  -H "Authorization: Bearer <token>"
```

#### Example Response (`200 OK`)
```json
[
  {
    "user_id": 42,
    "username": "client_alice",
    "admin_username": "reseller1",
    "locked_at": "2026-10-20T14:30:00",
    "lock_reason": "Admin quota exceeded"
  }
]
```

---

## Feature Comparison

| Feature | Marzban (Upstream) | Marzdar | Marzyar |
| :--- | :--- | :--- | :--- |
| **Compatibility** | Upstream | 100% Drop-in | 100% Drop-in (Zero DB alterations) |
| **Complete Web UI** | ❌ (CLI/API only for many features) | ✅ Complete | ✅ Complete |
| **ASGI Web Engine** | Uvicorn (Python) | ⚡ **Granian (Rust/Tokio) + Uvicorn fallback** | ⚡ **Granian (Rust/Tokio) + Uvicorn fallback** |
| **Subscription Caching** | ❌ None (recomputed per poll) | ⚡ **In-Memory Thread-Safe TTL Cache** | ⚡ **In-Memory Thread-Safe TTL Cache** |
| **Database Indexing** | Standard | ⚡ **Strategic Composite Indexes** | ⚡ **Strategic Composite Indexes** |
| **Reseller User Limits** | ❌ None | ❌ None | ✅ Native & UI-managed |
| **Bandwidth Quota & Oversell** | ❌ None | ❌ None | ✅ Native & Non-bypassable |
| **Auto-Lock on Over-Quota** | ❌ None | ❌ None | ✅ Real-time Xray detach/restore |
| **Allowed Inbounds Filtering**| ❌ None | ❌ None | ✅ Admin-level restriction |
| **Bidirectional Rollback** | Baseline | ✅ Safe | ✅ 100% Safe (No custom Alembic revisions) |

---

## Performance & Real-World Telemetry Benchmarks

Both **Marzdar** and **Marzyar** incorporate high-performance architectural optimizations engineered for large-scale production panels handling hundreds of concurrent VPN clients:

1. **Rust-Powered ASGI Engine ([Granian](https://github.com/emmett-framework/granian))**: Replaced standard Python Uvicorn with Granian, an ultra-fast HTTP server utilizing the Tokio runtime and PyO3 bindings for high-throughput asynchronous networking with significantly lower CPU overhead.
2. **Subscription In-Memory Response Caching**: Subscriptions are served from a bounded thread-safe memory cache (30s TTL) with instant automated invalidation whenever a user's configuration, status, or quota changes. Bypasses repetitive template rendering, cryptographic JWT operations, and redundant MySQL queries on continuous client polling.
3. **Strategic Composite Database Indexing**: Added critical compound indexes on high-frequency tables (`users(online_at)`, `users(created_at)`, `node_user_usages(node_id, created_at)`, and `node_usages(node_id, created_at)`), eliminating sequential table scans and lock waits during node statistics aggregation.
4. **Node Session Lifecycle & Stats Collection Resiliency**: Isolated node synchronization cycles, bounded gRPC timeouts, and transactional error handling ensure node stats collection never hangs or impairs API responsiveness.

<p align="center">
  <img src="docs/assets/architecture.png" alt="Marzdar and Marzyar Architecture Flowchart" width="850" height="auto">
</p>

### Key Performance Highlights:
- ⚡ **8.6x Faster Median Response**: Median (p50) subscription latency reduced from 46.27 ms to 5.37 ms (**88.4% faster**).
- 🚀 **+2,235% Higher Concurrency Throughput**: Handled 775.2 req/s vs 33.2 req/s under sustained 15-worker load (**23.3x total capacity**).
- ⚡ **96.1% Latency Drop Under Concurrency Load**: Average latency under sustained heavy stress dropped from 447.66 ms to 17.53 ms (**25.5x faster**).
- 🗄️ **31.7% Database Burden Reduction**: MySQL peak CPU spikes reduced from 53.62% down to 36.64% thanks to in-memory caching and compound indexes.
- 📦 **22.8x Greater Request Servicing**: Serviced 7,764 complete requests in a 10-second burst window vs. 341 on baseline Marzban.
- 🛡️ **25.6% Reduction in Tail Spikes**: Max latency spike dropped from 604.36 ms down to 449.63 ms under continuous saturation.

---

### Detailed Benchmark Reports

<details open>
<summary><b>1. Subscription Response Latency (8.6x Faster Median)</b></summary>

<p align="center">
  <img src="docs/assets/benchmark-latency.png" alt="Subscription Response Latency Benchmark" width="850" height="auto">
</p>

Measured across high-frequency production telemetry on a live production server under active user traffic and continuous query load:

| Latency Percentile | Marzban (Original / Baseline) | Marzdar & Marzyar (Optimized) | Improvement |
| :--- | :--- | :--- | :--- |
| **p50 (Median)** | **46.27 ms** | **5.37 ms** | **-88.4% (8.6x faster)** |
| **p75** | **60.89 ms** | **8.39 ms** | **-86.2% (7.3x faster)** |
| **p90** | **76.21 ms** | **13.81 ms** | **-81.9% (5.5x faster)** |
| **p95** | **93.08 ms** | **23.35 ms** | **-74.9% (4.0x faster)** |
| **Mean (Average)** | **53.38 ms** | **12.25 ms** | **-77.1% (4.4x faster)** |

```
Subscription Latency Percentiles (Lower is better):

p50 Median:
  Marzban:            ████████████████████████ 46.27 ms
  Marzdar & Marzyar:  ███ 5.37 ms (-88.4%)

p95 Tail:
  Marzban:            ██████████████████████████████████████████████ 93.08 ms
  Marzdar & Marzyar:  ████████████ 23.35 ms (-74.9%)

Mean Latency:
  Marzban:            ███████████████████████████ 53.38 ms
  Marzdar & Marzyar:  ██████ 12.25 ms (-77.1%)
```
</details>

<details>
<summary><b>2. Production Stability & Resource Efficiency</b></summary>

<p align="center">
  <img src="docs/assets/benchmark-stability.png" alt="Production Stability & CPU Benchmark" width="850" height="auto">
</p>

Continuous metrics recorded under active live production load:

| Telemetry Metric | Marzban (Original / Baseline) | Marzdar & Marzyar (Optimized) | Impact |
| :--- | :--- | :--- | :--- |
| **Peak MySQL CPU Spike** | 53.62% | **36.64%** | **31.7% lower DB query burden** |
| **Max Tail Latency Spike** | 604.36 ms | **449.63 ms** | **25.6% lower tail spike** |
| **Panel Memory Footprint** | ~125 MB | ~175 MB | Highly efficient bounded memory cache |
</details>

<details>
<summary><b>3. High-Concurrency Stress Benchmark (+2,235% Throughput Capacity)</b></summary>

<p align="center">
  <img src="docs/assets/benchmark-stress.png" alt="High Concurrency Stress Benchmark" width="850" height="auto">
</p>

Standardized burst test evaluating subscription endpoint capacity under sustained concurrency (15 worker threads, 10 seconds continuous load):

| Benchmark Metric | Marzban (Baseline: Uvicorn / No Cache) | Marzdar & Marzyar (Granian + Cache + Indexes) | Impact |
| :--- | :--- | :--- | :--- |
| **Throughput (Requests/sec)** | **33.2 req/s** | **775.2 req/s** | **+2,235% (23.3x Throughput)** 🚀 |
| **Mean Latency under Load** | **447.66 ms** | **17.53 ms** | **-96.1% Latency (25.5x faster)** |
| **p50 Latency under Load** | **431.47 ms** | **14.34 ms** | **-96.7% Latency (30.1x faster)** |
| **p95 Latency under Load** | **695.22 ms** | **38.62 ms** | **-94.4% Latency (18.0x faster)** |
| **p99 Latency under Load** | **767.31 ms** | **55.85 ms** | **-92.7% Latency (13.7x faster)** |
| **Total Completed Requests (10s)**| 341 requests | **7,764 requests** | **22.8x Total Serviced Reqs** |

```
Concurrent Throughput (Higher is better):
  Marzban:            █ 33.2 req/s
  Marzdar & Marzyar:  ███████████████████████ 775.2 req/s (+2,235% / 23.3x)

Latency Under Stress Load (Lower is better):
  Marzban:            ████████████████████████ 447.66 ms
  Marzdar & Marzyar:  █ 17.53 ms (-96.1% / 25.5x faster)
```
</details>

<details>
<summary><b>4. Comprehensive Benchmark Dashboard (Combined Overview)</b></summary>

<p align="center">
  <img src="docs/assets/benchmark.png" alt="Comprehensive Benchmark Dashboard" width="900" height="auto">
</p>
</details>

---

## Donation

If you find Marzyar useful, you can support its ongoing development:

- [Donate via MehrNet Gateway](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## License

Marzyar is licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).
