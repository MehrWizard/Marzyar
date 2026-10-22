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
- ⚡ **1.79x Faster Median Response**: Median (p50) subscription latency reduced from 46.27 ms to 25.84 ms (**44.2% faster**).
- 🚀 **+72.0% Higher Concurrency Throughput**: Handled 57.1 req/s vs 33.2 req/s under sustained 15-worker load (**1.72x total capacity**).
- 🛡️ **75.4% Elimination of Tail Latency Spikes**: Max latency spike dropped from 604.36 ms down to 148.94 ms.
- 📉 **50.6% Lower CPU Spikes**: Panel CPU load peaks reduced from 139.3% down to 68.9%; sustained p99 CPU cut by **55.4%**.
- 🗄️ **46.9% Database Burden Reduction**: MySQL peak CPU spikes reduced from 53.6% down to 28.5% thanks to in-memory caching and compound indexes.
- ⚡ **41.6% Latency Reduction Under Load**: Average latency under sustained heavy stress dropped from 447.66 ms to 261.24 ms.

---

### Detailed Benchmark Reports

<details open>
<summary><b>1. Subscription Response Latency (1.79x Faster Median)</b></summary>

<p align="center">
  <img src="docs/assets/benchmark-latency.png" alt="Subscription Response Latency Benchmark" width="850" height="auto">
</p>

Measured across a 4-hour telemetry window on a live high-traffic production server with ~80 concurrently active users (~969 samples total):

| Latency Percentile | Marzban (Original / Baseline) | Marzdar & Marzyar (Optimized) | Improvement |
| :--- | :--- | :--- | :--- |
| **p50 (Median)** | **46.27 ms** | **25.84 ms** | **-44.2% (1.79x faster)** |
| **p75** | **60.89 ms** | **43.38 ms** | **-28.8% faster** |
| **p90** | **76.21 ms** | **60.86 ms** | **-20.1% faster** |
| **p95** | **93.08 ms** | **72.73 ms** | **-21.9% faster** |
| **p99** | **173.22 ms** | **122.40 ms** | **-29.3% faster** |
| **Mean (Average)** | **53.38 ms** | **34.48 ms** | **-35.4% faster** |
| **Max Peak Latency Spike** | **604.36 ms** | **148.94 ms** | **-75.4% (No tail lag)** |

```
Subscription Latency Percentiles (Lower is better):

p50 Median:
  Marzban:            ████████████████████████ 46.27 ms
  Marzdar & Marzyar:  █████████████ 25.84 ms (-44.2%)

p95 Tail:
  Marzban:            ██████████████████████████████████████████████ 93.08 ms
  Marzdar & Marzyar:  ████████████████████████████████████ 72.73 ms (-21.9%)

Max Tail Spike:
  Marzban:            ████████████████████████████████████████████████████████████ 604.36 ms
  Marzdar & Marzyar:  ███████████████ 148.94 ms (-75.4%)
```
</details>

<details>
<summary><b>2. Production Stability & Resource Efficiency (75% Spike Reduction)</b></summary>

<p align="center">
  <img src="docs/assets/benchmark-stability.png" alt="Production Stability & CPU Benchmark" width="850" height="auto">
</p>

Continuous metrics recorded under live production load:

| Telemetry Metric | Marzban (Original / Baseline) | Marzdar & Marzyar (Optimized) | Impact |
| :--- | :--- | :--- | :--- |
| **Peak Panel CPU Spike** | 139.34% | **68.86%** | **50.6% reduction in CPU spikes** |
| **p99 Panel CPU** | 91.30% | **40.73%** | **55.4% lower CPU under load** |
| **Peak MySQL CPU Spike** | 53.62% | **28.49%** | **46.9% lower DB query burden** |
| **Panel Memory Footprint** | ~125 MB | ~141 MB | Highly efficient bounded memory cache |
</details>

<details>
<summary><b>3. High-Concurrency Stress Benchmark (+72.0% Throughput Capacity)</b></summary>

<p align="center">
  <img src="docs/assets/benchmark-stress.png" alt="High Concurrency Stress Benchmark" width="850" height="auto">
</p>

Standardized burst test evaluating subscription endpoint capacity under sustained concurrency (15 worker threads, 10 seconds continuous load):

| Benchmark Metric | Marzban (Baseline: Uvicorn / No Cache) | Marzdar & Marzyar (Granian + Cache + Indexes) | Impact |
| :--- | :--- | :--- | :--- |
| **Throughput (Requests/sec)** | **33.2 req/s** | **57.1 req/s** | **+72.0% Throughput** 🚀 |
| **Mean Latency under Load** | **447.66 ms** | **261.24 ms** | **-41.6% Latency** |
| **p50 Latency under Load** | **431.47 ms** | **247.18 ms** | **-42.7% Latency** |
| **p95 Latency under Load** | **695.22 ms** | **390.20 ms** | **-43.9% Latency** |
| **p99 Latency under Load** | **767.31 ms** | **658.34 ms** | **-14.2% Latency** |
| **Total Completed Requests (10s)**| 341 requests | **578 requests** | **+69.5% Capacity** |

```
Concurrent Throughput (Higher is better):
  Marzban:            █████████████████████████████████ 33.2 req/s
  Marzdar & Marzyar:  ████████████████████████████████████████████████████████ 57.1 req/s (+72.0%)

Latency Under Stress Load (Lower is better):
  Marzban:            █████████████████████████████████████████████ 447.66 ms
  Marzdar & Marzyar:  ██████████████████████████ 261.24 ms (-41.6%)
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
