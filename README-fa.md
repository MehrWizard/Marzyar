<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar" target="_blank" rel="noopener noreferrer">
    <img width="160" height="160" src="docs/assets/marzyar.png" alt="Marzyar Logo">
  </a>
</p>

<h1 align="center">مرزیار (Marzyar)</h1>

<p align="center">
  یک فورک کاملاً سازگار و جایگزین مستقیم برای <a href="https://github.com/gozargah/marzban">مرزبان (Marzban)</a> و <a href="https://github.com/MehrWizard/Marzdar">مرزدار (Marzdar)</a> با پنل کاربری کامل، سهمیه‌بندی پیشرفته نمایندگان، سقف تعداد کاربران، قابلیت اورسل و محدودسازی پروتکل‌ها.
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

## مرزیار چیست؟

**مرزیار** نسخه ارتقایافته و مجهز به سیستم مدیریت نمایندگان (Resellers) از پروژه‌های **مرزدار** و **مرزبان** است.

در حالی که پروژه **مرزدار** بر تکمیل بخش‌های جامانده رابط کاربری تمرکز دارد، **مرزیار** قابلیت‌های مدیریت، سهمیه‌بندی و کنترل دسترسی نمایندگان را به صورت بومی و بدون تغییر جداول اصلی پایگاه داده به سیستم اضافه کرده است:

1. **سقف تعداد حساب‌های کاربری**: تعیین حداکثر تعداد کاربرانی که هر ادمین/نماینده می‌تواند بسازد.
2. **سهمیه حجم و کنترل اورسل (Oversell)**:
   - **محدودیت مصرف یکپارچه**: در *تمامی* حالت‌ها، مجموع ترافیک مصرفی (`∑ active_usage + historical_resets_and_deletions`) هرگز نمی‌تواند از `traffic_limit` نماینده تجاوز کند.
   - **حالت بدون اورسل (سخت‌گیرانه)**: *علاوه بر شرط بالا*، مجموع محدودیت‌های تخصیص‌یافته به کاربران را نیز محدود می‌کند (`∑ user.data_limit ≤ traffic_limit`). نمایندگان نمی‌توانند بیش از ظرفیت تخصیص دهند یا کاربران با ترافیک نامحدود بسازند.
   - **حالت با اورسل**: محدودیت تخصیص را حذف می‌کند. نمایندگان می‌توانند آزادانه سرویس بسازند تا زمانی که مجموع مصرف واقعی به سقف سهمیه برسد.
   - **محاسبه امن و غیرقابل دور زدن**: نمایندگان نمی‌توانند با ریست کردن یا حذف کاربران، سهمیه خود را دور بزنند؛ مصرف گذشته کاربران حذف‌شده یا ریست‌شده در شمارنده مصرف تاریخی نماینده انباشته می‌شود.
3. **وضعیت هوشمند قفل (Locked State Machine)**:
   - با عبور نماینده از سهمیه، کاربران فعال او بدون تغییر در وضعیت دیتابیس به صورت موقت قفل شده و فوراً از اینباندهای Xray قطع می‌شوند.
   - با تمدید یا ریست سهمیه توسط ادمین کل (Sudo)، کاربران قفل‌شده بلافاصله باز شده و به هسته Xray بازمی‌گردند.
4. **اینباندهای مجاز (Allowed Inbounds)**: امکان محدود کردن نماینده به پروتکل‌ها و اینباندهای خاص (مثلاً فقط VMess).
5. **ویجت وضعیت سهمیه در هدر پنل**: نمایش زنده حجم مصرفی، سقف کاربران و کاربران قفل شده برای نماینده.

---

## مقایسه

