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
import asyncio

from database import Database
from keyboards import Keyboards
from donation_system import DonationSystem
from utils import (
    is_admin, check_banned, check_maintenance,
    format_product_info, format_user_info,
    format_order_info, check_rate_limit
)
import config

logger = logging.getLogger(__name__)
db = Database(config.DATABASE_NAME)
kb = Keyboards()
donation = DonationSystem()


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
    
    # معالجة التبرع من خلال الرابط
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        
        # التبرع
        if arg.startswith("donate:"):
            donation_url = arg.split(":")[1]
            donation = db.get_donation_by_url(donation_url)
            
            if donation:
                await update.message.reply_text(
                    f"🎁 <b>حملة تبرع</b>\n\n"
                    f"الوصف: {donation['description'] or 'تبرع'}\n"
                    f"الهدف: {donation['amount']}⭐\n"
                    f"المستقبل حالياً: {donation['total_received']}⭐\n\n"
                    f"كم تريد أن تتبرع؟\n"
                    f"أرسل الرقم (مثال: 10)",
                    parse_mode='HTML'
                )
                context.user_data['donation_contribute'] = donation['id']
                return
        
        # الإحالة العادية
        try:
            referrer_id = int(arg)
        except ValueError:
            referrer_id = None
    else:
        referrer_id = None
    
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

        # فتح قائمة تعديل منتج واحد
        elif data.startswith("edit_product:"):
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return

            product_id = int(data.split(":")[1])
            await query.edit_message_text(
                "✏️ اختر الحقل الذي تريد تعديله:",
                reply_markup=kb.edit_product_menu(product_id)
            )

        # بدء خطوات تعديل الحقول
        elif data.startswith("edit_product_name:"):
            product_id = int(data.split(":")[1])
            context.user_data['editing_product'] = {'product_id': product_id, 'step': 'name'}
            await query.edit_message_text("✏️ أرسل الاسم الجديد:", reply_markup=kb.back_button(f"product:{product_id}"))

        elif data.startswith("edit_product_desc:"):
            product_id = int(data.split(":")[1])
            context.user_data['editing_product'] = {'product_id': product_id, 'step': 'description'}
            await query.edit_message_text("📝 أرسل الوصف الجديد:", reply_markup=kb.back_button(f"product:{product_id}"))

        elif data.startswith("edit_product_price:"):
            product_id = int(data.split(":")[1])
            context.user_data['editing_product'] = {'product_id': product_id, 'step': 'price'}
            await query.edit_message_text(f"⭐ أرسل السعر الجديد (بين {config.MIN_PRODUCT_PRICE} و {config.MAX_PRODUCT_PRICE}):", reply_markup=kb.back_button(f"product:{product_id}"))

        elif data.startswith("edit_product_stock:"):
            product_id = int(data.split(":")[1])
            context.user_data['editing_product'] = {'product_id': product_id, 'step': 'stock'}
            await query.edit_message_text("🔢 أرسل كمية المخزون الجديدة (استخدم -1 لغير محدود):", reply_markup=kb.back_button(f"product:{product_id}"))

        elif data.startswith("edit_product_discount:"):
            product_id = int(data.split(":")[1])
            context.user_data['editing_product'] = {'product_id': product_id, 'step': 'discount'}
            await query.edit_message_text("🎁 أرسل نسبة الخصم الجديدة (0-100):", reply_markup=kb.back_button(f"product:{product_id}"))

        elif data.startswith("edit_product_content:"):
            product_id = int(data.split(":")[1])
            context.user_data['editing_product'] = {'product_id': product_id, 'step': 'content'}
            await query.edit_message_text("📄 أرسل المحتوى الجديد (نص أو ملف):", reply_markup=kb.back_button(f"product:{product_id}"))

        # قائمة تعديل المنتجات
        elif data == "edit_product_list":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return

            products = db.get_active_products()
            if not products:
                await query.edit_message_text("😔 لا توجد منتجات", reply_markup=kb.admin_products())
                return

            await query.edit_message_text(
                "✏️ اختر المنتج لتعديله:",
                reply_markup=kb.products_list(products, 0, "edit_product")
            )

        # قائمة حذف المنتجات
        elif data == "delete_product_list":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return

            products = db.get_active_products()
            if not products:
                await query.edit_message_text("😔 لا توجد منتجات", reply_markup=kb.admin_products())
                return

            await query.edit_message_text(
                "🗑 اختر المنتج للحذف:",
                reply_markup=kb.products_list(products, 0, "delete_product")
            )

        # عرض جميع المنتجات (قائمة عامة)
        elif data == "view_all_products" or data == "list_products":
            products = db.get_active_products()
            if not products:
                await query.edit_message_text(config.MESSAGES['no_products'], reply_markup=kb.back_button("start"))
                return

            await query.edit_message_text(
                f"🛍 المنتجات المتاحة ({len(products)})\n\nاختر المنتج:",
                reply_markup=kb.products_list(products, 0, "product")
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

        elif data == "manage_discounts":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return

            await query.edit_message_text("🎁 إدارة الخصومات (قيد التطوير)", reply_markup=kb.admin_settings())

        elif data == "referral_settings":
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return

            await query.edit_message_text(
                f"🔗 إعدادات الإحالة\n\nمكافأة الإحالة الحالية: {config.REFERRAL_REWARD_STARS} ⭐",
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

        # إضافة رصيد لمستخدم (من قبل المسؤول)
        elif data.startswith("add_balance:"):
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return

            target_id = int(data.split(":")[1])
            context.user_data['adding_balance'] = {'target': target_id}
            await query.edit_message_text(f"💰 أرسل قيمة الرصيد لإضافتها للمستخدم {target_id}:", reply_markup=kb.back_button('admin_users'))

        # عرض سجلات مستخدم
        elif data.startswith("user_logs:"):
            if not is_admin(user.id):
                await query.answer("⛔ غير مصرح لك!", show_alert=True)
                return

            target_id = int(data.split(":")[1])
            logs = db.get_logs(user_id=target_id, limit=50)
            if not logs:
                await query.edit_message_text("❌ لا توجد سجلات لهذا المستخدم", reply_markup=kb.back_button('admin_users'))
                return

            text = f"🔒 سجلات المستخدم {target_id}:\n\n"
            for l in logs:
                text += f"{l['timestamp'][:16]} - {l['action']} - {l.get('details','')}\n"

            await query.edit_message_text(text, reply_markup=kb.back_button('admin_users'))

        # عرض إيصال الطلب
        elif data.startswith("receipt:"):
            order_id = int(data.split(":")[1])
            order = db.get_order(order_id)
            if not order:
                await query.answer("❌ لم يتم العثور على الطلب!", show_alert=True)
                return

            await query.edit_message_text(
                f"🧾 إيصال الطلب #{order_id}\n\n"
                f"المنتج: {order.get('product_name')}\n"
                f"السعر: {order.get('final_price')} ⭐\n"
                f"الحالة: {order.get('status')}\n"
                f"الوقت: {order.get('created_at')}\n",
                reply_markup=kb.back_button('my_orders')
            )
        
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

        elif data == "buy_balance":
            await query.edit_message_text(
                "💳 شراء رصيد\n\nأرسل عدد النجوم التي تريد شراؤها:",
                reply_markup=kb.back_button("my_account")
            )
            context.user_data['buying_balance'] = True

        elif data == "balance_history":
            user_data = db.get_user(user.id)
            if not user_data:
                await query.answer("❌ خطأ في جلب البيانات!", show_alert=True)
                return

            history_text = (
                f"📜 تاريخ الحساب\n\n"
                f"إجمالي المصروفات: {user_data.get('total_spent',0)} ⭐\n"
                f"عدد المشتريات: {user_data.get('total_purchases',0)}\n"
            )
            await query.edit_message_text(history_text, reply_markup=kb.back_button('my_account'))
        
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

        # معلومات الحساب (تفاصيل)
        elif data == "account_info":
            user_data = db.get_user(user.id)
            if not user_data:
                await query.answer("❌ خطأ في جلب البيانات!", show_alert=True)
                return

            info = (
                f"👤 معلومات الحساب\n\n"
                f"الاسم: {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
                f"المعرف: @{user_data.get('username') or 'بدون'}\n"
                f"ID: {user_data.get('user_id')}\n"
                f"الانضمام: {user_data.get('join_date')[:10]}\n"
            )

            await query.edit_message_text(info, reply_markup=kb.back_button("my_account"))
        
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
        
        # التبرع الجديد للبوت
        elif data == "donate_to_bot":
            await DonationSystem.show_donation_button(update, context)
        
        elif data.startswith("donate_stars:"):
            amount = int(data.split(":")[1])
            await DonationSystem.handle_donation_amount(update, context, amount)
        
        elif data == "donate_custom":
            context.user_data['donation_custom_amount'] = True
            await query.edit_message_text(
                "💬 <b>مبلغ مخصص</b>\n\n"
                "أرسل المبلغ الذي تريد تبرعه بالنجوم:\n"
                "(يجب أن يكون بين 1 و 2500 نجمة)",
                reply_markup=kb.back_button("donate_to_bot"),
                parse_mode='HTML'
            )
        
        elif data == "donation_stats":
            await DonationSystem.show_donation_stats(update, context)

        # تأكيد تبرع (زر في لوحة التأكيد)
        elif data.startswith("confirm_donation:"):
            donation_id = int(data.split(":")[1])
            donation_obj = db.get_donation(donation_id)
            if not donation_obj:
                await query.answer("❌ حملة التبرع غير موجودة!", show_alert=True)
                return

            # علامة بسيطة: إرسال رابط الحملة أو رسالة تأكيد للمالك
            await query.answer("✅ تم تأكيد الحملة!", show_alert=True)
            try:
                await context.bot.send_message(
                    chat_id=donation_obj['donor_id'],
                    text=(f"🎉 تم تأكيد حملتك (#{donation_id})\n"
                          f"الوصف: {donation_obj.get('description') or 'لا وصف'}\n"
                          f"الهدف: {donation_obj.get('amount')}⭐")
                )
            except:
                pass
        
        # التبرع
        elif data == "donation_menu":
            await donation_menu_handler(query, context, user.id)
        
        elif data == "create_donation":
            await create_donation_handler(query, context, user.id)
        
        elif data == "my_donations":
            await my_donations_handler(query, context, user.id)
        
        # النقاط
        elif data == "view_points":
            await view_points_handler(query, context, user.id)
        
        elif data == "exchange_points":
            await exchange_points_handler(query, context, user.id)
        
        elif data == "points_history":
            await points_history_handler(query, context, user.id)
        
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
    
    # معالجة المبلغ المخصص للتبرع
    if context.user_data.get('donation_custom_amount'):
        try:
            amount = int(text)
            if amount < 1 or amount > 2500:
                await update.message.reply_text(
                    "❌ المبلغ يجب أن يكون بين 1 و 2500 نجمة!\n\n"
                    "حاول مرة أخرى أو اضغط /start"
                )
                return
            
            del context.user_data['donation_custom_amount']
            
            # معالجة التبرع
            await DonationSystem.handle_donation_amount(update, context, amount)
        except ValueError:
            await update.message.reply_text("❌ أدخل رقماً صحيحاً!")
        return
    
    # معالجة المساهمة في حملة التبرع
    if 'donation_contribute' in context.user_data:
        try:
            amount = int(text)
            donation_id = context.user_data['donation_contribute']
            
            if amount < 1:
                await update.message.reply_text("❌ يجب أن تكون المساهمة 1 نجمة على الأقل!")
                return
            
            # إضافة المساهمة
            if db.add_donation_contribution(donation_id, user.id, amount):
                await update.message.reply_text(
                    f"✅ شكراً لتبرعك!\n\n"
                    f"🎁 تبرعت بـ {amount}⭐\n"
                    f"📊 اكتسبت {amount} نقطة\n\n"
                    f"رسالة التقدير من صاحب الحملة قريباً 💝"
                )
                
                # إخطار صاحب الحملة
                donation = db.get_donation(donation_id)
                try:
                    await context.bot.send_message(
                        chat_id=donation['donor_id'],
                        text=(
                            f"🎉 تبرع جديد!\n\n"
                            f"👤 {user.first_name}\n"
                            f"💰 {amount}⭐\n\n"
                            f"شكراً للمساهمة 💝"
                        )
                    )
                except:
                    pass
            else:
                await update.message.reply_text("❌ فشلت المساهمة!")
            
            del context.user_data['donation_contribute']
        except ValueError:
            await update.message.reply_text("❌ أدخل رقماً صحيحاً!")
        return

    # معالجة إضافة رصيد (من قبل المسؤول)
    if 'adding_balance' in context.user_data:
        if not is_admin(user.id):
            return

        try:
            amount = int(text)
            target = context.user_data['adding_balance']['target']
            if amount <= 0:
                await update.message.reply_text("❌ أدخل قيمة صحيحة أكبر من 0")
                return

            if db.add_user_balance(target, amount):
                await update.message.reply_text(f"✅ تم إضافة {amount} ⭐ للمستخدم {target}")
                db.add_log('admin', user.id, 'add_balance', f'أضف {amount} ل {target}')
            else:
                await update.message.reply_text("❌ فشل إضافة الرصيد!")

            del context.user_data['adding_balance']
        except ValueError:
            await update.message.reply_text("❌ الرجاء إدخال رقم صحيح")
        return

    # شراء رصيد (بسيط - دون عملية دفع حقيقية، لإصدار تجريبي)
    if 'buying_balance' in context.user_data:
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ أدخل قيمة صحيحة أكبر من 0")
                return

            # نضيف الرصيد فوراً (تجريبي)
            if db.add_user_balance(user.id, amount):
                await update.message.reply_text(f"✅ تمت إضافة {amount} ⭐ إلى رصيدك!")
                db.add_log('purchase', user.id, 'buy_balance', f'قيمة: {amount}')
            else:
                await update.message.reply_text("❌ فشل إضافة الرصيد!")

            del context.user_data['buying_balance']
        except ValueError:
            await update.message.reply_text("❌ الرجاء إدخال رقم صحيح")
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
    
    # معالجة التبرع
    if 'donation_step' in context.user_data:
        donation_step = context.user_data.get('donation_step')
        
        if donation_step == 'amount':
            try:
                amount = int(text)
                if amount < 10:
                    await update.message.reply_text(
                        "❌ يجب أن يكون المبلغ 10 نجوم على الأقل!"
                    )
                    return
                
                context.user_data['donation_amount'] = amount
                context.user_data['donation_step'] = 'description'
                
                await update.message.reply_text(
                    f"✅ المبلغ: {amount}⭐\n\n"
                    "📝 اكتب وصف للحملة (أو اكتب 'لا' للتخطي):"
                )
            except ValueError:
                await update.message.reply_text("❌ أدخل رقماً صحيحاً!")
            return
        
        elif donation_step == 'description':
            description = text if text != 'لا' else None
            
            # إنشاء حملة تبرع
            donation_id = db.create_donation(
                donor_id=user.id,
                amount=context.user_data['donation_amount'],
                description=description
            )
            
            if donation_id:
                donation = db.get_donation(donation_id)
                
                await update.message.reply_text(
                    f"✅ تم إنشاء حملة التبرع!\n\n"
                    f"🎁 {description or 'تبرع'}\n"
                    f"⭐ الهدف: {donation['amount']} نجمة\n"
                    f"🔗 الرابط للمشاركة:\n"
                    f"<code>donate:{donation['donation_url']}</code>\n\n"
                    f"شارك الرابط مع أصدقائك!",
                    parse_mode='HTML'
                )
                
                del context.user_data['donation_step']
                del context.user_data['donation_amount']
            else:
                await update.message.reply_text("❌ فشل إنشاء الحملة!")
            return
    
    # معالجة استبدال النقاط
    if 'exchange_step' in context.user_data:
        exchange_step = context.user_data.get('exchange_step')
        
        if exchange_step == 'amount':
            try:
                points = int(text)
                user_points = db.get_user_points(user.id)
                
                if points > user_points['points']:
                    await update.message.reply_text(
                        f"❌ لديك {user_points['points']} نقطة فقط!"
                    )
                    return
                
                if points < 10:
                    await update.message.reply_text(
                        "❌ يجب أن تكون النقاط 10 على الأقل!"
                    )
                    return
                
                # استبدال النقاط
                if db.exchange_points_to_stars(user.id, points):
                    stars_received = int(points * 0.1)
                    
                    await update.message.reply_text(
                        f"✅ تم استبدال النقاط!\n\n"
                        f"📊 {points} نقطة → {stars_received} ⭐\n\n"
                        f"تم إضافة النجوم إلى رصيدك!"
                    )
                else:
                    await update.message.reply_text("❌ فشل الاستبدال!")
                
                del context.user_data['exchange_step']
            except ValueError:
                await update.message.reply_text("❌ أدخل رقماً صحيحاً!")
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
    user = update.effective_user
    if not is_admin(user.id):
        return

    editing = context.user_data.get('editing_product', {})
    product_id = editing.get('product_id')
    step = editing.get('step')

    if not product_id or not step:
        return

    try:
        text = update.message.text

        if step == 'name':
            db.update_product(product_id, name=text)
            await update.message.reply_text(f"✅ تم تحديث الاسم: {text}", reply_markup=kb.product_detail(product_id, is_admin=True))

        elif step == 'description':
            db.update_product(product_id, description=text)
            await update.message.reply_text("✅ تم تحديث الوصف", reply_markup=kb.product_detail(product_id, is_admin=True))

        elif step == 'price':
            try:
                price = int(text)
                if price < config.MIN_PRODUCT_PRICE or price > config.MAX_PRODUCT_PRICE:
                    await update.message.reply_text(f"❌ السعر يجب أن يكون بين {config.MIN_PRODUCT_PRICE} و {config.MAX_PRODUCT_PRICE} نجمة!")
                    return
                db.update_product(product_id, price=price)
                await update.message.reply_text(f"✅ تم تحديث السعر: {price} ⭐", reply_markup=kb.product_detail(product_id, is_admin=True))
            except ValueError:
                await update.message.reply_text("❌ أدخل رقماً صحيحاً للسعر!")

        elif step == 'stock':
            try:
                stock = int(text)
                db.update_product(product_id, stock=stock, is_limited=1 if stock >= 0 else 0)
                await update.message.reply_text(f"✅ تم تحديث المخزون: {stock}", reply_markup=kb.product_detail(product_id, is_admin=True))
            except ValueError:
                await update.message.reply_text("❌ أدخل رقماً صحيحاً للمخزون!")

        elif step == 'discount':
            try:
                discount = int(text)
                if discount < 0 or discount > 100:
                    await update.message.reply_text("❌ نسبة الخصم يجب أن تكون بين 0 و 100")
                    return
                db.update_product(product_id, discount_percentage=discount)
                await update.message.reply_text(f"✅ تم تحديث الخصم: {discount}%", reply_markup=kb.product_detail(product_id, is_admin=True))
            except ValueError:
                await update.message.reply_text("❌ أدخل رقماً صحيحاً للخصم!")

        elif step == 'content':
            # نأخذ المحتوى كنص عام أو file_id إذا أرسل ملف
            content = None
            if update.message.document:
                content = update.message.document.file_id
            elif update.message.photo:
                content = update.message.photo[-1].file_id
            else:
                content = text

            db.update_product(product_id, delivery_content=content)
            await update.message.reply_text("✅ تم تحديث المحتوى", reply_markup=kb.product_detail(product_id, is_admin=True))

        # إنهاء وضع التحرير
        if 'editing_product' in context.user_data:
            del context.user_data['editing_product']

        db.add_log('admin', user.id, 'edit_product', f'منتج: {product_id}, خطوة: {step}')

    except Exception as e:
        logger.error(f"خطأ في تعديل المنتج: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء تعديل المنتج")


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
        reply_markup=kb.my_account_menu(),
        parse_mode='HTML'
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


# ==================== معالجات التبرع والنقاط ====================

async def donation_menu_handler(query, context, user_id: int):
    """عرض قائمة التبرع"""
    user = query.from_user
    
    await query.edit_message_text(
        "🎁 <b>قائمة التبرع</b>\n\n"
        "شارك الحب والكرم مع الآخرين! 💝\n\n"
        "يمكنك إنشاء حملة تبرع وسيتمكن الآخرون من المساهمة حتى بدون البوت",
        reply_markup=kb.donation_menu(),
        parse_mode='HTML'
    )


async def create_donation_handler(query, context, user_id: int):
    """بدء عملية إنشاء حملة تبرع"""
    await query.edit_message_text(
        "🎁 <b>حملة تبرع جديدة</b>\n\n"
        "كم عدد النجوم التي تريد جمعها؟\n\n"
        "أرسل الرقم (مثال: 100)",
        reply_markup=kb.back_button("donation_menu"),
        parse_mode='HTML'
    )
    
    context.user_data['donation_step'] = 'amount'


async def my_donations_handler(query, context, user_id: int):
    """عرض حملات التبرع الخاصة بالمستخدم"""
    donations = db.get_user_donations(user_id)
    
    if not donations:
        await query.edit_message_text(
            "😔 لم تقم بإنشاء أي حملة تبرع بعد\n\n"
            "ابدأ حملتك الأولى الآن! 🚀",
            reply_markup=kb.back_button("donation_menu")
        )
        return
    
    donations_text = "🎁 <b>حملاتي</b>\n\n"
    
    for donation in donations:
        progress = (donation['total_received'] / donation['amount']) * 100
        status = "✅ مكتملة" if progress >= 100 else f"⏳ {progress:.0f}%"
        
        donations_text += (
            f"#{donation['id']} - {donation['description'] or 'تبرع'}\n"
            f"   الهدف: {donation['amount']}⭐\n"
            f"   المستقبل: {donation['total_received']}⭐\n"
            f"   الحالة: {status}\n\n"
        )
    
    await query.edit_message_text(
        donations_text,
        reply_markup=kb.back_button("donation_menu"),
        parse_mode='HTML'
    )


async def view_points_handler(query, context, user_id: int):
    """عرض نقاط المستخدم"""
    user_points = db.get_user_points(user_id)
    
    points_text = (
        f"📊 <b>نقاطك</b>\n\n"
        f"النقاط الحالية: {user_points['points']} 🎯\n"
        f"إجمالي المكتسب: {user_points['total_earned']} 📈\n"
        f"المستبدل: {user_points['total_exchanged']} ⭐\n\n"
        f"<i>اكسب نقاط بالتبرع والشراء!</i>"
    )
    
    await query.edit_message_text(
        points_text,
        reply_markup=kb.points_menu(),
        parse_mode='HTML'
    )


async def exchange_points_handler(query, context, user_id: int):
    """بدء عملية استبدال النقاط"""
    user_points = db.get_user_points(user_id)
    
    if user_points['points'] < 10:
        await query.answer(
            "❌ تحتاج إلى 10 نقاط على الأقل للاستبدال!",
            show_alert=True
        )
        return
    
    await query.edit_message_text(
        f"⭐ <b>استبدال النقاط</b>\n\n"
        f"نقاطك الحالية: {user_points['points']}\n\n"
        f"كم نقطة تريد استبدالها؟\n"
        f"(كل 10 نقاط = 1 نجمة)\n\n"
        f"أرسل الرقم (مثال: 10)",
        reply_markup=kb.back_button("view_points"),
        parse_mode='HTML'
    )
    
    context.user_data['exchange_step'] = 'amount'


async def points_history_handler(query, context, user_id: int):
    """عرض سجل تبادل النقاط"""
    history = db.get_exchange_history(user_id)
    
    if not history:
        await query.edit_message_text(
            "📜 <b>السجل</b>\n\n"
            "لم تقم باستبدال أي نقاط بعد",
            reply_markup=kb.back_button("view_points"),
            parse_mode='HTML'
        )
        return
    
    history_text = "📜 <b>سجل الاستبدال</b>\n\n"
    
    for record in history:
        history_text += (
            f"✅ {record['points_used']} نقطة → {record['stars_received']} ⭐\n"
            f"   📅 {record['created_at'][:10]}\n\n"
        )
    
    await query.edit_message_text(
        history_text,
        reply_markup=kb.back_button("view_points"),
        parse_mode='HTML'
    )


# استيراد asyncio
import asyncio
