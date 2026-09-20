<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar" target="_blank" rel="noopener noreferrer">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
      <img width="160" height="160" src="docs/assets/logo-light.svg" alt="Marzyar Logo">
    </picture>
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

## Donation

If you find Marzyar useful, you can support its ongoing development:

- [Donate via MehrNet Gateway](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## License

Marzyar is licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).
