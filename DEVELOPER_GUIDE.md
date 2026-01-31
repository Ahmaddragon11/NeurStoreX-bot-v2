# 📚 دليل المطور - Developer Guide

دليل شامل لفهم بنية البوت وكيفية تطويره وتخصيصه.

## 🏗️ البنية المعمارية

### نمط التصميم
البوت يستخدم:
- **MVC Pattern**: فصل المنطق عن العرض
- **Modular Architecture**: وحدات مستقلة
- **Singleton Pattern**: لقاعدة البيانات
- **Factory Pattern**: لإنشاء لوحات المفاتيح

## 📁 الوحدات الرئيسية

### 1. config.py
**الغرض**: إدارة جميع الإعدادات والثوابت

```python
# مثال على الاستخدام
import config

# الوصول للإعدادات
bot_token = config.BOT_TOKEN
admin_ids = config.ADMIN_IDS
messages = config.MESSAGES

# تعديل إعداد
config.MAINTENANCE_MODE = True
```

**الإعدادات الرئيسية**:
- `BOT_TOKEN`: توكن البوت
- `ADMIN_IDS`: قائمة المسؤولين
- `DATABASE_NAME`: اسم قاعدة البيانات
- `MESSAGES`: الرسائل النصية
- `EMOJI`: الرموز التعبيرية
- `PRODUCT_TYPES`: أنواع المنتجات

### 2. database.py
**الغرض**: إدارة قاعدة البيانات

```python
from database import Database

# إنشاء اتصال
db = Database("store_bot.db")

# إضافة مستخدم
db.add_user(
    user_id=123456,
    username="user123",
    first_name="محمد",
    last_name="أحمد"
)

# جلب مستخدم
user = db.get_user(123456)

# إضافة منتج
product_id = db.add_product(
    name="منتج جديد",
    description="وصف المنتج",
    price=50,
    product_type="text",
    delivery_content="المحتوى"
)

# إنشاء طلب
order_id = db.create_order(
    user_id=123456,
    product_id=1,
    product_name="منتج",
    payment_id="unique_payment_id",
    price=50
)
```

**الدوال الرئيسية**:

#### إدارة المستخدمين
- `add_user()`: إضافة مستخدم
- `get_user()`: جلب مستخدم
- `ban_user()`: حظر مستخدم
- `unban_user()`: إلغاء الحظر
- `update_user_activity()`: تحديث النشاط

#### إدارة المنتجات
- `add_product()`: إضافة منتج
- `get_product()`: جلب منتج
- `get_active_products()`: المنتجات النشطة
- `update_product()`: تحديث منتج
- `delete_product()`: حذف منتج
- `decrease_stock()`: تقليل المخزون (آمن)

#### إدارة الطلبات
- `create_order()`: إنشاء طلب
- `update_order_status()`: تحديث حالة الطلب
- `get_user_orders()`: طلبات مستخدم
- `complete_purchase()`: إتمام الشراء

#### الأمان
- `check_rate_limit()`: فحص معدل الطلبات
- `record_failed_attempt()`: تسجيل محاولة فاشلة
- `add_log()`: إضافة سجل

### 3. keyboards.py
**الغرض**: إنشاء لوحات المفاتيح

```python
from keyboards import Keyboards

kb = Keyboards()

# القائمة الرئيسية
keyboard = kb.main_menu(is_admin=False)

# لوحة المسؤولين
admin_panel = kb.admin_panel()

# قائمة منتجات
products = [...] # قائمة المنتجات
products_kb = kb.products_list(products, page=0)

# تفاصيل منتج
product_detail = kb.product_detail(product_id=1, is_admin=False)
```

**لوحات المفاتيح المتاحة**:
- `main_menu()`: القائمة الرئيسية
- `admin_panel()`: لوحة التحكم
- `admin_products()`: إدارة المنتجات
- `product_types()`: أنواع المنتجات
- `products_list()`: قائمة منتجات
- `product_detail()`: تفاصيل منتج
- `confirm_action()`: تأكيد إجراء
- `back_button()`: زر رجوع

