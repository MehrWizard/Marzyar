<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar" target="_blank" rel="noopener noreferrer">
    <img width="160" height="160" src="docs/assets/marzyar.png" alt="Marzyar Logo">
  </a>
</p>

<h1 align="center">Marzyar</h1>

<p align="center">
  基于 <a href="https://github.com/gozargah/marzban">Marzban</a> 与 <a href="https://github.com/MehrWizard/Marzdar">Marzdar</a> 的 100% 兼容无缝分支，具备完整网页 UI、原生分销商配额管理、用户数上限限制、超售模式与入站协议控制。
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

## 什么是 Marzyar？

**Marzyar** 是 **Marzdar** 与 **Marzban** 的分销商原生演进版本。

不同于修改核心表结构的第三方分支，Marzyar **绝不破坏基础数据库结构** (`admins`, `users`)，不增加有风险的 Alembic 迁移，确保在 Marzban、Marzdar 与 Marzyar 之间 **100% 双向安全互换**：

1. **用户账户数量上限 (Slots)**：限制每个分销商管理员可创建的用户账号数量。
2. **流量配额与超售控制**：
   - **统一消耗限制**：在 *所有* 模式下，总消耗流量（`∑ active_usage + historical_resets_and_deletions`）永远不能超过管理员的 `traffic_limit`。
   - **严格模式（禁止超售）**：*额外* 限制已分配用户流量上限的总和（`∑ user.data_limit ≤ traffic_limit`）。分销商无法超额分配或创建无流量限制的账户。
   - **超售模式**：移除分配限制。分销商可以自由分配用户计划，直到实际消耗的流量达到配额上限。
   - **防绕过审计**：分销商无法通过重置或删除用户流量来逃避配额；所有历史消耗都会安全地累积到分销商的历史消耗计数器中。
3. **智能锁定状态机 (Locked State Machine)**：
   - 当分销商流量配额耗尽时，其活跃用户将被无损标记为锁定状态，并立即从 Xray 入站断开（即时断网）。
   - 核心 `users` 表数据完全保持完好。
   - 当超级管理员（Sudo）调大或重置分销商配额后，所有锁定用户立即解锁并自动重新接入 Xray。
4. **允许的入站协议限制**：可限制特定分销商仅能使用指定的协议或节点入站。
5. **顶部导航实时配额组件**：分销商登录后可在面板顶部直观查看剩余名额与已用流量配额。

---

## 功能对比

| 功能模块 | Marzban (原版) | Marzdar | Marzyar |
| :--- | :--- | :--- | :--- |
| **兼容性与回滚** | 标准 | 100% 无缝兼容 | 100% 无缝兼容（核心表零改动） |
| **完整网页 UI** | ❌ 缺失多项功能 | ✅ 完整补齐 | ✅ 完整补齐 |
| **分销商用户名额上限** | ❌ 无 | ❌ 无 | ✅ 原生支持 |
| **流量配额与超售模式** | ❌ 无 | ❌ 无 | ✅ 原生支持（不可绕过） |
| **超额自动断网锁定** | ❌ 无 | ❌ 无 | ✅ 实时从 Xray 断开/恢复 |
| **限制分销商入站协议** | ❌ 无 | ❌ 无 | ✅ 原生支持 |
| **安全回滚至 Marzban** | - | ✅ 安全 | ✅ 100% 安全（无自定义 Alembic 破坏） |

---

## 安装与迁移配置

如需从 Marzban 或 Marzdar 切换到 Marzyar，仅需修改 `docker-compose.yml` 中的镜像：

```yaml
services:  
  marzban:  
    image: mehrwizard/marzyar:latest
```

随后执行更新：
```bash
marzban update
```

---

## Marzyar API 接口文档

除 Marzban 原生 API 外，Marzyar 提供了一组以 `/api/marzyar` 为前缀的专属 REST 接口，用于通过程序化方式管理分销商流量配额、用户配额上限、超售控制、允许的入站协议以及被锁定的用户。

交互式 Swagger/OpenAPI 文档可在面板的 `/docs` 路径直接在线查看与调试（需配置 `DOCS=true`）。

### 身份验证 (Authentication)
所有 Marzyar 接口均需要标准 Marzban OAuth2 Bearer 认证。请在 HTTP 请求头中携带 `Authorization`：
```http
Authorization: Bearer <access_token>
```
获取访问令牌：
```bash
curl -X POST "https://your-panel-domain:8000/api/admin/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

---

### 接口概览

| 请求方式 | 接口路径 (Endpoint) | 权限要求 | 接口说明 |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/marzyar/admins` | 仅限超级管理员 (Sudo) | 获取所有管理员的配额设置、已分配流量、实际消耗及锁定状态 |
| `GET` | `/api/marzyar/admin/{admin_identifier}/settings` | 仅限超级管理员 (Sudo) | 获取指定分销商管理员的配置与实时使用统计 |
| `PUT` | `/api/marzyar/admin/{admin_identifier}/settings` | 仅限超级管理员 (Sudo) | 修改分销商用户数上限、流量配额、超售模式及允许的入站协议 |
| `POST` | `/api/marzyar/admin/{admin_identifier}/reset_quota` | 仅限超级管理员 (Sudo) | 重置分销商已消耗的流量计数器并实时解锁其所有用户 |
| `GET` | `/api/marzyar/my_limits` | 所有已登录管理员 | 查询当前登录管理员自身的配额限制、剩余流量及可用协议 |
| `GET` | `/api/marzyar/locked_users` | 所有已登录管理员 | 查询因配额超限而被锁定的用户列表及锁定原因 |

