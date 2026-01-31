# -*- coding: utf-8 -*-
"""
Test Script
سكريبت اختبار البوت
"""

import sys
import os

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """اختبار استيراد الوحدات"""
    print("🔍 اختبار استيراد الوحدات...")
    
    try:
        import config
        print("✅ config.py")
    except Exception as e:
        print(f"❌ config.py: {e}")
        return False
    
    try:
        from database import Database
        print("✅ database.py")
    except Exception as e:
        print(f"❌ database.py: {e}")
        return False
    
    try:
        from keyboards import Keyboards
        print("✅ keyboards.py")
    except Exception as e:
        print(f"❌ keyboards.py: {e}")
        return False
    
    try:
        import handlers
        print("✅ handlers.py")
    except Exception as e:
        print(f"❌ handlers.py: {e}")
        return False
    
    try:
        import payment_handler
        print("✅ payment_handler.py")
    except Exception as e:
        print(f"❌ payment_handler.py: {e}")
        return False
    
    try:
        import utils
        print("✅ utils.py")
    except Exception as e:
        print(f"❌ utils.py: {e}")
        return False
    
    try:
        import admin_handlers
        print("✅ admin_handlers.py")
    except Exception as e:
        print(f"❌ admin_handlers.py: {e}")
        return False
    
    return True


def test_database():
    """اختبار قاعدة البيانات"""
    print("\n🔍 اختبار قاعدة البيانات...")
    
    try:
        from database import Database
        import config
        
        db = Database("test_bot.db")
        print("✅ إنشاء قاعدة البيانات")
        
        # اختبار إضافة مستخدم
        result = db.add_user(123456, "test_user", "Test", "User")
        if result or db.get_user(123456):
            print("✅ إضافة مستخدم")
        else:
            print("❌ فشل إضافة مستخدم")
        
        # اختبار إضافة منتج
        product_id = db.add_product(
            name="منتج تجريبي",
            description="وصف تجريبي",
            price=10,
            product_type="text",
            delivery_content="محتوى تجريبي"
        )
        
        if product_id:
            print(f"✅ إضافة منتج (ID: {product_id})")
        else:
            print("❌ فشل إضافة منتج")
        
        # اختبار الإحصائيات
        stats = db.get_statistics()
        if stats:
            print(f"✅ الإحصائيات (مستخدمون: {stats.get('total_users', 0)})")
        
        # تنظيف
        import os
        db.close()
        if os.path.exists("test_bot.db"):
            os.remove("test_bot.db")
            print("✅ تنظيف ملفات الاختبار")
        
        return True
    
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False


def test_config():
    """اختبار الإعدادات"""
    print("\n🔍 اختبار الإعدادات...")
    
    try:
        import config
        
        # التحقق من التوكن
        if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("⚠️  لم يتم إدخال توكن البوت")
        else:
            print("✅ توكن البوت موجود")
        
        # التحقق من المسؤولين
        if config.ADMIN_IDS == [123456789]:
            print("⚠️  لم يتم تغيير معرفات المسؤولين")
        else:
            print(f"✅ معرفات المسؤولين ({len(config.ADMIN_IDS)})")
        
        # التحقق من الإعدادات الأساسية
        print(f"✅ اسم البوت: {config.BOT_NAME}")
        print(f"✅ الإصدار: {config.BOT_VERSION}")
        print(f"✅ قاعدة البيانات: {config.DATABASE_NAME}")
        
        return True
    
    except Exception as e:
        print(f"❌ خطأ في الإعدادات: {e}")
        return False


def test_telegram_lib():
    """اختبار مكتبة تيليجرام"""
    print("\n🔍 اختبار مكتبة python-telegram-bot...")
    
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application
        print("✅ مكتبة telegram مثبتة")
        return True
    except ImportError:
        print("❌ مكتبة telegram غير مثبتة!")
        print("قم بتثبيتها: pip install python-telegram-bot")
        return False


def main():
    """الدالة الرئيسية"""
    print("=" * 50)
    print("🧪 اختبار بوت متجر تيليجرام الإلكتروني")
    print("=" * 50)
    
    all_tests_passed = True
    
    # اختبار المكتبات
    if not test_telegram_lib():
        all_tests_passed = False
    
    # اختبار الاستيراد
    if not test_imports():
        all_tests_passed = False
    
    # اختبار الإعدادات
    if not test_config():
        all_tests_passed = False
    
    # اختبار قاعدة البيانات
    if not test_database():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✅ جميع الاختبارات نجحت!")
        print("🚀 البوت جاهز للتشغيل")
        print("\nلتشغيل البوت:")
        print("  python main.py")
    else:
        print("❌ بعض الاختبارات فشلت")
        print("الرجاء مراجعة الأخطاء أعلاه")
    print("=" * 50)


if __name__ == "__main__":
    main()
