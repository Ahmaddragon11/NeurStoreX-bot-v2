# -*- coding: utf-8 -*-
"""
Utilities Module
الأدوات المساعدة
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from datetime import datetime
import logging
import os

from database import Database
import config

logger = logging.getLogger(__name__)
db = Database(config.DATABASE_NAME)


def is_admin(user_id: int) -> bool:
    """التحقق من صلاحيات المسؤول"""
    return user_id in config.ADMIN_IDS


async def check_banned(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                      is_callback: bool = False) -> bool:
    """التحقق من حظر المستخدم"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    if user_data and user_data['is_banned']:
        ban_message = config.MESSAGES['banned']
        if user_data.get('ban_reason'):
            ban_message += f"\n\nالسبب: {user_data['ban_reason']}"
        
        if is_callback:
            await update.callback_query.answer(ban_message, show_alert=True)
        else:
            await update.message.reply_text(ban_message)
        
        db.add_log('security', user.id, 'banned_user_attempt', 'محاولة استخدام البوت')
        return False
    
    return True


async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           is_callback: bool = False) -> bool:
    """التحقق من وضع الصيانة"""
    user = update.effective_user
    
    # السماح للمسؤولين دائماً
    if is_admin(user.id):
        return True
    
    # التحقق من وضع الصيانة
    maintenance_mode = db.get_setting('maintenance_mode')
    if maintenance_mode == 'True' or config.MAINTENANCE_MODE:
        if is_callback:
            await update.callback_query.answer(
                config.MESSAGES['maintenance'],
                show_alert=True
            )
        else:
            await update.message.reply_text(config.MESSAGES['maintenance'])
        
        return False
    
    return True


async def check_rate_limit(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          is_callback: bool = False) -> bool:
    """التحقق من معدل الطلبات"""
    user = update.effective_user
    
    # السماح للمسؤولين دائماً
    if is_admin(user.id):
        return True
    
    # فحص معدل الطلبات
    if not db.check_rate_limit(user.id, config.MAX_REQUESTS_PER_MINUTE):
        warning_message = (
            "⚠️ تجاوزت الحد المسموح من الطلبات!\n"
            "انتظر قليلاً قبل المحاولة مرة أخرى."
        )
        
        if is_callback:
            await update.callback_query.answer(warning_message, show_alert=True)
        else:
            await update.message.reply_text(warning_message)
        
        db.add_log('security', user.id, 'rate_limit_exceeded', 
                  f'تجاوز {config.MAX_REQUESTS_PER_MINUTE} طلب/دقيقة')
        return False
    
    return True


