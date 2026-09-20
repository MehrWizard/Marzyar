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
2. **流量配额与超售管理 (Oversell)**：
   - **严格模式（禁止超售）**：配额限制分销商名下所有用户分配的额度总和 ($\sum \text{user.data\_limit} \le \text{traffic\_limit}$)。
   - **超售模式**：配额限制实际已消耗的总流量 ($\sum \text{user.used\_traffic} + \text{历史重置} \le \text{traffic\_limit}$)。
   - **安全防绕过计量**：普通管理员重置用户流量并不能重置其自身的已用配额，重置的流量会安全累加至分销商配额计数器中。
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

## 赞助支持 (Donation)

如果您觉得 Marzyar 对您有所帮助：

- [通过 MehrNet 支付网关赞助](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## 开源协议

Marzyar 遵循 [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE) 开源协议。