---

### 1. 获取所有管理员的设置与配额
- **接口路径**: `GET /api/marzyar/admins`
- **权限要求**: 仅限超级管理员 (Sudo)。
- **说明**: 返回所有管理员的配置信息，包括用户上限、流量配额限制、已分配总流量、已消耗总流量以及锁定用户数。

#### 请求示例
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admins" \
  -H "Authorization: Bearer <token>"
```

#### 响应示例 (`200 OK`)
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

### 2. 获取指定管理员的设置
- **接口路径**: `GET /api/marzyar/admin/{admin_identifier}/settings`
- **权限要求**: 仅限超级管理员 (Sudo)。
- **路径参数**: `admin_identifier` (管理员数字 ID 如 `2` 或用户名如 `reseller1`)。
- **响应**: `MarzyarAdminSettingsResponse` 对象；若管理员不存在则返回 `404 Not Found`。

#### 请求示例
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admin/reseller1/settings" \
  -H "Authorization: Bearer <token>"
```

---

### 3. 修改分销商设置与配额
- **接口路径**: `PUT /api/marzyar/admin/{admin_identifier}/settings`
- **权限要求**: 仅限超级管理员 (Sudo)。
- **路径参数**: 管理员数字 ID 或用户名。
- **请求体 (JSON)**:
  | 字段 | 类型 | 必填 | 说明 |
  | :--- | :--- | :--- | :--- |
  | `users_limit` | 整数 或 `null` | 否 | 最大允许创建的用户数（`null` 表示不限制）。 |
  | `traffic_limit` | 整数 或 `null` | 否 | 流量配额，单位为 **字节 (bytes)**（`null` 表示不限制）。例如：`107374182400` 表示 100 GB。 |
  | `oversell_allowed` | 布尔值 | 否 | `false` = 严格模式（所有用户的额度总和不能超过 `traffic_limit`）；`true` = 超售模式（仅对实际消耗的总流量做上限控制）。 |
  | `allowed_inbounds` | 字符串数组 或 `null` | 否 | 允许使用的入站协议标签列表（`null` 表示允许所有入站）。现有用户将被自动同步限制在指定入站内。 |

> **提示**: 更改设置后系统将立即重新审计配额：若调高配额或解锁限制，被锁定的用户会实时在 Xray 中恢复；若更改了允许的入站协议，也会立刻更新关联用户的入站权限。

#### 请求示例
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

---

### 4. 重置分销商流量配额计数器
- **接口路径**: `POST /api/marzyar/admin/{admin_identifier}/reset_quota`
- **权限要求**: 仅限超级管理员 (Sudo)。
- **说明**: 将分销商的历史消耗累计计数器归零，并立即将该分销商旗下所有被锁定的用户解锁并在 Xray 中恢复连通。

#### 请求示例
```bash
curl -X POST "https://your-panel-domain:8000/api/marzyar/admin/reseller1/reset_quota" \
  -H "Authorization: Bearer <token>"
```

---

### 5. 获取当前管理员自身的配额 (Self-Service)
- **接口路径**: `GET /api/marzyar/my_limits`
- **权限要求**: 所有已登录管理员（超级管理员与分销商均可）。
- **说明**: 返回当前发起请求的管理员自身的配额状态、剩余名额、实际消耗与可用入站。非常适合分销商自主查询客户端或对接机器人。

#### 请求示例
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/my_limits" \
  -H "Authorization: Bearer <token>"
```

#### 响应示例 (`200 OK`)
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

### 6. 查询被锁定的用户列表
- **接口路径**: `GET /api/marzyar/locked_users`
- **权限要求**: 所有已登录管理员。
  - **超级管理员 (Sudo)**: 可查看全平台所有分销商名下被锁定的用户。
  - **分销商管理员**: 仅能查看自己名下被锁定的用户。
- **说明**: 列出当前因分销商配额耗尽而暂时断开 Xray 连接的用户，包含锁定时间与原因。

#### 请求示例
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/locked_users" \
  -H "Authorization: Bearer <token>"
```

#### 响应示例 (`200 OK`)
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

## 赞助支持 (Donation)

如果您觉得 Marzyar 对您有所帮助：

- [通过 MehrNet 支付网关赞助](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## 开源协议

Marzyar 遵循 [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE) 开源协议。

