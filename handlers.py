# -*- coding: utf-8 -*-
"""
Handlers Module
معالجات الرسائل والأوامر
"""

from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import logging
from datetime import datetime

from database import Database
from keyboards import Keyboards
from utils import (
    is_admin, check_banned, check_maintenance,
    format_product_info, format_user_info,
    format_order_info, check_rate_limit
)
import config

logger = logging.getLogger(__name__)
db = Database(config.DATABASE_NAME)
kb = Keyboards()


# ==================== معالجات المستخدمين ====================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    
    # التحقق من الصيانة
    if not await check_maintenance(update, context):
        return
    
    # التحقق من الحظر
    if not await check_banned(update, context):
        return
    
    # التحقق من معدل الطلبات
    if not await check_rate_limit(update, context):
        return
    
    # معالجة رابط الإحالة
    referrer_id = None
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
        except ValueError:
            pass
    
    # إضافة المستخدم إلى قاعدة البيانات
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referrer_id=referrer_id
    )
    
    # تحديث آخر نشاط
    db.update_user_activity(user.id)
    
    # تسجيل
    db.add_log('info', user.id, 'start_command', 'بدء استخدام البوت')
    
    # الرسالة الترحيبية
    welcome_text = config.MESSAGES['welcome']
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=kb.main_menu(is_admin(user.id))
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    data = query.data
    
    # التحقق من الصيانة
    if not await check_maintenance(update, context, is_callback=True):
        return
    
    # التحقق من الحظر
    if not await check_banned(update, context, is_callback=True):
        return
    
    # التحقق من معدل الطلبات
    if not await check_rate_limit(update, context, is_callback=True):
        return
    
    # تحديث النشاط
    db.update_user_activity(user.id)
    
    try:
        # القائمة الرئيسية
        if data == "start":
            await query.edit_message_text(
                config.MESSAGES['welcome'],
                reply_markup=kb.main_menu(is_admin(user.id))
            )
        
        # تصفح المنتجات
        elif data == "browse_products":
            await browse_products_handler(query, context)
        
        # عرض منتج
        elif data.startswith("product:"):
            product_id = int(data.split(":")[1])
            await show_product_handler(query, context, product_id)
        
        # شراء منتج
        elif data.startswith("buy:"):
            product_id = int(data.split(":")[1])
            await buy_product_handler(query, context, product_id, user.id)
        
        # مشترياتي
        elif data == "my_purchases":
            await my_purchases_handler(query, context, user.id)
        
        # طلباتي
        elif data == "my_orders":
            await my_orders_handler(query, context, user.id)
        
        # حسابي
        elif data == "my_account":
            await my_account_handler(query, context, user.id)
        
        # المساعدة
        elif data == "help":
            await query.edit_message_text(
                config.MESSAGES['help'],
                reply_markup=kb.back_button("start")
            )
        
        # لوحة التحكم (للمسؤولين فقط)
        elif data == "admin_panel":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await query.edit_message_text(
                "🎛 لوحة التحكم الرئيسية\n\nاختر القسم الذي تريد:",
                reply_markup=kb.admin_panel()
            )
        
        # إدارة المنتجات
        elif data == "admin_products":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await query.edit_message_text(
                "📦 إدارة المنتجات\n\nاختر الإجراء:",
                reply_markup=kb.admin_products()
            )
        
        # إضافة منتج
        elif data == "add_product_start":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            context.user_data['adding_product'] = {'step': 'name'}
            await query.edit_message_text(
                "➕ إضافة منتج جديد\n\n"
                "📝 أرسل اسم المنتج:",
                reply_markup=kb.back_button("admin_products")
            )
        
        # الإحصائيات
        elif data == "admin_stats":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await show_statistics_handler(query, context)
        
        # المستخدمون
        elif data == "admin_users":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await show_users_handler(query, context)
        
        # الطلبات
        elif data == "admin_orders":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await show_orders_handler(query, context)
        
        # الإعدادات
        elif data == "admin_settings":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await query.edit_message_text(
                "⚙️ الإعدادات\n\nاختر ما تريد تعديله:",
                reply_markup=kb.admin_settings()
            )
        
        # تبديل وضع الصيانة
        elif data == "toggle_maintenance":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            config.MAINTENANCE_MODE = not config.MAINTENANCE_MODE
            status = "مُفعَّل ✅" if config.MAINTENANCE_MODE else "مُعطَّل ❌"
            
            db.set_setting('maintenance_mode', str(config.MAINTENANCE_MODE))
            db.add_log('admin', user.id, 'toggle_maintenance', f'وضع الصيانة: {status}')
            
            await query.answer(f"تم تغيير وضع الصيانة: {status}", show_alert=True)
            await query.edit_message_text(
                f"⚙️ الإعدادات\n\n🔧 وضع الصيانة: {status}",
                reply_markup=kb.admin_settings()
            )
        
        # النسخ الاحتياطي
        elif data == "backup_database":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await backup_database_handler(query, context)
        
        # التصدير
        elif data == "export_data":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await query.edit_message_text(
                "📊 تصدير البيانات\n\nاختر البيانات للتصدير:",
                reply_markup=kb.export_options()
            )
        
        # السجلات
        elif data == "admin_logs":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            await show_logs_handler(query, context)
        
        # التصفح بالصفحات
        elif data.startswith("page:"):
            parts = data.split(":")
            callback_type = parts[1]
            page = int(parts[2])
            
            if callback_type == "product":
                await browse_products_handler(query, context, page)
        
        # اختيار نوع المنتج
        elif data.startswith("product_type:"):
            from admin_handlers import admin_handler
            await admin_handler.handle_product_type_selection(update, context)
        
        # اختيار نوع المخزون
        elif data.startswith("stock_type:"):
            from admin_handlers import admin_handler
            await admin_handler.handle_stock_type_selection(update, context)
        
        # البث الجماعي
        elif data == "broadcast_message":
            from admin_handlers import admin_handler
            await admin_handler.handle_broadcast_start(update, context)
        
        # التصدير
        elif data.startswith("export:"):
            from admin_handlers import admin_handler
            await admin_handler.handle_export_data(update, context)
        
        # حظر مستخدم
        elif data.startswith("ban_user:"):
            from admin_handlers import admin_handler
            await admin_handler.handle_ban_user(update, context)
        
        # إلغاء حظر مستخدم
        elif data.startswith("unban_user:"):
            from admin_handlers import admin_handler
            await admin_handler.handle_unban_user(update, context)
        
        # حذف منتج
        elif data.startswith("delete_product:"):
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            product_id = int(data.split(":")[1])
            await query.edit_message_text(
                "⚠️ هل أنت متأكد من حذف هذا المنتج؟\n\n"
                "هذا الإجراء لا يمكن التراجع عنه!",
                reply_markup=kb.confirm_action(
                    f"confirm_delete_product:{product_id}",
                    "admin_products"
                )
            )
        
        # تأكيد حذف منتج
        elif data.startswith("confirm_delete_product:"):
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            product_id = int(data.split(":")[1])
            if db.delete_product(product_id):
                db.add_log('admin', user.id, 'delete_product', f'حذف منتج: {product_id}')
                await query.answer("✅ تم حذف المنتج بنجاح!", show_alert=True)
            else:
                await query.answer("❌ فشل حذف المنتج!", show_alert=True)
            
            await query.edit_message_text(
                "📦 إدارة المنتجات",
                reply_markup=kb.admin_products()
            )
        
        # تبديل حالة المنتج
        elif data.startswith("toggle_product:"):
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return
            
            product_id = int(data.split(":")[1])
            product = db.get_product(product_id)
            
            if product:
                new_status = 0 if product['is_active'] else 1
                db.update_product(product_id, is_active=new_status)
                
                status_text = "مفعّل" if new_status else "معطّل"
                await query.answer(f"تم تغيير حالة المنتج إلى: {status_text}")
                
                await show_product_handler(query, context, product_id, is_admin=True)
        
        # رصيدي
        elif data == "my_balance":
            user_data = db.get_user(user.id)
            if user_data:
                balance_text = (
                    f"💰 رصيدك الحالي\n\n"
                    f"الرصيد: {user_data['balance']} ⭐\n"
                    f"إجمالي المصروفات: {user_data['total_spent']} ⭐\n"
                    f"عدد المشتريات: {user_data['total_purchases']}"
                )
                await query.edit_message_text(
                    balance_text,
                    reply_markup=kb.back_button("my_account")
                )
        
        # رابط الإحالة
        elif data == "my_referral":
            bot = await context.bot.get_me()
            referral_link = f"https://t.me/{bot.username}?start={user.id}"
            
            user_data = db.get_user(user.id)
            referral_count = user_data.get('referral_count', 0) if user_data else 0
            
            referral_text = (
                f"🔗 رابط الإحالة الخاص بك\n\n"
                f"شارك هذا الرابط مع أصدقائك:\n"
                f"`{referral_link}`\n\n"
                f"👥 عدد الإحالات: {referral_count}\n"
                f"💰 مكافأة الإحالة: {config.REFERRAL_REWARD_STARS} ⭐"
            )
            
            await query.edit_message_text(
                referral_text,
                reply_markup=kb.back_button("my_account"),
                parse_mode='Markdown'
            )
        
        # إحصائياتي
        elif data == "my_stats":
            user_data = db.get_user(user.id)
            if user_data:
                stats_text = (
                    f"📊 إحصائياتك\n\n"
                    f"👤 المعرف: {user.id}\n"
                    f"📅 تاريخ الانضمام: {user_data['join_date'][:10]}\n"
                    f"💰 الرصيد: {user_data['balance']} ⭐\n"
                    f"💸 إجمالي المصروفات: {user_data['total_spent']} ⭐\n"
                    f"🛍 عدد المشتريات: {user_data['total_purchases']}\n"
                    f"🔗 عدد الإحالات: {user_data['referral_count']}"
                )
                await query.edit_message_text(
                    stats_text,
                    reply_markup=kb.back_button("my_account")
                )
        
        else:
            await query.answer("⚠️ وظيفة قيد التطوير")
    
    except Exception as e:
        logger.error(f"خطأ في معالج الأزرار: {e}")
        await query.answer("❌ حدث خطأ، حاول مرة أخرى")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    user = update.effective_user
    text = update.message.text
    
    # التحقق من الصيانة
    if not await check_maintenance(update, context):
        return
    
    # التحقق من الحظر
    if not await check_banned(update, context):
        return
    
    # معالجة إضافة منتج
    if 'adding_product' in context.user_data:
        if not is_admin(user.id):
            return
        
        product_data = context.user_data['adding_product']
        step = product_data.get('step')
        
        # معالجة المحتوى
        if step == 'content':
            from admin_handlers import admin_handler
            await admin_handler.handle_product_content(update, context)
            return
        
        # معالجة كمية المخزون
        if step == 'stock_amount':
            from admin_handlers import admin_handler
            await admin_handler.handle_stock_amount(update, context)
            return
        
        await handle_add_product_step(update, context)
        return
    
    # معالجة تعديل منتج
    if 'editing_product' in context.user_data:
        if not is_admin(user.id):
            return
        
        await handle_edit_product_step(update, context)
        return
    
    # معالجة البث الجماعي
    if 'broadcasting' in context.user_data:
        if not is_admin(user.id):
            return
        
        await handle_broadcast(update, context)
        return
    
    # رسالة افتراضية
    await update.message.reply_text(
        "👋 مرحباً! استخدم الأزرار أدناه للتنقل:",
        reply_markup=kb.main_menu(is_admin(user.id))
    )


