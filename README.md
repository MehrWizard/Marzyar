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

## Comparison

| Feature | Marzban (Upstream) | Marzdar | Marzyar |
| :--- | :--- | :--- | :--- |
| **Compatibility** | Upstream | 100% Drop-in | 100% Drop-in (Zero DB alterations) |
| **Complete Web UI** | ❌ (CLI/API only for many features) | ✅ Complete | ✅ Complete |
| **Reseller User Limits** | ❌ None | ❌ None | ✅ Native & UI-managed |
| **Bandwidth Quota & Oversell** | ❌ None | ❌ None | ✅ Native & Non-bypassable |
| **Auto-Lock on Over-Quota** | ❌ None | ❌ None | ✅ Real-time Xray detach/restore |
| **Allowed Inbounds Filtering**| ❌ None | ❌ None | ✅ Admin-level restriction |
| **Bidirectional Rollback** | Baseline | ✅ Safe | ✅ 100% Safe (No custom Alembic revisions) |

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

## Marzyar API Endpoints

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

## Donation

If you find Marzyar useful, you can support its ongoing development:

- [Donate via MehrNet Gateway](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## License

Marzyar is licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).