| بخش | مرزبان (پروژه اصلی) | مرزدار | مرزیار |
| :--- | :--- | :--- | :--- |
| **سازگاری و جابجایی** | استاندارد | ۱۰۰٪ سازگار | ۱۰۰٪ سازگار (بدون دستکاری جداول اصلی) |
| **رابط کاربری وب** | ناقص | ✅ کامل | ✅ کامل |
| **سقف تعداد کاربران نماینده** | ❌ ندارد | ❌ ندارد | ✅ دارد (تحت پنل وب) |
| **سهمیه ترافیک و اورسل** | ❌ ندارد | ❌ ندارد | ✅ دارد (با کنترل دقیق) |
| **قطع خودکار در اتمام سهمیه** | ❌ ندارد | ❌ ندارد | ✅ دارد (جدا شدن آنی از Xray) |
| **محدودسازی اینباندهای نماینده** | ❌ ندارد | ❌ ندارد | ✅ دارد |
| **قابلیت بازگشت به مرزبان** | - | ✅ ایمن | ✅ ۱۰۰٪ ایمن (بدون مایگریشن‌های مخرب) |

---

## نصب و راه‌اندازی

برای جابجایی از مرزبان یا مرزدار به مرزیار، کافیست ایمیج داکر را در `docker-compose.yml` تغییر دهید:

```yaml
services:  
  marzban:  
    image: mehrwizard/marzyar:latest
```

سپس دستور زیر را اجرا نمایید:
```bash
marzban update
```

---

## مستندات API مرزیار

علاوه بر اندپوینت‌های استاندارد مرزبان، مرزیار دارای مجموعه‌ای از اندپوینت‌های اختصاصی REST تحت پیشوند `/api/marzyar` است که امکان مدیریت سهمیه‌های ترافیک، سقف تعداد کاربران، حالت اورسل، اینباندهای مجاز و کاربران قفل‌شده را از طریق کدنویسی و اسکریپت‌ها فراهم می‌کند.

مستندات تعاملی Swagger/OpenAPI نیز در مسیر `/docs` پنل (در صورت فعال بودن متغیر `DOCS=true`) به صورت زنده در دسترس است.

### احراز هویت (Authentication)
تمامی اندپوینت‌های مرزیار نیازمند توکن Bearer معتبر مرزبان هستند. توکن دریافتی را در هدر `Authorization` ارسال کنید:
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

### فهرست اندپوینت‌ها

| متد | مسیر (Endpoint) | سطح دسترسی | توضیحات |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/marzyar/admins` | فقط Sudo | دریافت تنظیمات، محدودیت‌ها، مصرف سهمیه و وضعیت قفل برای تمام ادمین‌ها |
| `GET` | `/api/marzyar/admin/{admin_identifier}/settings` | فقط Sudo | دریافت تنظیمات و آمار مصرف زنده یک ادمین خاص |
| `PUT` | `/api/marzyar/admin/{admin_identifier}/settings` | فقط Sudo | ویرایش سقف کاربر، سهمیه ترافیک، حالت اورسل و اینباندهای مجاز نماینده |
| `POST` | `/api/marzyar/admin/{admin_identifier}/reset_quota` | فقط Sudo | ریست شمارنده مصرف ترافیک نماینده و باز کردن آنی کاربران قفل‌شده |
| `GET` | `/api/marzyar/my_limits` | تمامی ادمین‌ها | دریافت محدودیت‌ها، سهمیه باقی‌مانده و دسترسی‌های ادمین لاگین‌شده |
| `GET` | `/api/marzyar/locked_users` | تمامی ادمین‌ها | مشاهده لیست کاربران قفل‌شده به همراه علت و زمان قفل شدن |

---

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

### ۲. دریافت تنظیمات یک ادمین مشخص
- **مسیر**: `GET /api/marzyar/admin/{admin_identifier}/settings`
- **دسترسی**: فقط ادمین کل (Sudo Admin).
- **پارامتر مسیر**: `admin_identifier` (شناسه عددی ادمین مانند `2` یا نام کاربری مانند `reseller1`).
- **پاسخ**: مدل `MarzyarAdminSettingsResponse`؛ در صورت عدم وجود ادمین خطای `404 Not Found`.

#### نمونه درخواست
```bash
curl -X GET "https://your-panel-domain:8000/api/marzyar/admin/reseller1/settings" \
  -H "Authorization: Bearer <token>"
