# -*- coding: utf-8 -*-
"""
اختبارات شاملة للبوت
Comprehensive Test Suite
"""

import unittest
import sqlite3
import os
import tempfile
from datetime import datetime
import logging

from database import Database
from config import (
    MIN_PRODUCT_PRICE, MAX_PRODUCT_PRICE,
    DATABASE_NAME, REFERRAL_REWARD_STARS
)

# إعداد التسجيل
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestDatabase(unittest.TestCase):
    """اختبارات قاعدة البيانات"""
    
    def setUp(self):
        """إعداد الاختبار"""
        # استخدام قاعدة بيانات مؤقتة للاختبار
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        self.db_name = self.test_db.name
        
        # إنشاء مثيل من قاعدة البيانات
        self.db = Database(self.db_name)
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        self.db.close()
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
    
    # ==================== اختبارات المستخدمين ====================
    
    def test_add_user(self):
        """اختبار إضافة مستخدم"""
        result = self.db.add_user(
            user_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        self.assertTrue(result)
        
        # التحقق من إضافة المستخدم
        user = self.db.get_user(123456)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], "testuser")
        self.assertEqual(user['first_name'], "Test")
    
    def test_get_user_not_found(self):
        """اختبار البحث عن مستخدم غير موجود"""
        user = self.db.get_user(999999)
        self.assertIsNone(user)
    
    def test_ban_user(self):
        """اختبار حظر مستخدم"""
        # إضافة مستخدم
        self.db.add_user(123456, "testuser", "Test", "User")
        
        # حظر المستخدم
        result = self.db.ban_user(123456, "اختبار")
        self.assertTrue(result)
        
        # التحقق من الحظر
        user = self.db.get_user(123456)
        self.assertEqual(user['is_banned'], 1)
        self.assertEqual(user['ban_reason'], "اختبار")
    
    def test_unban_user(self):
        """اختبار إلغاء حظر مستخدم"""
        # إضافة ثم حظر مستخدم
        self.db.add_user(123456, "testuser", "Test", "User")
        self.db.ban_user(123456, "اختبار")
        
        # إلغاء الحظر
        result = self.db.unban_user(123456)
        self.assertTrue(result)
        
        # التحقق
        user = self.db.get_user(123456)
        self.assertEqual(user['is_banned'], 0)
        self.assertIsNone(user['ban_reason'])
    
    def test_update_user_activity(self):
        """اختبار تحديث نشاط المستخدم"""
        self.db.add_user(123456, "testuser", "Test", "User")
        
        before = datetime.now()
        self.db.update_user_activity(123456)
        after = datetime.now()
        
        user = self.db.get_user(123456)
        # التحقق من تحديث الوقت
        self.assertIsNotNone(user['last_activity'])
    
    # ==================== اختبارات المنتجات ====================
    
    def test_add_product(self):
        """اختبار إضافة منتج"""
        product_id = self.db.add_product(
            name="منتج اختبار",
            description="وصف اختبار",
            price=100,
            product_type="file",
            stock=10,
            is_limited=1
        )
        
        self.assertIsNotNone(product_id)
        
        # التحقق من المنتج
        product = self.db.get_product(product_id)
        self.assertEqual(product['name'], "منتج اختبار")
        self.assertEqual(product['price'], 100)
        self.assertEqual(product['type'], "file")
    
    def test_update_product(self):
        """اختبار تحديث منتج"""
        product_id = self.db.add_product(
            name="المنتج الأول",
            description="وصف",
            price=100,
            product_type="code"
        )
        
        # تحديث المنتج
        result = self.db.update_product(
            product_id,
            name="المنتج المحدّث",
            price=150
        )
        self.assertTrue(result)
        
        # التحقق
        product = self.db.get_product(product_id)
        self.assertEqual(product['name'], "المنتج المحدّث")
        self.assertEqual(product['price'], 150)
    
    def test_delete_product(self):
        """اختبار حذف منتج"""
        product_id = self.db.add_product(
            name="منتج حذف",
            description="سيتم حذفه",
            price=50,
            product_type="text"
        )
        
        result = self.db.delete_product(product_id)
        self.assertTrue(result)
        
        # التحقق من الحذف
        product = self.db.get_product(product_id)
        self.assertIsNone(product)
    
    def test_get_active_products(self):
        """اختبار جلب المنتجات النشطة"""
        # إضافة منتجات
        product1 = self.db.add_product("منتج 1", "وصف", 100, "file")
        product2 = self.db.add_product("منتج 2", "وصف", 200, "code")
        
        # جلب المنتجات النشطة
        products = self.db.get_active_products()
        self.assertEqual(len(products), 2)
    
    def test_decrease_stock(self):
        """اختبار تقليل المخزون"""
        product_id = self.db.add_product(
            name="منتج مخزون",
            description="اختبار",
            price=100,
            product_type="file",
            stock=5,
            is_limited=1
        )
        
        # تقليل المخزون
        result = self.db.decrease_stock(product_id)
        self.assertTrue(result)
        
        # التحقق
        product = self.db.get_product(product_id)
        self.assertEqual(product['stock'], 4)
    
    # ==================== اختبارات الرصيد ====================
    
    def test_add_user_balance(self):
        """اختبار إضافة رصيد"""
        self.db.add_user(123456, "testuser", "Test", "User")
        
        # إضافة رصيد
        result = self.db.add_user_balance(123456, 100)
        self.assertTrue(result)
        
        # التحقق
        balance = self.db.get_user_balance(123456)
        self.assertEqual(balance, 100)
    
    def test_subtract_user_balance(self):
        """اختبار خصم رصيد"""
        self.db.add_user(123456, "testuser", "Test", "User")
        self.db.add_user_balance(123456, 100)
        
        # خصم رصيد
        result = self.db.subtract_user_balance(123456, 30)
        self.assertTrue(result)
        
        # التحقق
        balance = self.db.get_user_balance(123456)
        self.assertEqual(balance, 70)
    
    def test_subtract_balance_insufficient(self):
        """اختبار خصم رصيد أكبر من المتوفر"""
        self.db.add_user(123456, "testuser", "Test", "User")
        self.db.add_user_balance(123456, 50)
        
        # محاولة خصم 100 (أكثر من المتوفر)
        result = self.db.subtract_user_balance(123456, 100)
        self.assertFalse(result)
        
        # التحقق من عدم تغيير الرصيد
        balance = self.db.get_user_balance(123456)
        self.assertEqual(balance, 50)
    
    def test_transfer_balance(self):
        """اختبار تحويل الرصيد"""
        self.db.add_user(111111, "user1", "User", "One")
        self.db.add_user(222222, "user2", "User", "Two")
        
        # إضافة رصيد للمستخدم الأول
        self.db.add_user_balance(111111, 100)
        
        # تحويل رصيد
        result = self.db.transfer_balance(111111, 222222, 50)
        self.assertTrue(result)
        
        # التحقق
        balance1 = self.db.get_user_balance(111111)
        balance2 = self.db.get_user_balance(222222)
        
        self.assertEqual(balance1, 50)
        self.assertEqual(balance2, 50)
    
    # ==================== اختبارات الأكواد ====================
    
    def test_add_codes(self):
        """اختبار إضافة أكواد"""
        product_id = self.db.add_product(
            name="منتج أكواد",
            description="اختبار",
            price=50,
            product_type="code"
        )
        
        codes = ["CODE123", "CODE456", "CODE789"]
        result = self.db.add_codes(product_id, codes)
        self.assertTrue(result)
        
        # التحقق
        available = self.db.get_available_codes_count(product_id)
        self.assertEqual(available, 3)
    
    def test_get_unused_code(self):
        """اختبار جلب كود غير مستخدم"""
        product_id = self.db.add_product(
            name="منتج أكواد",
            description="اختبار",
            price=50,
            product_type="code"
        )
        
        self.db.add_codes(product_id, ["CODE123", "CODE456"])
        
        # جلب كود غير مستخدم
        code = self.db.get_unused_code(product_id, 123456)
        self.assertIsNotNone(code)
        self.assertIn(code, ["CODE123", "CODE456"])
        
        # التحقق من عدد الأكواد المتاحة (يجب أن ينقص)
        available = self.db.get_available_codes_count(product_id)
        self.assertEqual(available, 1)
    
    # ==================== اختبارات الطلبات ====================
    
    def test_create_order(self):
        """اختبار إنشاء طلب"""
        self.db.add_user(123456, "testuser", "Test", "User")
        product_id = self.db.add_product(
            name="منتج شراء",
            description="اختبار",
            price=100,
            product_type="file"
        )
        
        # إنشاء طلب
        order_id = self.db.create_order(
            user_id=123456,
            product_id=product_id,
            product_name="منتج شراء",
            payment_id="PAYMENT_123",
            price=100,
            discount_amount=0
        )
        
        self.assertIsNotNone(order_id)
    
    def test_duplicate_order_prevention(self):
        """اختبار منع الطلبات المكررة"""
        self.db.add_user(123456, "testuser", "Test", "User")
        product_id = self.db.add_product(
            name="منتج",
            description="اختبار",
            price=100,
            product_type="file"
        )
        
        # إنشاء طلب الأول
        order1 = self.db.create_order(
            user_id=123456,
            product_id=product_id,
            product_name="منتج",
            payment_id="PAYMENT_123",
            price=100
        )
        
        # محاولة إنشاء طلب بنفس معرف الدفع
        order2 = self.db.create_order(
            user_id=123456,
            product_id=product_id,
            product_name="منتج",
            payment_id="PAYMENT_123",
            price=100
        )
        
        # يجب أن يكون الثاني None (منع التكرار)
        self.assertIsNone(order2)
    
    def test_update_order_status(self):
        """اختبار تحديث حالة الطلب"""
        self.db.add_user(123456, "testuser", "Test", "User")
        product_id = self.db.add_product(
            name="منتج",
            description="اختبار",
            price=100,
            product_type="file"
        )
        
        order_id = self.db.create_order(
            user_id=123456,
            product_id=product_id,
            product_name="منتج",
            payment_id="PAYMENT_123",
            price=100
        )
        
        # تحديث الحالة
        result = self.db.update_order_status(
            order_id,
            status='completed',
            delivery_status='delivered'
        )
        self.assertTrue(result)
    
    def test_complete_purchase(self):
        """اختبار إتمام الشراء وتحديث الإحصائيات"""
        self.db.add_user(123456, "testuser", "Test", "User")
        product_id = self.db.add_product(
            name="منتج",
            description="اختبار",
            price=100,
            product_type="file"
        )
        
        # إتمام الشراء
        result = self.db.complete_purchase(123456, product_id, 100)
        self.assertTrue(result)
        
        # التحقق من الإحصائيات
        user = self.db.get_user(123456)
        self.assertEqual(user['total_spent'], 100)
        self.assertEqual(user['total_purchases'], 1)
        
        product = self.db.get_product(product_id)
        self.assertEqual(product['sales_count'], 1)
    
    # ==================== اختبارات الإعدادات ====================
    
    def test_set_and_get_setting(self):
        """اختبار تعيين وجلب الإعدادات"""
        result = self.db.set_setting("maintenance_mode", "True")
        self.assertTrue(result)
        
        value = self.db.get_setting("maintenance_mode")
        self.assertEqual(value, "True")
    
    def test_get_all_settings(self):
        """اختبار جلب جميع الإعدادات"""
        self.db.set_setting("key1", "value1")
        self.db.set_setting("key2", "value2")
        
        settings = self.db.get_all_settings()
        self.assertEqual(settings['key1'], "value1")
        self.assertEqual(settings['key2'], "value2")
    
    # ==================== اختبارات السجلات ====================
    
    def test_add_log(self):
        """اختبار إضافة سجل"""
        result = self.db.add_log(
            log_type='info',
            user_id=123456,
            action='test_action',
            details='تفاصيل الاختبار'
        )
        self.assertTrue(result)
    
    def test_get_logs(self):
        """اختبار جلب السجلات"""
        self.db.add_log('info', 123456, 'action1', 'تفاصيل')
        self.db.add_log('error', 123456, 'action2', 'خطأ')
        
        logs = self.db.get_logs(limit=10)
        self.assertGreaterEqual(len(logs), 2)
    
    # ==================== اختبارات الإحصائيات ====================
    
    def test_get_statistics(self):
        """اختبار جلب الإحصائيات"""
        self.db.add_user(111111, "user1", "User", "One")
        self.db.add_user(222222, "user2", "User", "Two")
        
        product_id = self.db.add_product(
            name="منتج",
            description="اختبار",
            price=100,
            product_type="file"
        )
        
        self.db.complete_purchase(111111, product_id, 100)
        
        stats = self.db.get_statistics()
        self.assertGreaterEqual(stats['total_users'], 2)
        self.assertGreaterEqual(stats['active_products'], 1)
    
    # ==================== اختبارات معدل الطلبات ====================
    
    def test_rate_limiting(self):
        """اختبار حماية معدل الطلبات"""
        user_id = 123456
        
        # محاولة 20 طلب (الحد الأقصى)
        for i in range(20):
            result = self.db.check_rate_limit(user_id, max_requests=20)
            self.assertTrue(result)
        
        # الطلب الـ 21 يجب أن ينجح
        result = self.db.check_rate_limit(user_id, max_requests=20)
        self.assertFalse(result)