async def handle_add_product_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة خطوات إضافة منتج"""
    user = update.effective_user
    text = update.message.text
    product_data = context.user_data.get('adding_product', {})
    step = product_data.get('step')
    
    try:
        if step == 'name':
            product_data['name'] = text
            product_data['step'] = 'description'
            
            await update.message.reply_text(
                f"✅ الاسم: {text}\n\n"
                "📝 أرسل وصف المنتج:",
                reply_markup=kb.back_button("admin_products")
            )
        
        elif step == 'description':
            product_data['description'] = text
            product_data['step'] = 'price'
            
            await update.message.reply_text(
                f"✅ الوصف: {text}\n\n"
                f"⭐ أرسل سعر المنتج بالنجوم (رقم فقط):",
                reply_markup=kb.back_button("admin_products")
            )
        
        elif step == 'price':
            try:
                price = int(text)
                if price < config.MIN_PRODUCT_PRICE or price > config.MAX_PRODUCT_PRICE:
                    await update.message.reply_text(
                        f"❌ السعر يجب أن يكون بين {config.MIN_PRODUCT_PRICE} و {config.MAX_PRODUCT_PRICE} نجمة!"
                    )
                    return
                
                product_data['price'] = price
                product_data['step'] = 'type'
                
                await update.message.reply_text(
                    f"✅ السعر: {price} ⭐\n\n"
                    "📦 اختر نوع المنتج:",
                    reply_markup=kb.product_types()
                )
            except ValueError:
                await update.message.reply_text("❌ أدخل رقماً صحيحاً للسعر!")
        
        context.user_data['adding_product'] = product_data
    
    except Exception as e:
        logger.error(f"خطأ في إضافة منتج: {e}")
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")


async def handle_edit_product_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة خطوات تعديل منتج"""
    # سيتم تنفيذها لاحقاً
    pass


