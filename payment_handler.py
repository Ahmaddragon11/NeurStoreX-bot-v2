# -*- coding: utf-8 -*-
"""
Payment Handler Module
معالج الدفع بنجوم تيليجرام
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging
from datetime import datetime

from database import Database
from utils import send_product_to_user
import config

logger = logging.getLogger(__name__)
db = Database(config.DATABASE_NAME)


async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج ما قبل الدفع - للتحقق من الطلب"""
    query = update.pre_checkout_query
    
    try:
        # استخراج معلومات المنتج من payload
        payload = query.invoice_payload
        parts = payload.split("_")
        
        if len(parts) < 3 or parts[0] != "product":
            await query.answer(ok=False, error_message="❌ فاتورة غير صالحة!")
            return
        
        product_id = int(parts[1])
        user_id = int(parts[2])
        
        # التحقق من صحة المستخدم
        if query.from_user.id != user_id:
            await query.answer(ok=False, error_message="❌ المستخدم غير مطابق!")
            db.add_log('security', user_id, 'payment_fraud_attempt', 
                      f'محاولة دفع من مستخدم مختلف')
            return
        
        # التحقق من وجود المنتج
        product = db.get_product(product_id)
        
        if not product:
            await query.answer(ok=False, error_message="❌ المنتج غير موجود!")
            return
        
        # التحقق من نشاط المنتج
        if not product['is_active']:
            await query.answer(ok=False, error_message="❌ المنتج غير متاح!")
            return
        
        # التحقق من المخزون
        if product['is_limited']:
            if product['stock'] <= 0:
                await query.answer(ok=False, error_message=config.MESSAGES['out_of_stock'])
                return
        
        # التحقق من الأكواد (للمنتجات من نوع code)
        if product['type'] == 'code':
            available_codes = db.get_available_codes_count(product_id)
            if available_codes <= 0:
                await query.answer(ok=False, error_message=config.MESSAGES['out_of_stock'])
                return
        
        # التحقق من السعر
        expected_price = product['price']
        discount = product.get('discount_percentage', 0)
        final_price = expected_price - (expected_price * discount // 100)
        
        if query.total_amount != final_price:
            await query.answer(ok=False, error_message="❌ السعر غير مطابق!")
            db.add_log('security', user_id, 'price_manipulation', 
                      f'محاولة تعديل السعر للمنتج {product_id}')
            return
        
        # كل شيء على ما يرام، قبول الدفع
        await query.answer(ok=True)
        
        db.add_log('payment', user_id, 'precheckout_approved', 
                  f'منتج: {product_id}, سعر: {final_price}')
    
    except Exception as e:
        logger.error(f"خطأ في precheckout: {e}")
        await query.answer(ok=False, error_message="❌ حدث خطأ في معالجة الدفع!")


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الدفع الناجح - توصيل المنتج"""
    message = update.message
    payment = message.successful_payment
    user = message.from_user
    
    try:
        # استخراج معلومات المنتج
        payload = payment.invoice_payload
        parts = payload.split("_")
        
        product_id = int(parts[1])
        user_id = int(parts[2])
        
        # معرف الدفع الفريد من تيليجرام
        telegram_payment_id = payment.telegram_payment_charge_id
        
        # التحقق من عدم تكرار الطلب
        existing_order = db.create_order(
            user_id=user_id,
            product_id=product_id,
            product_name=payment.invoice_payload.split("_")[0] if len(parts) > 3 else "منتج",
            payment_id=telegram_payment_id,
            price=payment.total_amount,
            discount_amount=0
        )
        
        if not existing_order:
            # الطلب موجود مسبقاً (حماية من التكرار)
            logger.warning(f"طلب مكرر: {telegram_payment_id}")
            await message.reply_text(
                "⚠️ تم معالجة هذا الدفع مسبقاً!\n"
                "إذا لم تستلم المنتج، تواصل مع الدعم."
            )
            return
        
        # جلب تفاصيل المنتج
        product = db.get_product(product_id)
        
        if not product:
            await message.reply_text(
                "❌ حدث خطأ: المنتج غير موجود!\n"
                "تم استرجاع مبلغك تلقائياً."
            )
            db.update_order_status(existing_order, 'failed', 'failed', 'المنتج غير موجود')
            return
        
        # تقليل المخزون (مع قفل لمنع race conditions)
        if product['is_limited']:
            stock_decreased = db.decrease_stock(product_id)
            if not stock_decreased:
                await message.reply_text(
                    "❌ نفذت الكمية المتاحة!\n"
                    "سيتم استرجاع مبلغك."
                )
                db.update_order_status(existing_order, 'failed', 'failed', 'نفذ المخزون')
                return
        
        # توصيل المنتج حسب نوعه
        delivery_success = await send_product_to_user(
            context=context,
            user_id=user_id,
            product=product,
            order_id=existing_order
        )
        
        if delivery_success:
            # تحديث حالة الطلب
            db.update_order_status(
                existing_order,
                status='completed',
                delivery_status='delivered'
            )
            
            # تحديث إحصائيات الشراء
            db.complete_purchase(user_id, product_id, payment.total_amount)
            
            # رسالة نجاح
            success_message = (
                f"✅ {config.MESSAGES['purchase_success']}\n\n"
                f"📦 المنتج: {product['name']}\n"
                f"💰 المبلغ المدفوع: {payment.total_amount} ⭐\n"
                f"🧾 رقم الطلب: #{existing_order}\n\n"
                f"شكراً لثقتك بنا! 🎉"
            )
            
            await message.reply_text(success_message)
            
            # إشعار المسؤول
            if config.NOTIFY_ADMIN_ON_PURCHASE:
                for admin_id in config.ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=(
                                f"🔔 عملية شراء جديدة!\n\n"
                                f"👤 المستخدم: {user.first_name} (@{user.username or 'بدون'})\n"
                                f"📦 المنتج: {product['name']}\n"
                                f"💰 المبلغ: {payment.total_amount} ⭐\n"
                                f"🧾 الطلب: #{existing_order}"
                            )
                        )
                    except Exception as e:
                        logger.error(f"فشل إرسال إشعار للمسؤول: {e}")
            
            # معالجة مكافأة الإحالة
            if config.ENABLE_REFERRAL:
                user_data = db.get_user(user_id)
                if user_data and user_data.get('referrer_id'):
                    # التحقق إذا كانت أول عملية شراء
                    if user_data['total_purchases'] == 1:
                        referrer_id = user_data['referrer_id']
                        # إضافة مكافأة للمُحيل
                        db.update_user_activity(referrer_id)
                        
                        # يمكن إضافة رصيد أو مكافأة للمُحيل هنا
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text=(
                                    f"🎉 تهانينا!\n\n"
                                    f"قام أحد المستخدمين الذين أحلتهم بإجراء أول عملية شراء!\n"
                                    f"🎁 مكافأتك: {config.REFERRAL_REWARD_STARS} ⭐"
                                )
                            )
                        except Exception as e:
                            logger.error(f"فشل إرسال إشعار الإحالة: {e}")
            
            db.add_log('purchase', user_id, 'purchase_completed', 
                      f'منتج: {product_id}, طلب: {existing_order}')
        
        else:
            # فشل التوصيل
            db.update_order_status(existing_order, 'failed', 'failed', 'فشل التوصيل')
            
            await message.reply_text(
                f"❌ {config.MESSAGES['purchase_failed']}\n\n"
                "تم تسجيل الطلب ولكن فشل التوصيل.\n"
                "تواصل مع الدعم مع رقم الطلب: #{existing_order}"
            )
            
            db.add_log('error', user_id, 'delivery_failed', f'طلب: {existing_order}')
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الدفع الناجح: {e}")
        await message.reply_text(
            "❌ حدث خطأ في معالجة عملية الشراء!\n"
            "تواصل مع الدعم للمساعدة."
        )
        
        db.add_log('error', user.id, 'payment_processing_error', str(e))


async def refund_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استرداد المبالغ (إن وجد)"""
    # يمكن إضافة منطق استرداد المبالغ هنا إذا لزم الأمر
    pass