class TestIntegration(unittest.TestCase):
    """اختبارات التكامل"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        self.db_name = self.test_db.name
        self.db = Database(self.db_name)
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        self.db.close()
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
    
    def test_complete_purchase_flow(self):
        """اختبار تدفق شراء كامل"""
        # 1. إضافة مستخدمين
        user_id = 123456
        referrer_id = 789012
        
        self.db.add_user(user_id, "buyer", "Buyer", "User", referrer_id=referrer_id)
        self.db.add_user(referrer_id, "referrer", "Referrer", "User")
        
        # 2. إضافة منتج
        product_id = self.db.add_product(
            name="منتج اختبار شامل",
            description="وصف",
            price=1000,
            product_type="file",
            stock=10,
            is_limited=1
        )
        
        # 3. إنشاء طلب
        order_id = self.db.create_order(
            user_id=user_id,
            product_id=product_id,
            product_name="منتج اختبار شامل",
            payment_id="PAYMENT_FULL_TEST",
            price=1000,
            discount_amount=100
        )
        
        self.assertIsNotNone(order_id)
        
        # 4. تقليل المخزون
        self.db.decrease_stock(product_id)
        
        # 5. إتمام الشراء
        self.db.complete_purchase(user_id, product_id, 900)
        self.db.update_order_status(order_id, 'completed', 'delivered')
        
        # 6. إضافة رصيد الإحالة
        self.db.add_user_balance(referrer_id, REFERRAL_REWARD_STARS)
        
        # 7. التحقق من النتائج
        buyer = self.db.get_user(user_id)
        self.assertEqual(buyer['total_purchases'], 1)
        self.assertEqual(buyer['total_spent'], 900)
        
        referrer = self.db.get_user(referrer_id)
        self.assertEqual(referrer['balance'], REFERRAL_REWARD_STARS)
        
        product = self.db.get_product(product_id)
        self.assertEqual(product['stock'], 9)
        self.assertEqual(product['sales_count'], 1)


def run_tests():
    """تشغيل جميع الاختبارات"""
    # إنشاء مجموعة الاختبارات
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # إضافة الاختبارات
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # تشغيل الاختبارات
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # إرجاع النتيجة
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 بدء الاختبارات الشاملة للبوت")
    print("=" * 60)
    
    success = run_tests()
    
    print("=" * 60)
    if success:
        print("✅ جميع الاختبارات نجحت!")
    else:
        print("❌ بعض الاختبارات فشلت!")
    
    exit(0 if success else 1)