def format_product_info(product: dict, include_stock: bool = True) -> str:
    """تنسيق معلومات المنتج"""
    icon = config.EMOJI.get(product['type'], config.EMOJI['products'])
    
    info = f"<b>{icon} {product['name']}</b>\n\n"
    
    if product.get('description'):
        info += f"📝 <b>الوصف:</b>\n{product['description']}\n\n"
    
    # السعر مع الخصم
    price = product['price']
    discount = product.get('discount_percentage', 0)
    
    if discount > 0:
        final_price = price - (price * discount // 100)
        info += f"💰 <b>السعر:</b> <s>{price}</s> {final_price} ⭐\n"
        info += f"🎁 <b>خصم:</b> {discount}%\n"
    else:
        info += f"💰 <b>السعر:</b> {price} ⭐\n"
    
    # نوع المنتج
    product_type = config.PRODUCT_TYPES.get(product['type'], 'غير معروف')
    info += f"📦 <b>النوع:</b> {product_type}\n"
    
    # المخزون
    if include_stock:
        if product['is_limited']:
            stock_status = f"{product['stock']} متوفر"
            if product['stock'] <= 0:
                stock_status = "نفذت الكمية ❌"
            elif product['stock'] < 10:
                stock_status += " ⚠️"
        else:
            stock_status = "غير محدود ♾️"
        
        info += f"📊 <b>المخزون:</b> {stock_status}\n"
    
    # عدد المبيعات
    if product.get('sales_count', 0) > 0:
        info += f"🏆 <b>المبيعات:</b> {product['sales_count']}\n"
    
    # الحالة
    status = "✅ نشط" if product['is_active'] else "❌ معطّل"
    info += f"🔄 <b>الحالة:</b> {status}\n"
    
    return info


def format_user_info(user: dict) -> str:
    """تنسيق معلومات المستخدم"""
    info = f"👤 <b>معلومات الحساب</b>\n\n"
    
    info += f"🆔 <b>المعرف:</b> <code>{user['user_id']}</code>\n"
    
    if user.get('username'):
        info += f"👤 <b>اسم المستخدم:</b> @{user['username']}\n"
    
    info += f"📅 <b>تاريخ الانضمام:</b> {user['join_date'][:10]}\n"
    info += f"💰 <b>الرصيد:</b> {user['balance']} ⭐\n"
    info += f"💸 <b>إجمالي المصروفات:</b> {user['total_spent']} ⭐\n"
    info += f"🛍 <b>عدد المشتريات:</b> {user['total_purchases']}\n"
    info += f"🔗 <b>الإحالات:</b> {user['referral_count']}\n"
    
    # الحالة
    if user['is_banned']:
        info += f"\n🚫 <b>الحالة:</b> محظور\n"
        if user.get('ban_reason'):
            info += f"📝 <b>السبب:</b> {user['ban_reason']}\n"
    else:
        info += f"\n✅ <b>الحالة:</b> نشط\n"
    
    return info


def format_order_info(order: dict) -> str:
    """تنسيق معلومات الطلب"""
    status_emoji = {
        'pending': '⏳',
        'completed': '✅',
        'failed': '❌',
        'refunded': '💸'
    }.get(order['status'], '❓')
    
    info = f"{status_emoji} <b>الطلب #{order['id']}</b>\n"
    info += f"📦 {order['product_name']}\n"
    info += f"💰 {order['final_price']} ⭐\n"
    info += f"📅 {order['created_at'][:16]}\n"
    
    if order.get('discount_amount', 0) > 0:
        info += f"🎁 خصم: {order['discount_amount']} ⭐\n"
    
    return info


async def send_product_to_user(context: ContextTypes.DEFAULT_TYPE, 
                               user_id: int, 
                               product: dict,
                               order_id: int) -> bool:
    """إرسال المنتج للمستخدم حسب نوعه"""
    try:
        product_type = product['type']
        
        # منتج من نوع ملف
        if product_type == 'file':
            if product.get('delivery_content'):
                # افتراض أن delivery_content يحتوي على file_id
                await context.bot.send_document(
                    chat_id=user_id,
                    document=product['delivery_content'],
                    caption=f"📄 {product['name']}\n\n✅ شكراً لشرائك!"
                )
                return True
        
        # منتج من نوع صورة
        elif product_type == 'image':
            if product.get('delivery_content'):
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=product['delivery_content'],
                    caption=f"🖼 {product['name']}\n\n✅ شكراً لشرائك!"
                )
                return True
        
        # منتج من نوع نص
        elif product_type == 'text':
            if product.get('delivery_content'):
                message_text = (
                    f"📝 <b>{product['name']}</b>\n\n"
                    f"{product['delivery_content']}\n\n"
                    f"✅ شكراً لشرائك!"
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message_text,
                    parse_mode='HTML'
                )
                return True
        
        # منتج من نوع كود
        elif product_type == 'code':
            # الحصول على كود غير مستخدم
            code = db.get_unused_code(product['id'], user_id)
            
            if code:
                code_message = (
                    f"🔑 <b>{product['name']}</b>\n\n"
                    f"الكود الخاص بك:\n"
                    f"<code>{code}</code>\n\n"
                    f"💡 انسخ الكود بالضغط عليه\n"
                    f"✅ شكراً لشرائك!"
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=code_message,
                    parse_mode='HTML'
                )
                
                # حفظ الكود في الطلب
                db.update_order_status(order_id, 'completed', 'delivered', code)
                return True
            else:
                logger.error(f"لا توجد أكواد متاحة للمنتج {product['id']}")
                return False
        
        # منتج من نوع رصيد
        elif product_type == 'balance':
            # إضافة رصيد للمستخدم
            balance_amount = int(product.get('delivery_content', 0))
            
            # إضافة الرصيد إلى قاعدة البيانات
            if db.add_user_balance(user_id, balance_amount):
                balance_message = (
                    f"💰 <b>{product['name']}</b>\n\n"
                    f"✅ تم إضافة {balance_amount} ⭐ إلى رصيدك!\n\n"
                    f"شكراً لشرائك!"
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=balance_message,
                    parse_mode='HTML'
                )
                
                # تحديث حالة الطلب
                db.update_order_status(order_id, 'completed', 'delivered')
                return True
            else:
                logger.error(f"فشل إضافة الرصيد للمستخدم {user_id}")
                return False
        
        # نوع غير مدعوم
        else:
            logger.error(f"نوع منتج غير مدعوم: {product_type}")
            return False
    
    except TelegramError as e:
        logger.error(f"خطأ في إرسال المنتج: {e}")
        return False
    except Exception as e:
        logger.error(f"خطأ عام في إرسال المنتج: {e}")
        return False


