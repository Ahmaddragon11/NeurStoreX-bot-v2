# -*- coding: utf-8 -*-
"""
Admin Commands Handler
معالج الأوامر الإدارية المتقدمة
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
import asyncio
from datetime import datetime

from database import Database
from keyboards import Keyboards
from utils import (
    is_admin, export_to_csv, format_product_info,
    validate_price, validate_stock, sanitize_input
)
import config

logger = logging.getLogger(__name__)
db = Database(config.DATABASE_NAME)
kb = Keyboards()


# حالات المحادثة
(PRODUCT_NAME, PRODUCT_DESC, PRODUCT_PRICE, 
 PRODUCT_TYPE, PRODUCT_CONTENT, PRODUCT_STOCK) = range(6)


class AdminCommandsHandler:
    """فئة لمعالجة الأوامر الإدارية المتقدمة"""
    
    @staticmethod
    async def handle_product_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار نوع المنتج"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        if not is_admin(user.id):
            await query.answer("⛔ غير مصرح لك!", show_alert=True)
            return
        
        data = query.data
        
        if data.startswith("product_type:"):
            product_type = data.split(":")[1]
            
            if 'adding_product' not in context.user_data:
                context.user_data['adding_product'] = {}
            
            context.user_data['adding_product']['type'] = product_type
            context.user_data['adding_product']['step'] = 'content'
            
            # رسائل مختلفة حسب النوع
            messages = {
                'file': "📄 أرسل الملف الذي تريد بيعه:",
                'image': "🖼 أرسل الصورة التي تريد بيعها:",
                'text': "📝 أرسل النص الذي سيتم إرساله للمشتري:",
                'code': "🔑 أرسل الأكواد (كود في كل سطر):",
                'balance': "💰 أرسل قيمة الرصيد بالنجوم:"
            }
            
            await query.edit_message_text(
                f"✅ تم اختيار النوع: {config.PRODUCT_TYPES[product_type]}\n\n"
                f"{messages.get(product_type, 'أرسل المحتوى:')}",
                reply_markup=kb.back_button("admin_products")
            )
    
    @staticmethod
    async def handle_stock_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار نوع المخزون"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        if not is_admin(user.id):
            await query.answer("⛔ غير مصرح لك!", show_alert=True)
            return
        
        data = query.data
        
        if data.startswith("stock_type:"):
            stock_type = data.split(":")[1]
            
            if 'adding_product' not in context.user_data:
                return
            
            product_data = context.user_data['adding_product']
            
            if stock_type == "unlimited":
                product_data['is_limited'] = 0
                product_data['stock'] = -1
                
                # إنشاء المنتج
                await AdminCommandsHandler.create_product(query, context, product_data)
            
            elif stock_type == "limited":
                product_data['is_limited'] = 1
                product_data['step'] = 'stock_amount'
                
                await query.edit_message_text(
                    "🔢 أرسل كمية المخزون المتاحة:",
                    reply_markup=kb.back_button("admin_products")
                )
    
    @staticmethod
    async def create_product(query, context, product_data):
        """إنشاء المنتج في قاعدة البيانات"""
        try:
            product_id = db.add_product(
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                product_type=product_data['type'],
                delivery_content=product_data.get('content'),
                stock=product_data.get('stock', -1),
                is_limited=product_data.get('is_limited', 0)
            )
            
            if product_id:
                # إضافة الأكواد إذا كان من نوع code
                if product_data['type'] == 'code' and product_data.get('codes'):
                    db.add_codes(product_id, product_data['codes'])
                
                success_text = (
                    f"✅ تم إضافة المنتج بنجاح!\n\n"
                    f"🆔 المعرف: {product_id}\n"
                    f"📦 الاسم: {product_data['name']}\n"
                    f"💰 السعر: {product_data['price']} ⭐\n"
                    f"📊 النوع: {config.PRODUCT_TYPES[product_data['type']]}"
                )
                
                await query.edit_message_text(
                    success_text,
                    reply_markup=kb.admin_products()
                )
                
                # تسجيل
                db.add_log('admin', query.from_user.id, 'add_product', 
                          f'منتج: {product_id}')
                
                # حذف البيانات المؤقتة
                del context.user_data['adding_product']
            else:
                await query.edit_message_text(
                    "❌ فشل إضافة المنتج!",
                    reply_markup=kb.admin_products()
                )
        
        except Exception as e:
            logger.error(f"خطأ في إنشاء المنتج: {e}")
            await query.edit_message_text(
                "❌ حدث خطأ في إضافة المنتج!",
                reply_markup=kb.admin_products()
            )
    
    @staticmethod
    async def handle_product_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة محتوى المنتج"""
        user = update.effective_user
        
        if not is_admin(user.id):
            return
        
        if 'adding_product' not in context.user_data:
            return
        
        product_data = context.user_data['adding_product']
        
        if product_data.get('step') != 'content':
            return
        
        product_type = product_data['type']
        
        try:
            if product_type == 'file':
                if update.message.document:
                    file_id = update.message.document.file_id
                    product_data['content'] = file_id
                    product_data['step'] = 'stock_type'
                    
                    await update.message.reply_text(
                        "✅ تم حفظ الملف!\n\n"
                        "📊 اختر نوع المخزون:",
                        reply_markup=kb.stock_type()
                    )
                else:
                    await update.message.reply_text("❌ الرجاء إرسال ملف!")
            
            elif product_type == 'image':
                if update.message.photo:
                    file_id = update.message.photo[-1].file_id
                    product_data['content'] = file_id
                    product_data['step'] = 'stock_type'
                    
                    await update.message.reply_text(
                        "✅ تم حفظ الصورة!\n\n"
                        "📊 اختر نوع المخزون:",
                        reply_markup=kb.stock_type()
                    )
                else:
                    await update.message.reply_text("❌ الرجاء إرسال صورة!")
            
            elif product_type == 'text':
                text_content = sanitize_input(update.message.text, max_length=4000)
                product_data['content'] = text_content
                product_data['step'] = 'stock_type'
                
                await update.message.reply_text(
                    "✅ تم حفظ النص!\n\n"
                    "📊 اختر نوع المخزون:",
                    reply_markup=kb.stock_type()
                )
            
            elif product_type == 'code':
                codes_text = update.message.text
                codes = [code.strip() for code in codes_text.split('\n') if code.strip()]
                
                if codes:
                    product_data['codes'] = codes
                    product_data['content'] = f"{len(codes)} أكواد"
                    product_data['is_limited'] = 1
                    product_data['stock'] = len(codes)
                    
                    await update.message.reply_text(
                        f"✅ تم حفظ {len(codes)} كود!\n\n"
                        "📊 جاري إنشاء المنتج...",
                        reply_markup=kb.back_button("admin_products")
                    )
                    
                    # إنشاء المنتج مباشرة
                    product_id = db.add_product(
                        name=product_data['name'],
                        description=product_data['description'],
                        price=product_data['price'],
                        product_type=product_data['type'],
                        delivery_content=product_data['content'],
                        stock=len(codes),
                        is_limited=1
                    )
                    
                    if product_id:
                        db.add_codes(product_id, codes)
                        
                        await update.message.reply_text(
                            f"✅ تم إضافة المنتج بنجاح! (المعرف: {product_id})",
                            reply_markup=kb.admin_products()
                        )
                        
                        del context.user_data['adding_product']
                    else:
                        await update.message.reply_text(
                            "❌ فشل إضافة المنتج!",
                            reply_markup=kb.admin_products()
                        )
                else:
                    await update.message.reply_text("❌ لم يتم العثور على أكواد!")
            
            elif product_type == 'balance':
                try:
                    balance_amount = int(update.message.text)
                    
                    if balance_amount <= 0:
                        await update.message.reply_text("❌ القيمة يجب أن تكون أكبر من 0!")
                        return
                    
                    product_data['content'] = str(balance_amount)
                    product_data['step'] = 'stock_type'
                    
                    await update.message.reply_text(
                        f"✅ تم حفظ قيمة الرصيد: {balance_amount} ⭐\n\n"
                        "📊 اختر نوع المخزون:",
                        reply_markup=kb.stock_type()
                    )
                except ValueError:
                    await update.message.reply_text("❌ الرجاء إدخال رقم صحيح!")
        
        except Exception as e:
            logger.error(f"خطأ في معالجة محتوى المنتج: {e}")
            await update.message.reply_text("❌ حدث خطأ!")
    
    @staticmethod
    async def handle_stock_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة كمية المخزون"""
        user = update.effective_user
        
        if not is_admin(user.id):
            return
        
        if 'adding_product' not in context.user_data:
            return
        
        product_data = context.user_data['adding_product']
        
        if product_data.get('step') != 'stock_amount':
            return
        
        is_valid, result = validate_stock(update.message.text)
        
        if is_valid:
            product_data['stock'] = result
            
            await update.message.reply_text(
                "📊 جاري إنشاء المنتج...",
                reply_markup=kb.back_button("admin_products")
            )
            
            # إنشاء المنتج
            product_id = db.add_product(
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                product_type=product_data['type'],
                delivery_content=product_data.get('content'),
                stock=result,
                is_limited=1
            )
            
            if product_id:
                await update.message.reply_text(
                    f"✅ تم إضافة المنتج بنجاح! (المعرف: {product_id})",
                    reply_markup=kb.admin_products()
                )
                
                db.add_log('admin', user.id, 'add_product', f'منتج: {product_id}')
                del context.user_data['adding_product']
            else:
                await update.message.reply_text(
                    "❌ فشل إضافة المنتج!",
                    reply_markup=kb.admin_products()
                )
        else:
            await update.message.reply_text(f"❌ {result}")
    
    @staticmethod
    async def handle_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء البث الجماعي"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        if not is_admin(user.id):
            await query.answer("⛔ غير مصرح لك!", show_alert=True)
            return
        
        context.user_data['broadcasting'] = True
        
        await query.edit_message_text(
            "📢 إرسال رسالة جماعية\n\n"
            "📝 أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n"
            "⚠️ تأكد من صياغة الرسالة بعناية!",
            reply_markup=kb.back_button("admin_settings")
        )
    
    @staticmethod
    async def handle_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تصدير البيانات"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        if not is_admin(user.id):
            await query.answer("⛔ غير مصرح لك!", show_alert=True)
            return
        
        data_type = query.data.split(":")[1]
        
        await query.edit_message_text(
            "⏳ جاري تصدير البيانات...",
            reply_markup=kb.back_button("admin_settings")
        )
        
        try:
            if data_type == 'users':
                data = db.export_data('users')
                filename = f'users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            elif data_type == 'products':
                data = db.export_data('products')
                filename = f'products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            elif data_type == 'orders':
                data = db.export_data('orders')
                filename = f'orders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            elif data_type == 'stats':
                stats = db.get_statistics()
                data = [stats]
                filename = f'stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            else:
                await query.edit_message_text(
                    "❌ نوع بيانات غير معروف!",
                    reply_markup=kb.export_options()
                )
                return
            
            # تصدير إلى CSV
            filepath = await export_to_csv(data, filename)
            
            if filepath:
                with open(filepath, 'rb') as file:
                    await query.message.reply_document(
                        document=file,
                        filename=filename,
                        caption=f"📊 ملف البيانات: {data_type}"
                    )
                
                await query.edit_message_text(
                    "✅ تم التصدير بنجاح!",
                    reply_markup=kb.export_options()
                )
                
                db.add_log('admin', user.id, 'export_data', f'نوع: {data_type}')
            else:
                await query.edit_message_text(
                    "❌ فشل التصدير!",
                    reply_markup=kb.export_options()
                )
        
        except Exception as e:
            logger.error(f"خطأ في التصدير: {e}")
            await query.edit_message_text(
                "❌ حدث خطأ في التصدير!",
                reply_markup=kb.export_options()
            )
    
    @staticmethod
    async def handle_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حظر مستخدم"""
        query = update.callback_query
        await query.answer()
        
        admin = update.effective_user
        if not is_admin(admin.id):
            await query.answer("⛔ غير مصرح لك!", show_alert=True)
            return
        
        user_id = int(query.data.split(":")[1])
        
        if db.ban_user(user_id, "محظور من قبل المسؤول"):
            await query.answer("✅ تم حظر المستخدم!", show_alert=True)
            db.add_log('admin', admin.id, 'ban_user', f'مستخدم: {user_id}')
        else:
            await query.answer("❌ فشل حظر المستخدم!", show_alert=True)
    
    @staticmethod
    async def handle_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء حظر مستخدم"""
        query = update.callback_query
        await query.answer()
        
        admin = update.effective_user
        if not is_admin(admin.id):
            await query.answer("⛔ غير مصرح لك!", show_alert=True)
            return
        
        user_id = int(query.data.split(":")[1])
        
        if db.unban_user(user_id):
            await query.answer("✅ تم إلغاء حظر المستخدم!", show_alert=True)
            db.add_log('admin', admin.id, 'unban_user', f'مستخدم: {user_id}')
        else:
            await query.answer("❌ فشل إلغاء الحظر!", show_alert=True)


# تصدير المعالجات
admin_handler = AdminCommandsHandler()