```

---

### ۳. ویرایش تنظیمات و محدودیت‌های نماینده
- **مسیر**: `PUT /api/marzyar/admin/{admin_identifier}/settings`
- **دسترسی**: فقط ادمین کل (Sudo Admin).
- **پارامتر مسیر**: شناسه عددی یا نام کاربری نماینده.
- **بدنه درخواست (JSON)**:
  | فیلد | نوع | الزامی | توضیحات |
  | :--- | :--- | :--- | :--- |
  | `users_limit` | عدد صحیح یا `null` | خیر | حداکثر تعداد کاربر مجاز (`null` برای نامحدود). |
  | `traffic_limit` | عدد صحیح یا `null` | خیر | سقف ترافیک به **بایت** (`null` برای نامحدود). مثال: `107374182400` برای ۱۰۰ گیگابایت. |
  | `oversell_allowed` | بولی (`true` / `false`) | خیر | `false` = حالت بدون اورسل (مجموع حجم پلن‌های کاربران نمی‌تواند از سهمیه تجاوز کند)؛ `true` = حالت اورسل (صرفاً مصرف واقعی کنترل می‌شود). |
  | `allowed_inbounds` | آرایه‌ای از رشته‌ها یا `null` | خیر | لیست تگ اینباندهای مجاز (`null` برای دسترسی به همه اینباندها). |

> **نکته**: پس از به‌روزرسانی تنظیمات، سهمیه‌ها بلافاصله ممیزی می‌شوند؛ اگر سهمیه افزایش یابد کاربران قفل‌شده فوراً آنلاک و در Xray وصل می‌شوند. همچنین در صورت محدودسازی اینباندها، دسترسی کاربران موجود بلافاصله با لیست جدید هماهنگ می‌شود.

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
مدل `MarzyarAdminSettingsResponse` به‌روزرسانی شده برگردانده می‌شود.

---

### ۴. ریست سهمیه ترافیک مصرفی نماینده
- **مسیر**: `POST /api/marzyar/admin/{admin_identifier}/reset_quota`
- **دسترسی**: فقط ادمین کل (Sudo Admin).
- **توضیحات**: شمارنده مصرف انباشته نماینده را صفر کرده و تمامی کاربران قفل‌شده او را فوراً در هسته Xray فعال و متصل می‌کند.

#### نمونه درخواست
```bash
curl -X POST "https://your-panel-domain:8000/api/marzyar/admin/reseller1/reset_quota" \
  -H "Authorization: Bearer <token>"
```

#### نمونه پاسخ (`200 OK`)
مدل `MarzyarAdminSettingsResponse` به‌روزرسانی شده با ریست شدن مقدار `current_consumed_traffic` و صفر شدن `locked_users_count` بازگردانده می‌شود.

---

### ۵. دریافت وضعیت و سهمیه ادمین جاری (Self-Service)
- **مسیر**: `GET /api/marzyar/my_limits`
- **دسترسی**: تمامی ادمین‌ها (هم ادمین کل و هم نمایندگان).
- **توضیحات**: وضعیت لحظه‌ای مصرف، سقف مجاز، ظرفیت باقی‌مانده کاربران و ترافیک، و اینباندهای مجاز ادمین احرازهویت‌شده را بازمی‌گرداند. ایده‌آل برای ربات‌ها و اپلیکیشن‌های سمت نماینده.

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
- **دسترسی**: تمامی ادمین‌ها.
  - **ادمین کل (Sudo)**: لیست کاربران قفل‌شده تمامی نمایندگان را مشاهده می‌کند.
  - **نماینده (Reseller)**: صرفاً کاربران قفل‌شده متعلق به اکانت خود را مشاهده می‌کند.
- **توضیحات**: لیست کاربرانی را که به دلیل اتمام سهمیه نماینده موقتاً قطع شده‌اند به همراه زمان و علت قفل شدن نمایش می‌دهد.

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

---

## حمایت مالی (Donation)

اگر مرزیار برای شما مفید واقع شده و مایل به حمایت از توسعه آن هستید:

- [حمایت مالی از طریق درگاه پرداخت مهرنت](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## لایسنس

مرزیار تحت لایسنس [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE) منتشر شده است.