### 4. handlers.py
**الغرض**: معالجة الرسائل والأوامر

```python
# معالجات رئيسية
async def start_handler(update, context):
    """معالج أمر /start"""
    
async def callback_handler(update, context):
    """معالج الأزرار"""
    
async def message_handler(update, context):
    """معالج الرسائل النصية"""
```

**تدفق المعالجة**:
1. استقبال التحديث
2. التحقق من الصيانة
3. التحقق من الحظر
4. التحقق من معدل الطلبات
5. معالجة الطلب
6. تحديث النشاط
7. تسجيل الحدث

### 5. payment_handler.py
**الغرض**: معالجة عمليات الدفع

```python
async def precheckout_handler(update, context):
    """التحقق قبل الدفع"""
    # التحقق من المنتج
    # التحقق من المخزون
    # التحقق من السعر
    # قبول/رفض الدفع

async def successful_payment_handler(update, context):
    """معالجة الدفع الناجح"""
    # إنشاء الطلب
    # تقليل المخزون
    # توصيل المنتج
    # تحديث الإحصائيات
    # إرسال الإشعارات
```

**تدفق الدفع**:
1. المستخدم يضغط "شراء"
2. إنشاء فاتورة Telegram Stars
3. `precheckout_handler` يتحقق من الطلب
4. المستخدم يدفع
5. `successful_payment_handler` يعالج الدفع
6. توصيل فوري للمنتج

### 6. utils.py
**الغرض**: أدوات مساعدة

```python
from utils import (
    is_admin,
    check_banned,
    check_maintenance,
    format_product_info,
    send_product_to_user,
    validate_price,
    export_to_csv
)

# مثال
if is_admin(user_id):
    # منطق المسؤول
    pass

# تنسيق معلومات منتج
product = db.get_product(1)
formatted_text = format_product_info(product)

# إرسال منتج
success = await send_product_to_user(
    context, user_id, product, order_id
)
```

### 7. admin_handlers.py
**الغرض**: معالجات إدارية متقدمة

```python
from admin_handlers import AdminCommandsHandler

handler = AdminCommandsHandler()

# معالجة اختيار نوع المنتج
await handler.handle_product_type_selection(update, context)

# معالجة محتوى المنتج
await handler.handle_product_content(update, context)

# البث الجماعي
await handler.handle_broadcast_start(update, context)

# تصدير البيانات
await handler.handle_export_data(update, context)
```

## 🔐 الأمان

### حماية من Race Conditions

```python
# تقليل المخزون بشكل آمن
cursor.execute("BEGIN EXCLUSIVE")
cursor.execute("""
    UPDATE products SET stock = stock - 1
    WHERE id = ? AND stock > 0
""", (product_id,))
conn.commit()
```

### حماية من Double Spending

```python
# استخدام payment_id فريد
db.create_order(
    payment_id=telegram_payment_id  # معرف فريد من تيليجرام
)
# إذا كان الطلب موجوداً، يتم رفضه
```

### Rate Limiting

```python
# فحص معدل الطلبات
if not db.check_rate_limit(user_id, max_requests=20):
    # رفض الطلب
    return
```

### تنظيف المدخلات

```python
from utils import sanitize_input

# تنظيف النص
clean_text = sanitize_input(user_input, max_length=1000)
```

## 📊 قاعدة البيانات

### مخطط الجداول

```sql
-- المستخدمون
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0
);

-- المنتجات
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    type TEXT NOT NULL,
    stock INTEGER DEFAULT -1,
    is_active INTEGER DEFAULT 1
);

-- الطلبات
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    payment_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending'
);
```

### الفهارس

```sql
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_logs_user ON logs(user_id);
```

## 🔄 إضافة ميزة جديدة

### مثال: إضافة نظام تقييمات

#### 1. تحديث قاعدة البيانات

```python
# في database.py - دالة _create_tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        rating INTEGER CHECK(rating >= 1 AND rating <= 5),
        review TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
""")
```

#### 2. إضافة دوال قاعدة البيانات

