# -*- coding: utf-8 -*-
"""
Telegram Store Bot - Main File
بوت متجر تيليجرام الإلكتروني
الملف الرئيسي
"""

import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters
)

# استيراد الوحدات
import config
from database import Database
from handlers import (
    start_handler,
    callback_handler,
    message_handler
)
from payment_handler import (
    precheckout_handler,
    successful_payment_handler
)
from utils import clean_temp_files

# إعداد نظام التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    # التحقق من التوكن
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ خطأ: لم يتم إدخال توكن البوت!")
        logger.error("الرجاء فتح ملف config.py ووضع التوكن الخاص بك")
        sys.exit(1)
    
    # التحقق من معرفات المسؤولين
    if config.ADMIN_IDS == [123456789]:
        logger.warning("⚠️ تحذير: لم يتم تغيير معرفات المسؤولين!")
        logger.warning("الرجاء فتح ملف config.py ووضع معرفك الحقيقي")
    
    logger.info("🚀 بدء تشغيل البوت...")
    
    # إنشاء قاعدة البيانات
    try:
        db = Database(config.DATABASE_NAME)
        logger.info("✅ تم إنشاء قاعدة البيانات بنجاح")
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
        sys.exit(1)
    
    # تنظيف الملفات المؤقتة
    clean_temp_files()
    
    # إنشاء التطبيق
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # ==================== معالجات الأوامر ====================
    application.add_handler(CommandHandler("start", start_handler))
    
    # ==================== معالجات الأزرار ====================
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # ==================== معالجات الرسائل ====================
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    ))
    
    # ==================== معالجات الدفع ====================
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(
        filters.SUCCESSFUL_PAYMENT,
        successful_payment_handler
    ))
    
    # ==================== معالج الأخطاء ====================
    async def error_handler(update: Update, context):
        """معالج الأخطاء العام"""
        logger.error(f"حدث خطأ: {context.error}")
        
        if update and update.effective_user:
            try:
                error_message = (
                    "❌ عذراً، حدث خطأ غير متوقع!\n"
                    "الرجاء المحاولة مرة أخرى أو التواصل مع الدعم."
                )
                
                if update.message:
                    await update.message.reply_text(error_message)
                elif update.callback_query:
                    await update.callback_query.answer(error_message, show_alert=True)
            except:
                pass
    
    application.add_error_handler(error_handler)
    
    # ==================== بدء التشغيل ====================
    logger.info("✅ تم تهيئة البوت بنجاح")
    logger.info(f"📝 اسم البوت: {config.BOT_NAME}")
    logger.info(f"🔢 الإصدار: {config.BOT_VERSION}")
    logger.info(f"👥 عدد المسؤولين: {len(config.ADMIN_IDS)}")
    logger.info("🎯 البوت جاهز لاستقبال الرسائل...")
    
    # تشغيل البوت
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.critical(f"❌ خطأ حرج: {e}")
        sys.exit(1)
