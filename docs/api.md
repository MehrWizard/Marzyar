# Marzyar REST API Reference

In addition to standard upstream Marzban APIs, Marzyar provides dedicated REST endpoints under the `/api/marzyar` prefix for managing reseller quotas, user slot limits, overselling modes, allowed inbounds, and locked users.

Interactive Swagger/OpenAPI documentation is also available directly in your browser at `/docs` (when enabled via `DOCS=true`).

---

## Authentication

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

## Endpoint Summary

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/marzyar/admins` | Sudo Only | List settings, limits, quota usage, and lock counts for all admins |
| `GET` | `/api/marzyar/admin/{admin_identifier}/settings` | Sudo Only | Retrieve Marzyar settings and real-time usage for a specific admin |
| `PUT` | `/api/marzyar/admin/{admin_identifier}/settings` | Sudo Only | Modify reseller limits, traffic quota, oversell flag, and allowed inbounds |
| `POST` | `/api/marzyar/admin/{admin_identifier}/reset_quota` | Sudo Only | Reset an admin's accumulated consumed quota counter and unlock their users |
| `GET` | `/api/marzyar/my_limits` | All Admins | Retrieve the currently logged-in admin's own limits and quota status |
| `GET` | `/api/marzyar/locked_users` | All Admins | List currently locked users with lock reasons and timestamps |

---

## Detailed Endpoints

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
