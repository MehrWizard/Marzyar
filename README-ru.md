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
  100% совместимый drop-in форк <a href="https://github.com/gozargah/marzban">Marzban</a> и <a href="https://github.com/MehrWizard/Marzdar">Marzdar</a> с завершённым интерфейсом, лимитами для реселлеров, квотами трафика, режимом оверселлинга и ограничением протоколов.
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

## Что такое Marzyar?

**Marzyar** — это эволюция **Marzdar** и **Marzban** со встроенным нативным функционалом для реселлеров.

В отличие от сторонних форков, Marzyar **не изменяет базовые таблицы базы данных** (`admins`, `users`) и не создает ломающих миграций Alembic, гарантируя **100% безопасную обратную совместимость**:

1. **Лимит пользователей (Slots)**: Ограничение количества аккаунтов, которые может создать реселлер.
2. **Квоты трафика и Контроль оверселлинга**:
   - **Единый лимит потребления**: Во *всех* режимах общий потребленный трафик (`∑ active_usage + historical_resets_and_deletions`) никогда не может превысить `traffic_limit` администратора.
   - **Строгий режим (Без оверселлинга)**: *Дополнительно* ограничивает сумму выделенных лимитов данных пользователей (`∑ user.data_limit ≤ traffic_limit`). Реселлеры не могут выделять больше квоты или создавать аккаунты с безлимитным трафиком.
   - **Режим оверселлинга**: Снимает ограничение на выделение. Реселлеры могут свободно создавать тарифы до тех пор, пока фактический потребленный трафик не достигнет лимита квоты.
   - **Необходимый учет**: Реселлеры не могут обнулять или удалять пользователей для обхода квоты; прошлый трафик надежно сохраняется в историческом счетчике потребления реселлера.
3. **Автоматическая блокировка (Locked State Machine)**:
   - При превышении квоты активные пользователи реселлера переводятся в статус `locked` и немедленно отключаются от входящих подключений Xray.
   - Записи в таблице `users` не повреждаются.
   - При увеличении или сбросе квоты суперпользователем (Sudo) все пользователи мгновенно разблокируются и подключаются обратно к Xray.
4. **Разрешенные инбаунды**: Возможность ограничить каждого реселлера конкретными инбаундами и протоколами.
5. **Индикатор квоты в шапке панели**: Отображение оставшихся слотов и объема трафика в реальном времени.

---

## Сравнение

| Раздел | Marzban (Оригинал) | Marzdar | Marzyar |
| :--- | :--- | :--- | :--- |
| **Совместимость** | Стандарт | 100% совместимость | 100% совместимость (без изменения основных таблиц) |
| **Веб-интерфейс** | Неполный | ✅ Полный | ✅ Полный |
| **Лимит пользователей реселлера** | ❌ Нет | ❌ Нет | ✅ Встроен в UI |
| **Квоты трафика и оверселлинг** | ❌ Нет | ❌ Нет | ✅ Встроен в UI |
| **Автоблокировка при перерасходе** | ❌ Нет | ❌ Нет | ✅ Мгновенное отключение от Xray |
| **Ограничение инбаундов** | ❌ Нет | ❌ Нет | ✅ Доступно |
| **Безопасный откат к Marzban** | - | ✅ Безопасно | ✅ 100% Безопасно (без кастомных миграций) |

---

## Установка и миграция

Для перехода на Marzyar достаточно изменить строку образа в `docker-compose.yml`:

```yaml
services:  
  marzban:  
    image: mehrwizard/marzyar:latest
```

Затем выполните команду:
```bash
marzban update
```

---

## Пожертвование (Donation)

Если вы находите Marzyar полезным:

- [Поддержать проект через платежный шлюз MehrNet](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## Лицензия

Marzyar распространяется под лицензией [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).

