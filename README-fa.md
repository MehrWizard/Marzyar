<p align="center">
  <a href="https://github.com/MehrWizard/Marzyar" target="_blank" rel="noopener noreferrer">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
      <img width="160" height="160" src="docs/assets/logo-light.svg" alt="Marzyar Logo">
    </picture>
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
   - **حالت بدون اورسل (سخت‌گیرانه)**: سهمیه نماینده بر اساس مجموع حجم‌های تعریف شده برای کاربران سنجیده می‌شود و نماینده نمی‌تواند حجمی بیش از سهمیه خود به کاربران اختصاص دهد.
   - **حالت با اورسل**: سهمیه نماینده بر اساس ترافیک واقعی مصرف شده سنجیده می‌شود.
   - **محاسبه امن و غیرقابل دور زدن**: ادمین‌های عادی با ریست کردن ترافیک کاربران نمی‌توانند سهمیه مصرفی خود را بازگردانند؛ حجم ریست شده در شمارنده سهمیه ادمین ثبت می‌گردد.
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

## حمایت مالی (Donation)

اگر مرزیار برای شما مفید واقع شده و مایل به حمایت از توسعه آن هستید:

- [حمایت مالی از طریق درگاه پرداخت مهرنت](https://gateway.mehrnet.com/product/1DE5C11019E2)

---

## لایسنس

مرزیار تحت لایسنس [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE) منتشر شده است.
