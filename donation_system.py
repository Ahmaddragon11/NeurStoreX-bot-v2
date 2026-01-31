# -*- coding: utf-8 -*-
"""
Donation System Module
نظام التبرع للبوت
"""

from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging
from datetime import datetime
import uuid

from database import Database
import config

logger = logging.getLogger(__name__)
db = Database(config.DATABASE_NAME)


class DonationSystem:
    """نظام التبرع المحسّن للبوت"""
    
    # حالات المحادثة
    DONATION_AMOUNT = 1
    DONATION_CONFIRM = 2
    
    @staticmethod
    async def show_donation_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض زر التبرع في الرسالة"""
        from keyboards import Keyboards
        kb = Keyboards()
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                "🎁 <b>ساعد في تطوير البوت</b>\n\n"
                "تبرعاتك تساعدنا على:\n"
                "✨ تطوير ميزات جديدة\n"
                "⚡ تحسين الخدمات\n"
                "🛡 الحفاظ على أمان البوت\n\n"
                "<b>كم تريد أن تتبرع بنجمة؟</b>",
                reply_markup=kb.donation_stars_amounts(),
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                "🎁 <b>ساعد في تطوير البوت</b>\n\n"
                "تبرعاتك تساعدنا على:\n"
                "✨ تطوير ميزات جديدة\n"
                "⚡ تحسين الخدمات\n"
                "🛡 الحفاظ على أمان البوت\n\n"
                "<b>كم تريد أن تتبرع بنجمة؟</b>",
                reply_markup=kb.donation_stars_amounts(),
                parse_mode=ParseMode.HTML
            )
    
    @staticmethod
    async def handle_donation_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
        """معالجة اختيار مبلغ التبرع"""
        user = update.effective_user
        
        # الحصول على query من update
        if hasattr(update, 'callback_query') and update.callback_query:
            query = update.callback_query
            is_callback = True
        else:
            query = None
            is_callback = False
        
        if amount < 1:
            if is_callback:
                await query.answer("❌ يجب أن يكون المبلغ 1 نجمة على الأقل!", show_alert=True)
            else:
                await update.message.reply_text("❌ يجب أن يكون المبلغ 1 نجمة على الأقل!")
            return
        
        if amount > 2500:
            if is_callback:
                await query.answer("❌ الحد الأقصى 2500 نجمة!", show_alert=True)
            else:
                await update.message.reply_text("❌ الحد الأقصى 2500 نجمة!")
            return
        
        # إنشاء رابط دفع
        try:
            payload = f"donation_{user.id}_{uuid.uuid4().hex[:8]}"
            
            prices = [LabeledPrice("تبرع للبوت", amount * 100)]  # بالنقود الصغيرة (1 نجمة = 100 وحدة صغيرة)
            
            await context.bot.send_invoice(
                chat_id=user.id,
                title="🎁 تبرع للبوت",
                description=f"شكراً لدعمك للبوت! تبرع بـ {amount}⭐",
                payload=payload,
                provider_token="",  # للدفع بالنجوم
                currency="XTR",  # عملة النجوم
                prices=prices
            )
            
            # تسجيل المحاولة
            db.add_log('donation', user.id, 'donation_initiated', f'محاولة تبرع: {amount} نجمة')
            
            if is_callback:
                await query.answer(f"✅ تم إنشاء فاتورة التبرع بـ {amount}⭐", show_alert=True)
            else:
                await update.message.reply_text(f"✅ تم إنشاء فاتورة التبرع بـ {amount}⭐")
        
        except Exception as e:
            logger.error(f"خطأ في إنشاء فاتورة التبرع: {e}")
            error_msg = "❌ حدث خطأ في إنشاء فاتورة التبرع!"
            if is_callback:
                await query.answer(error_msg, show_alert=True)
            else:
                await update.message.reply_text(error_msg)
            db.add_log('donation', user.id, 'donation_error', f'خطأ: {str(e)}')
    
    @staticmethod
    async def handle_donation_payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة دفع التبرع الناجح"""
        message = update.message
        payment = message.successful_payment
        user = message.from_user
        
        try:
            # استخراج معلومات التبرع
            payload = payment.invoice_payload
            
            # الحصول على المبلغ
            amount = payment.total_amount // 100  # تحويل من وحدات صغيرة إلى نجوم
            
            # إضافة المساهمة في جدول التبرعات
            db.add_donation_to_bot(
                user_id=user.id,
                amount=amount,
                username=user.username or user.first_name
            )
            
            # إرسال رسالة شكر
            await message.reply_text(
                f"🎉 <b>شكراً لتبرعك!</b>\n\n"
                f"👤 المتبرع: {user.first_name}\n"
                f"💰 المبلغ: {amount}⭐\n\n"
                f"<b>شكراً لدعمك للبوت! ❤️</b>\n\n"
                f"تبرعاتك تساهم في:\n"
                f"✨ تطوير ميزات جديدة\n"
                f"⚡ تحسين الخدمة\n"
                f"🛡 الحفاظ على الأمان",
                parse_mode=ParseMode.HTML
            )
            
            # إخطار الإداريين
            for admin_id in config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f"🎁 <b>تبرع جديد للبوت!</b>\n\n"
                            f"👤 المتبرع: {user.first_name} (@{user.username})\n"
                            f"🆔 المعرف: {user.id}\n"
                            f"💰 المبلغ: {amount}⭐\n"
                            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        ),
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
            
            # تسجيل
            db.add_log('donation', user.id, 'donation_successful', f'تبرع ناجح: {amount} نجمة')
            
        except Exception as e:
            logger.error(f"خطأ في معالجة دفع التبرع: {e}")
            await message.reply_text("❌ حدث خطأ في معالجة التبرع!")
            db.add_log('donation', user.id, 'donation_error', f'خطأ في المعالجة: {str(e)}')
    
    @staticmethod
    async def show_donation_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات التبرعات"""
        query = update.callback_query
        
        try:
            stats = db.get_donation_stats()
            
            stats_text = (
                f"🎁 <b>إحصائيات التبرعات</b>\n\n"
                f"👥 عدد المتبرعين: {stats.get('total_donors', 0)}\n"
                f"⭐ إجمالي المبلغ: {stats.get('total_amount', 0)} نجمة\n"
                f"📊 متوسط التبرع: {stats.get('average_amount', 0)}⭐\n"
                f"🏆 أكبر تبرع: {stats.get('max_amount', 0)}⭐"
            )
            
            from keyboards import Keyboards
            kb = Keyboards()
            
            await query.edit_message_text(
                stats_text,
                reply_markup=kb.back_button("start"),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"خطأ في عرض إحصائيات التبرعات: {e}")
            await query.answer("❌ حدث خطأ!", show_alert=True)