```python
# في database.py
def add_rating(self, user_id: int, product_id: int, 
               rating: int, review: str = None) -> bool:
    """إضافة تقييم"""
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ratings (user_id, product_id, rating, review)
            VALUES (?, ?, ?, ?)
        """, (user_id, product_id, rating, review))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"خطأ في إضافة التقييم: {e}")
        return False
```

#### 3. إضافة لوحة مفاتيح

```python
# في keyboards.py
@staticmethod
def rating_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """لوحة التقييم"""
    keyboard = []
    
    # أزرار النجوم
    stars_row = []
    for i in range(1, 6):
        stars_row.append(
            InlineKeyboardButton(
                "⭐" * i,
                callback_data=f"rate:{product_id}:{i}"
            )
        )
    keyboard.append(stars_row)
    
    return InlineKeyboardMarkup(keyboard)
```

#### 4. إضافة معالج

```python
# في handlers.py - ضمن callback_handler
elif data.startswith("rate:"):
    parts = data.split(":")
    product_id = int(parts[1])
    rating = int(parts[2])
    
    if db.add_rating(user.id, product_id, rating):
        await query.answer("✅ شكراً على التقييم!", show_alert=True)
    else:
        await query.answer("❌ فشل التقييم!", show_alert=True)
```

## 🧪 الاختبار

### اختبار وحدة

```python
# test.py
def test_add_product():
    db = Database("test.db")
    
    product_id = db.add_product(
        name="منتج تجريبي",
        description="وصف",
        price=10,
        product_type="text"
    )
    
    assert product_id is not None
    assert product_id > 0
    
    product = db.get_product(product_id)
    assert product['name'] == "منتج تجريبي"
    assert product['price'] == 10
```

### اختبار تكاملي

```python
async def test_purchase_flow():
    # محاكاة عملية شراء كاملة
    # 1. إنشاء منتج
    # 2. إنشاء فاتورة
    # 3. محاكاة دفع ناجح
    # 4. التحقق من التوصيل
    # 5. التحقق من المخزون
    pass
```

## 📝 أفضل الممارسات

### 1. التسجيل

```python
import logging

logger = logging.getLogger(__name__)

# تسجيل معلومات
logger.info("تم إنشاء منتج جديد")

# تسجيل تحذير
logger.warning("مخزون منخفض")

# تسجيل خطأ
logger.error(f"فشل في العملية: {e}")
```

### 2. معالجة الأخطاء

```python
try:
    # الكود
    pass
except SpecificException as e:
    # معالجة محددة
    logger.error(f"خطأ محدد: {e}")
except Exception as e:
    # معالجة عامة
    logger.error(f"خطأ غير متوقع: {e}")
finally:
    # تنظيف
    pass
```

### 3. الأمان

```python
# دائماً تحقق من الصلاحيات
if not is_admin(user.id):
    return

# دائماً نظف المدخلات
clean_input = sanitize_input(user_text)

# دائماً استخدم معاملات آمنة
cursor.execute("BEGIN EXCLUSIVE")
# العمليات الحرجة
conn.commit()
```

### 4. الأداء

```python
# استخدم الفهارس
CREATE INDEX idx_important ON table(column);

# استخدم الـ batch operations
cursor.executemany("INSERT ...", data_list)

# استخدم التخزين المؤقت عند الحاجة
```

## 🚀 النشر

### على VPS

```bash
# تثبيت المتطلبات
pip3 install -r requirements.txt

# تشغيل في الخلفية
nohup python3 main.py &

# أو استخدام screen
screen -S telegram_bot
python3 main.py
# اضغط Ctrl+A ثم D للخروج
```

### باستخدام systemd

```ini
# /etc/systemd/system/telegram-bot.service
[Unit]
Description=Telegram Store Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### باستخدام Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```bash
docker build -t telegram-store-bot .
docker run -d telegram-store-bot
```

## 📚 موارد إضافية

- [وثائق python-telegram-bot](https://docs.python-telegram-bot.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Stars Payment](https://core.telegram.org/bots/payments#stars)

---

✨ **مع التمنيات بالنجاح في التطوير!**