async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة البث الجماعي"""
    user = update.effective_user
    text = update.message.text
    
    if not is_admin(user.id):
        return
    
    await update.message.reply_text("⏳ جاري إرسال الرسالة...")
    
    users = db.get_all_users()
    success_count = 0
    failed_count = 0
    
    for user_data in users:
        try:
            await context.bot.send_message(
                chat_id=user_data['user_id'],
                text=f"📢 رسالة من الإدارة:\n\n{text}"
            )
            success_count += 1
            
            # تأخير بسيط لتجنب الحظر
            await asyncio.sleep(config.BROADCAST_DELAY)
        except Exception as e:
            failed_count += 1
            logger.warning(f"فشل إرسال رسالة إلى {user_data['user_id']}: {e}")
    
    result_text = (
        f"✅ تم إرسال الرسالة!\n\n"
        f"نجح: {success_count}\n"
        f"فشل: {failed_count}"
    )
    
    await update.message.reply_text(result_text)
    
    # إنهاء وضع البث
    del context.user_data['broadcasting']
    
    db.add_log('admin', user.id, 'broadcast', f'إرسال جماعي: نجح {success_count}, فشل {failed_count}')


# ==================== معالجات العرض ====================

async def browse_products_handler(query, context, page: int = 0):
    """عرض قائمة المنتجات"""
    products = db.get_active_products()
    
    if not products:
        await query.edit_message_text(
            config.MESSAGES['no_products'],
            reply_markup=kb.back_button("start")
        )
        return
    
    await query.edit_message_text(
        f"🛍 المنتجات المتاحة ({len(products)})\n\n"
        "اختر المنتج الذي تريده:",
        reply_markup=kb.products_list(products, page, "product")
    )


async def show_product_handler(query, context, product_id: int, is_admin: bool = False):
    """عرض تفاصيل منتج"""
    product = db.get_product(product_id)
    
    if not product:
        await query.answer("❌ المنتج غير موجود!", show_alert=True)
        return
    
    product_text = format_product_info(product)
    
    await query.edit_message_text(
        product_text,
        reply_markup=kb.product_detail(product_id, is_admin),
        parse_mode='HTML'
    )


async def buy_product_handler(query, context, product_id: int, user_id: int):
    """معالج شراء المنتج"""
    product = db.get_product(product_id)
    
    if not product:
        await query.answer("❌ المنتج غير موجود!", show_alert=True)
        return
    
    if not product['is_active']:
        await query.answer("❌ المنتج غير متاح حالياً!", show_alert=True)
        return
    
    # التحقق من المخزون
    if product['is_limited'] and product['stock'] <= 0:
        await query.answer(config.MESSAGES['out_of_stock'], show_alert=True)
        return
    
    # التحقق من الأكواد للمنتجات من نوع code
    if product['type'] == 'code':
        available_codes = db.get_available_codes_count(product_id)
        if available_codes <= 0:
            await query.answer(config.MESSAGES['out_of_stock'], show_alert=True)
            return
    
    # حساب السعر مع الخصم
    price = product['price']
    discount = product.get('discount_percentage', 0)
    final_price = price - (price * discount // 100)
    
    # إنشاء فاتورة Telegram Stars
    title = product['name']
    description = product['description'] or "منتج رقمي"
    
    payload = f"product_{product_id}_{user_id}_{int(datetime.now().timestamp())}"
    
    prices = [LabeledPrice(label=title, amount=final_price)]
    
    try:
        # إرسال الفاتورة
        await query.message.reply_invoice(
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # فارغ لـ Telegram Stars
            currency="XTR",  # عملة Telegram Stars
            prices=prices
        )
        
        await query.answer("💳 تم إنشاء الفاتورة! أكمل الدفع 👆")
        
        db.add_log('purchase', user_id, 'invoice_created', f'منتج: {product_id}')
    
    except TelegramError as e:
        logger.error(f"خطأ في إنشاء الفاتورة: {e}")
        await query.answer("❌ فشل إنشاء الفاتورة!", show_alert=True)


async def my_purchases_handler(query, context, user_id: int):
    """عرض مشتريات المستخدم"""
    orders = db.get_user_orders(user_id, limit=20)
    
    if not orders:
        await query.edit_message_text(
            "😔 لم تقم بأي عملية شراء بعد",
            reply_markup=kb.back_button("start")
        )
        return
    
    purchases_text = "⭐ مشترياتي:\n\n"
    
    for order in orders:
        status_emoji = "✅" if order['status'] == 'completed' else "⏳"
        purchases_text += (
            f"{status_emoji} {order['product_name']}\n"
            f"   💰 {order['final_price']} ⭐\n"
            f"   📅 {order['created_at'][:10]}\n\n"
        )
    
    await query.edit_message_text(
        purchases_text,
        reply_markup=kb.back_button("start")
    )


async def my_orders_handler(query, context, user_id: int):
    """عرض طلبات المستخدم"""
    orders = db.get_user_orders(user_id, limit=10)
    
    if not orders:
        await query.edit_message_text(
            "😔 لا توجد طلبات",
            reply_markup=kb.back_button("start")
        )
        return
    
    orders_text = "🧾 طلباتي:\n\n"
    
    for order in orders:
        orders_text += format_order_info(order) + "\n"
    
    await query.edit_message_text(
        orders_text,
        reply_markup=kb.back_button("start")
    )


async def my_account_handler(query, context, user_id: int):
    """عرض معلومات الحساب"""
    user_data = db.get_user(user_id)
    
    if not user_data:
        await query.answer("❌ خطأ في جلب البيانات!", show_alert=True)
        return
    
    account_text = format_user_info(user_data)
    
    await query.edit_message_text(
        account_text,
        reply_markup=kb.my_account_menu()
    )


# ==================== معالجات المسؤولين ====================

async def show_statistics_handler(query, context):
    """عرض الإحصائيات"""
    stats = db.get_statistics()
    
    stats_text = (
        f"📊 إحصائيات البوت\n\n"
        f"👥 إجمالي المستخدمين: {stats.get('total_users', 0)}\n"
        f"👤 نشط (24س): {stats.get('active_users_24h', 0)}\n"
        f"💰 إجمالي المبيعات: {stats.get('total_revenue', 0)} ⭐\n"
        f"🧾 إجمالي الطلبات: {stats.get('total_orders', 0)}\n"
        f"✅ طلبات مكتملة: {stats.get('completed_orders', 0)}\n"
        f"📦 منتجات نشطة: {stats.get('active_products', 0)}\n\n"
        f"🏆 أكثر المنتجات مبيعاً:\n"
    )
    
    for i, product in enumerate(stats.get('top_products', [])[:5], 1):
        stats_text += f"{i}. {product['name']} - {product['sales_count']} مبيعة\n"
    
    await query.edit_message_text(
        stats_text,
        reply_markup=kb.back_button("admin_panel")
    )


async def show_users_handler(query, context, page: int = 0):
    """عرض المستخدمين"""
    users = db.get_all_users(limit=10, offset=page * 10)
    total_users = db.get_users_count()
    
    users_text = f"👥 المستخدمون ({total_users})\n\n"
    
    for user in users:
        status = "🚫" if user['is_banned'] else "✅"
        users_text += (
            f"{status} {user['first_name']} (@{user['username'] or 'بدون'})\n"
            f"   ID: {user['user_id']}\n"
            f"   💰 {user['total_spent']} ⭐\n\n"
        )
    
    await query.edit_message_text(
        users_text,
        reply_markup=kb.back_button("admin_panel")
    )


async def show_orders_handler(query, context):
    """عرض الطلبات"""
    orders = db.get_all_orders(limit=20)
    
    orders_text = "🧾 آخر الطلبات:\n\n"
    
    for order in orders:
        orders_text += (
            f"#{order['id']} - {order['product_name']}\n"
            f"   👤 @{order.get('username', 'غير معروف')}\n"
            f"   💰 {order['final_price']} ⭐\n"
            f"   📅 {order['created_at'][:16]}\n\n"
        )
    
    await query.edit_message_text(
        orders_text,
        reply_markup=kb.back_button("admin_panel")
    )


async def show_logs_handler(query, context):
    """عرض السجلات"""
    logs = db.get_logs(limit=20)
    
    logs_text = "🔒 سجلات الأمان:\n\n"
    
    for log in logs:
        logs_text += (
            f"{log['type'].upper()} - {log['action']}\n"
            f"   👤 {log['user_id']}\n"
            f"   📅 {log['timestamp'][:16]}\n\n"
        )
    
    await query.edit_message_text(
        logs_text,
        reply_markup=kb.back_button("admin_panel")
    )


async def backup_database_handler(query, context):
    """نسخ احتياطي لقاعدة البيانات"""
    import shutil
    import os
    from datetime import datetime
    
    try:
        # إنشاء مجلد النسخ الاحتياطية
        os.makedirs(config.BACKUP_PATH, exist_ok=True)
        
        # اسم الملف
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{config.BACKUP_PATH}backup_{timestamp}.db"
        
        # نسخ قاعدة البيانات
        shutil.copy2(config.DATABASE_NAME, backup_file)
        
        # إرسال الملف
        with open(backup_file, 'rb') as file:
            await query.message.reply_document(
                document=file,
                filename=f"backup_{timestamp}.db",
                caption="💾 نسخة احتياطية من قاعدة البيانات"
            )
        
        await query.answer("✅ تم إنشاء النسخة الاحتياطية!", show_alert=True)
        
        # حذف النسخ القديمة
        backups = sorted([f for f in os.listdir(config.BACKUP_PATH) if f.endswith('.db')])
        if len(backups) > config.MAX_BACKUPS:
            for old_backup in backups[:-config.MAX_BACKUPS]:
                os.remove(os.path.join(config.BACKUP_PATH, old_backup))
        
        db.add_log('admin', query.from_user.id, 'backup', 'نسخ احتياطي')
    
    except Exception as e:
        logger.error(f"خطأ في النسخ الاحتياطي: {e}")
        await query.answer("❌ فشل إنشاء النسخة الاحتياطية!", show_alert=True)


# استيراد asyncio
import asyncio