def validate_price(price_str: str) -> tuple:
    """التحقق من صحة السعر"""
    try:
        price = int(price_str)
        
        if price < config.MIN_PRODUCT_PRICE:
            return False, f"السعر لا يمكن أن يكون أقل من {config.MIN_PRODUCT_PRICE} نجمة"
        
        if price > config.MAX_PRODUCT_PRICE:
            return False, f"السعر لا يمكن أن يكون أكثر من {config.MAX_PRODUCT_PRICE} نجمة"
        
        return True, price
    except ValueError:
        return False, "الرجاء إدخال رقم صحيح للسعر"


def validate_stock(stock_str: str) -> tuple:
    """التحقق من صحة المخزون"""
    try:
        stock = int(stock_str)
        
        if stock < 0:
            return False, "المخزون لا يمكن أن يكون سالباً"
        
        return True, stock
    except ValueError:
        return False, "الرجاء إدخال رقم صحيح للمخزون"


def format_timestamp(timestamp_str: str) -> str:
    """تنسيق التاريخ والوقت"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return timestamp_str


async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, 
                                  message: str):
    """إرسال إشعار للمسؤولين"""
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔔 <b>إشعار:</b>\n\n{message}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"فشل إرسال إشعار للمسؤول {admin_id}: {e}")


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """تنظيف المدخلات النصية"""
    if not text:
        return ""
    
    # إزالة المسافات الزائدة
    text = text.strip()
    
    # تحديد الطول الأقصى
    if len(text) > max_length:
        text = text[:max_length]
    
    # إزالة HTML tags خطيرة (للحماية من XSS)
    dangerous_tags = ['<script>', '</script>', '<iframe>', '</iframe>']
    for tag in dangerous_tags:
        text = text.replace(tag, '')
    
    return text


def create_pagination_text(current_page: int, total_pages: int) -> str:
    """إنشاء نص للصفحات"""
    return f"📄 الصفحة {current_page + 1} من {total_pages}"


async def export_to_csv(data: list, filename: str) -> str:
    """تصدير البيانات إلى CSV"""
    import csv
    
    try:
        os.makedirs(config.TEMP_EXPORT_PATH, exist_ok=True)
        filepath = os.path.join(config.TEMP_EXPORT_PATH, filename)
        
        if not data:
            return None
        
        # الحصول على أسماء الأعمدة من أول عنصر
        headers = data[0].keys()
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        return filepath
    except Exception as e:
        logger.error(f"خطأ في تصدير CSV: {e}")
        return None


def clean_temp_files():
    """تنظيف الملفات المؤقتة"""
    import os
    import time
    
    try:
        # تنظيف مجلد التصدير
        if os.path.exists(config.TEMP_EXPORT_PATH):
            for file in os.listdir(config.TEMP_EXPORT_PATH):
                filepath = os.path.join(config.TEMP_EXPORT_PATH, file)
                # حذف الملفات الأقدم من 24 ساعة
                if os.path.getmtime(filepath) < time.time() - 86400:
                    os.remove(filepath)
                    logger.info(f"تم حذف ملف مؤقت: {filepath}")
    except Exception as e:
        logger.error(f"خطأ في تنظيف الملفات المؤقتة: {e}")
    """تنظيف الملفات المؤقتة"""
    try:
        if os.path.exists(config.TEMP_EXPORT_PATH):
            for file in os.listdir(config.TEMP_EXPORT_PATH):
                file_path = os.path.join(config.TEMP_EXPORT_PATH, file)
                try:
                    os.remove(file_path)
                except:
                    pass
    except Exception as e:
        logger.error(f"خطأ في تنظيف الملفات: {e}")


def generate_referral_code(user_id: int) -> str:
    """توليد كود إحالة"""
    import hashlib
    
    # إنشاء كود فريد
    raw = f"{user_id}_{datetime.now().timestamp()}"
    code = hashlib.md5(raw.encode()).hexdigest()[:8]
    return code.upper()


def calculate_discount(price: int, discount_percentage: int) -> int:
    """حساب السعر بعد الخصم"""
    if discount_percentage <= 0:
        return price
    
    discount_amount = (price * discount_percentage) // 100
    return price - discount_amount


async def log_error(user_id: int, error_type: str, error_message: str):
    """تسجيل الأخطاء"""
    db.add_log('error', user_id, error_type, error_message)
    logger.error(f"User {user_id} - {error_type}: {error_message}")


def get_emoji_for_status(status: str) -> str:
    """الحصول على إيموجي حسب الحالة"""
    emoji_map = {
        'active': '✅',
        'inactive': '❌',
        'pending': '⏳',
        'completed': '✅',
        'failed': '❌',
        'banned': '🚫',
        'warning': '⚠️',
        'info': 'ℹ️',
        'success': '✅',
        'error': '❌'
    }
    return emoji_map.get(status, '❓')


def truncate_text(text: str, max_length: int = 100) -> str:
    """اختصار النص"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
