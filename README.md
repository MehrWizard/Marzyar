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

It combines all completed web UI features of **Marzdar** with native, non-bypassable reseller management and high-performance Rust networking, guaranteeing **zero database schema disruption** and **100% bidirectional migration safety**:

1. **User Account Limits**: Cap the number of user accounts each reseller admin can create.
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
6. **High-Performance Rust Web Engine & Caching**: Powered by Granian (Tokio runtime) with thread-safe in-memory subscription caching and composite database indexes for ultra-low latency response times.

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

### Endpoint Summary

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/marzyar/admins` | Sudo Only | List settings, limits, quota usage, and lock counts for all admins |
| `GET` | `/api/marzyar/admin/{admin_identifier}/settings` | Sudo Only | Retrieve Marzyar settings and real-time usage for a specific admin |
| `PUT` | `/api/marzyar/admin/{admin_identifier}/settings` | Sudo Only | Modify reseller limits, traffic quota, oversell flag, and allowed inbounds |
| `POST` | `/api/marzyar/admin/{admin_identifier}/reset_quota` | Sudo Only | Reset an admin's accumulated consumed quota counter and unlock their users |
| `GET` | `/api/marzyar/my_limits` | All Admins | Retrieve the currently logged-in admin's own limits and quota status |
| `GET` | `/api/marzyar/locked_users` | All Admins | List currently locked users with lock reasons and timestamps |

👉 For full request/response schemas, JSON payloads, and curl examples, see the [Marzyar API Reference](docs/api.md).

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
- ⚡ **8.6x Faster Median Response**: Live telemetry median (p50) subscription latency reduced from 46.27 ms down to 5.37 ms (-88.4% lower latency).
- 🚀 **23.3x Cache Saturation Throughput**: Serviced **775.2 req/s** (7,764 requests in 10s) vs **33.2 req/s** (341 requests) under sustained 15-worker concurrency (+2,235% capacity via in-memory caching).
- ⚡ **96.1% Lower Latency Under Load**: Average latency under sustained heavy concurrency dropped from 447.66 ms down to 17.53 ms (25.5x faster response).
- 🗄️ **31.7% Lower Database Load**: MySQL peak CPU spikes reduced from 53.62% down to 36.64% under active query traffic thanks to in-memory caching and compound indexes.
- 🛡️ **25.6% Tail Spike Suppression**: Maximum latency spike suppressed from 604.36 ms down to 449.63 ms under continuous saturation.

<p align="center">
  <img src="docs/assets/benchmark.png" alt="Comprehensive Benchmark Dashboard" width="900" height="auto">
</p>

<details>
<summary><b>Detailed Metrics & Percentile Tables</b></summary>

#### 1. Subscription Response Latency (Live Production Telemetry)

| Latency Percentile | Marzban (Original / Baseline) | Marzdar & Marzyar (Optimized) | Improvement |
| :--- | :--- | :--- | :--- |
| **p50 (Median)** | **46.27 ms** | **5.37 ms** | **-88.4% (8.6x faster)** |
| **p75** | **60.89 ms** | **8.39 ms** | **-86.2% (7.3x faster)** |
| **p90** | **76.21 ms** | **13.81 ms** | **-81.9% (5.5x faster)** |
| **p95** | **93.08 ms** | **23.35 ms** | **-74.9% (4.0x faster)** |
| **Mean (Average)** | **53.38 ms** | **12.25 ms** | **-77.1% (4.4x faster)** |

#### 2. Production Stability & Resource Efficiency

| Telemetry Metric | Marzban (Original / Baseline) | Marzdar & Marzyar (Optimized) | Impact |
| :--- | :--- | :--- | :--- |
| **Peak MySQL CPU Spike** | 53.62% | **36.64%** | **31.7% lower DB query burden** |
| **Max Tail Latency Spike** | 604.36 ms | **449.63 ms** | **25.6% lower tail spike** |
| **Panel Memory Footprint** | ~125 MB | ~175 MB | Highly efficient bounded memory cache |

#### 3. High-Concurrency Stress & Cache Saturation (15 Workers, 10s Burst)

| Benchmark Metric | Marzban (Baseline: Uvicorn / No Cache) | Marzdar & Marzyar (Granian + Cache + Indexes) | Impact |
| :--- | :--- | :--- | :--- |
| **Throughput (Requests/sec)** | **33.2 req/s** | **775.2 req/s** | **+2,235% (23.3x Throughput)** 🚀 |
| **Mean Latency under Load** | **447.66 ms** | **17.53 ms** | **-96.1% Latency (25.5x faster)** |
| **p50 Latency under Load** | **431.47 ms** | **14.34 ms** | **-96.7% Latency (30.1x faster)** |
| **p95 Latency under Load** | **695.22 ms** | **38.62 ms** | **-94.4% Latency (18.0x faster)** |
| **p99 Latency under Load** | **767.31 ms** | **55.85 ms** | **-92.7% Latency (13.7x faster)** |
| **Total Completed Requests (10s)**| 341 requests | **7,764 requests** | **22.8x Total Serviced Reqs** |
</details>

---

## Donation

If you find Marzyar useful, you can support its ongoing development:

- [Donate via MehrNet Gateway](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## License

Marzyar is licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).
