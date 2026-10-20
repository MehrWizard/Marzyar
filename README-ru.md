<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar" target="_blank" rel="noopener noreferrer">
    <img width="160" height="160" src="docs/assets/marzyar.png" alt="Marzyar Logo">
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

## Документация API Marzyar

В дополнение к стандартным API Marzban, Marzyar предоставляет набор REST эндпоинтов с префиксом `/api/marzyar` для программного управления квотами реселлеров, лимитами пользователей, оверселлингом, разрешенными инбаундами и заблокированными пользователями.

Интерактивная документация Swagger/OpenAPI доступна по адресу `/docs` (если включена переменная `DOCS=true`).

### Аутентификация
Для всех эндпоинтов Marzyar требуется стандартная Bearer-аутентификация Marzban. Передавайте токен доступа в заголовке `Authorization`:
```http
Authorization: Bearer <access_token>
```
Получение токена доступа:
```bash
curl -X POST "https://your-panel-domain:8000/api/admin/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

---

### Список эндпоинтов

| Метод | Эндпоинт | Доступ | Описание |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/marzyar/admins` | Только Sudo | Список настроек, лимитов, квот и заблокированных пользователей всех админов |
| `GET` | `/api/marzyar/admin/{admin_identifier}/settings` | Только Sudo | Настройки и статистика использования конкретного реселлера |
| `PUT` | `/api/marzyar/admin/{admin_identifier}/settings` | Только Sudo | Изменение лимитов пользователей, квоты трафика, оверселлинга и инбаундов |
| `POST` | `/api/marzyar/admin/{admin_identifier}/reset_quota` | Только Sudo | Сброс счетчика потребления квоты реселлера и разблокировка пользователей |
| `GET` | `/api/marzyar/my_limits` | Все админы | Текущие лимиты и остаток квоты авторизованного администратора |
| `GET` | `/api/marzyar/locked_users` | Все админы | Список заблокированных из-за исчерпания квоты пользователей |

---

### 1. Список настроек и квот всех администраторов
- **Эндпоинт**: `GET /api/marzyar/admins`
- **Доступ**: Только суперпользователь (Sudo).
- **Описание**: Возвращает список всех администраторов с их лимитами, выделенным трафиком, фактическим потреблением и количеством заблокированных пользователей.

#### Пример запроса
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admins" \
  -H "Authorization: Bearer <token>"
```

#### Пример ответа (`200 OK`)
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

### 2. Получить настройки конкретного администратора
- **Эндпоинт**: `GET /api/marzyar/admin/{admin_identifier}/settings`
- **Доступ**: Только суперпользователь (Sudo).
- **Параметр пути**: `admin_identifier` (числовой ID или логин администратора).
- **Ответ**: Объект `MarzyarAdminSettingsResponse`; `404 Not Found` если администратор не найден.

#### Пример запроса
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admin/reseller1/settings" \
  -H "Authorization: Bearer <token>"
```

---

### 3. Обновить настройки и лимиты реселлера
- **Эндпоинт**: `PUT /api/marzyar/admin/{admin_identifier}/settings`
- **Доступ**: Только суперпользователь (Sudo).
- **Тело запроса (JSON)**:
  | Поле | Тип | Обязательно | Описание |
  | :--- | :--- | :--- | :--- |
  | `users_limit` | целое число или `null` | Нет | Максимальное количество пользователей (`null` — без ограничений). |
  | `traffic_limit` | целое число или `null` | Нет | Квота трафика в **байтах** (`null` — без ограничений). Пример: `107374182400` (100 ГБ). |
  | `oversell_allowed` | boolean | Нет | `false` = Строгий режим (сумма тарифов ограничена `traffic_limit`); `true` = Оверселлинг (учитывается фактический трафик). |
  | `allowed_inbounds` | массив строк или `null` | Нет | Разрешенные теги инбаундов (`null` — все инбаунды разрешены). |

> **Примечание**: Изменение настроек немедленно запускает перепроверку: при увеличении квоты заблокированные пользователи сразу восстанавливаются в Xray.

#### Пример запроса
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

### 4. Сброс квоты потребления трафика
- **Эндпоинт**: `POST /api/marzyar/admin/{admin_identifier}/reset_quota`
- **Доступ**: Только суперпользователь (Sudo).
- **Описание**: Обнуляет счетчик потребленного трафика реселлера и немедленно разблокирует всех его пользователей в Xray.

#### Пример запроса
```bash
curl -X POST "https://your-panel-domain:8000/api/marzyar/admin/reseller1/reset_quota" \
  -H "Authorization: Bearer <token>"
```

---

### 5. Получить свои лимиты (Self-Service)
- **Эндпоинт**: `GET /api/marzyar/my_limits`
- **Доступ**: Любой авторизованный администратор.
- **Описание**: Возвращает собственные лимиты, остаток квоты, количество пользователей и разрешенные инбаунды для текущего реселлера.

#### Пример запроса
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/my_limits" \
  -H "Authorization: Bearer <token>"
```

#### Пример ответа (`200 OK`)
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

### 6. Список заблокированных пользователей
- **Эндпоинт**: `GET /api/marzyar/locked_users`
- **Доступ**: Любой авторизованный администратор (Sudo видит всех пользователей; реселлер — только своих).
- **Описание**: Возвращает список пользователей, временно заблокированных из-за превышения квоты реселлера.

#### Пример запроса
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/locked_users" \
  -H "Authorization: Bearer <token>"
```

#### Пример ответа (`200 OK`)
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

## Пожертвование (Donation)

Если вы находите Marzyar полезным:

- [Поддержать проект через платежный шлюз MehrNet](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## Лицензия

Marzyar распространяется под лицензией [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).

