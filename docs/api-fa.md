# مستندات رابط کاربری برنامه‌نویسی (REST API) مرزیار

علاوه بر اندپوینت‌های استاندارد مرزبان، مرزیار دارای مجموعه‌ای از اندپوینت‌های اختصاصی تحت پیشوند `/api/marzyar` برای مدیریت سهمیه نمایندگان، سقف تعداد کاربران، حالت‌های اورسل، محدودسازی اینباندها و کاربران قفل‌شده است.

مستندات تعاملی Swagger/OpenAPI نیز مستقیماً از طریق آدرس `/docs` در مرورگر شما در دسترس است (در صورتی که با متغیر `DOCS=true` فعال شده باشد).

---

## احراز هویت (Authentication)

تمامی اندپوینت‌های مرزیار از سیستم احراز هویت توکن استاندارد مرزبان (OAuth2 Bearer Token) استفاده می‌کنند. توکن دسترسی باید در هدر HTTP ارسال شود:

```http
Authorization: Bearer <access_token>
```

برای دریافت توکن دسترسی:

```bash
curl -X POST "https://your-panel-domain:8000/api/admin/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

---

## فهرست اندپوینت‌ها

| متد | مسیر (Endpoint) | سطح دسترسی | توضیحات |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/marzyar/admins` | فقط Sudo | دریافت تنظیمات، محدودیت‌ها، مصرف سهمیه و وضعیت قفل برای تمام ادمین‌ها |
| `GET` | `/api/marzyar/admin/{admin_identifier}/settings` | فقط Sudo | دریافت تنظیمات و آمار مصرف زنده یک ادمین خاص |
| `PUT` | `/api/marzyar/admin/{admin_identifier}/settings` | فقط Sudo | ویرایش سقف کاربر، سهمیه ترافیک، حالت اورسل و اینباندهای مجاز نماینده |
| `POST` | `/api/marzyar/admin/{admin_identifier}/reset_quota` | فقط Sudo | ریست شمارنده مصرف ترافیک نماینده و باز کردن آنی کاربران قفل‌شده |
| `GET` | `/api/marzyar/my_limits` | تمامی ادمین‌ها | دریافت محدودیت‌ها، سهمیه باقی‌مانده و دسترسی‌های ادمین لاگین‌شده |
| `GET` | `/api/marzyar/locked_users` | تمامی ادمین‌ها | مشاهده لیست کاربران قفل‌شده به همراه علت و زمان قفل شدن |

---

## جزئیات اندپوینت‌ها

### ۱. دریافت تنظیمات و سهمیه همه ادمین‌ها
- **مسیر**: `GET /api/marzyar/admins`
- **دسترسی**: فقط ادمین کل (Sudo Admin).
- **توضیحات**: فهرستی از وضعیت تمام ادمین‌ها شامل سقف کاربران، سهمیه ترافیک، ترافیک تخصیص‌یافته، ترافیک مصرف‌شده کل و تعداد کاربران قفل‌شده را برمی‌گرداند.

#### نمونه درخواست
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admins" \
  -H "Authorization: Bearer <token>"
```

#### نمونه پاسخ (`200 OK`)
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

### ۲. دریافت تنظیمات یک ادمین خاص
- **مسیر**: `GET /api/marzyar/admin/{admin_identifier}/settings`
- **دسترسی**: فقط ادمین کل (Sudo Admin).
- **پارامترهای مسیر**:
  - `admin_identifier`: شناسه عددی ادمین (مثلاً `2`) یا نام کاربری (مثلاً `reseller1`).

#### نمونه درخواست
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admin/reseller1/settings" \
  -H "Authorization: Bearer <token>"
```

---

### ۳. ویرایش تنظیمات و محدودیت‌های نماینده
- **مسیر**: `PUT /api/marzyar/admin/{admin_identifier}/settings`
- **دسترسی**: فقط ادمین کل (Sudo Admin).
- **بدنه درخواست** (`application/json`):
  | فیلد | نوع | الزامی | توضیحات |
  | :--- | :--- | :--- | :--- |
  | `users_limit` | عدد صحیح \| null | خیر | سقف تعداد کاربران مجاز (`null` برای نامحدود). |
  | `traffic_limit` | عدد صحیح \| null | خیر | سهمیه ترافیک به **بایت** (`null` برای نامحدود). مثال: `107374182400` برای ۱۰۰ گیگابایت. |
  | `oversell_allowed` | بولی (boolean) | خیر | `false` = حالت بدون اورسل (سخت‌گیرانه)؛ `true` = حالت با اورسل. |
  | `allowed_inbounds` | آرایه‌ای از رشته‌ها \| null | خیر | فهرست تگ‌های اینباندهای مجاز (`null` برای دسترسی به همه). |

> **نکته**: به‌روزرسانی تنظیمات فوراً وضعیت سهمیه‌ها را بازبینی می‌کند: در صورت افزایش محدودیت، کاربران قفل‌شده بلافاصله باز می‌شوند؛ در صورت تغییر اینباندها، کاربران فوراً در Xray همگام‌سازی می‌گردند.

#### نمونه درخواست
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

#### نمونه پاسخ (`200 OK`)
تنظیمات به‌روزرسانی‌شده بازگردانده می‌شود.

---

### ۴. ریست کردن شمارنده مصرف نماینده
- **مسیر**: `POST /api/marzyar/admin/{admin_identifier}/reset_quota`
- **دسترسی**: فقط ادمین کل (Sudo Admin).
- **توضیحات**: شمارنده مصرف ترافیک انباشته‌شده نماینده را صفر می‌کند و کلیه کاربران قفل‌شده او را بلافاصله در Xray آزاد و فعال می‌نماید.

#### نمونه درخواست
```bash
curl -X POST "https://your-panel-domain:8000/api/marzyar/admin/reseller1/reset_quota" \
  -H "Authorization: Bearer <token>"
```

#### نمونه پاسخ (`200 OK`)
پاسخ ادمین با شمارنده مصرف صفرشده و تعداد کاربران قفل‌شده `0`.

---

### ۵. دریافت محدودیت‌های ادمین جاری (سرویس خودکار)
- **مسیر**: `GET /api/marzyar/my_limits`
- **دسترسی**: کلیه ادمین‌ها (سودو یا نماینده).
- **توضیحات**: محدودیت‌ها، سهمیه مصرفی، سهمیه باقی‌مانده و دسترسی‌های ادمینی که توکن به نام اوست را برمی‌گرداند. بسیار مناسب برای توسعه ربات‌ها و اپلیکیشن‌های جانبی نمایندگان.

#### نمونه درخواست
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/my_limits" \
  -H "Authorization: Bearer <token>"
```

#### نمونه پاسخ (`200 OK`)
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

### ۶. مشاهده لیست کاربران قفل‌شده
- **مسیر**: `GET /api/marzyar/locked_users`
- **دسترسی**: کلیه ادمین‌ها.
  - **ادمین کل (Sudo)**: مشاهده تمام کاربران قفل‌شده در کل سیستم.
  - **ادمین نماینده (Reseller)**: مشاهده فقط کاربران قفل‌شده تحت مالکیت خودش.

#### نمونه درخواست
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/locked_users" \
  -H "Authorization: Bearer <token>"
```

#### نمونه پاسخ (`200 OK`)
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
