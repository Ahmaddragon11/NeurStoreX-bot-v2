# -*- coding: utf-8 -*-
"""
اختبار شامل لنظام التبرع والميزات الجديدة
"""

import unittest
import sqlite3
from database import Database
import config

class TestDonationSystem(unittest.TestCase):
    """اختبار نظام التبرع"""
    
    def setUp(self):
        """إعداد قبل كل اختبار"""
        self.db = Database(":memory:")
        config.BOT_TOKEN = "test_token"
    
    def test_add_donation_to_bot(self):
        """اختبار إضافة تبرع للبوت"""
        result = self.db.add_donation_to_bot(
            user_id=123,
            amount=100,
            username="test_user"
        )
        self.assertTrue(result)
    
    def test_get_donation_stats(self):
        """اختبار جلب إحصائيات التبرعات"""
        # إضافة تبرعات للاختبار
        self.db.add_donation_to_bot(123, 100, "user1")
        self.db.add_donation_to_bot(456, 200, "user2")
        self.db.add_donation_to_bot(789, 50, "user3")
        
        stats = self.db.get_donation_stats()
        
        self.assertEqual(stats['total_amount'], 350)
        self.assertEqual(stats['total_donors'], 3)
        self.assertEqual(stats['average_amount'], 116)
        self.assertEqual(stats['max_amount'], 200)
    
    def test_get_bot_donations(self):
        """اختبار جلب التبرعات"""
        self.db.add_donation_to_bot(123, 100, "user1")
        self.db.add_donation_to_bot(456, 200, "user2")
        
        donations = self.db.get_bot_donations(limit=10)
        
        self.assertEqual(len(donations), 2)
        self.assertEqual(donations[0]['amount'], 200)  # الأحدث أولاً
        self.assertEqual(donations[1]['amount'], 100)
    
    def test_donation_min_max(self):
        """اختبار حدود التبرع"""
        self.assertGreaterEqual(config.MIN_DONATION_AMOUNT, 1)
        self.assertLessEqual(config.MAX_DONATION_AMOUNT, 2500)
    
    def test_config_values(self):
        """اختبار قيم الإعدادات"""
        self.assertTrue(hasattr(config, 'ENABLE_DONATIONS'))
        self.assertTrue(hasattr(config, 'MIN_DONATION_AMOUNT'))
        self.assertTrue(hasattr(config, 'MAX_DONATION_AMOUNT'))


class TestDatabase(unittest.TestCase):
    """اختبار قاعدة البيانات"""
    
    def setUp(self):
        """إعداد قبل كل اختبار"""
        self.db = Database(":memory:")
    
    def test_table_creation(self):
        """اختبار إنشاء الجداول"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # التحقق من وجود جدول التبرعات
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bot_donations'")
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
    
    def test_index_creation(self):
        """اختبار إنشاء الفهارس"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # التحقق من وجود فهرس
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_bot_donations%'")
        result = cursor.fetchall()
        
        self.assertGreater(len(result), 0)
    
    def test_user_creation(self):
        """اختبار إضافة مستخدم"""
        result = self.db.add_user(
            user_id=123,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        self.assertTrue(result)
        
        user = self.db.get_user(123)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], "testuser")


class TestConfigValues(unittest.TestCase):
    """اختبار قيم الإعدادات"""
    
    def test_bot_version(self):
        """اختبار إصدار البوت"""
        self.assertIsNotNone(config.BOT_VERSION)
    
    def test_emoji_config(self):
        """اختبار الإيموجي"""
        self.assertIn('store', config.EMOJI)
        self.assertIn('star', config.EMOJI)
        self.assertIn('money', config.EMOJI)
    
    def test_messages_config(self):
        """اختبار الرسائل"""
        self.assertIn('welcome', config.MESSAGES)
        self.assertIn('help', config.MESSAGES)
        self.assertIn('purchase_success', config.MESSAGES)
    
    def test_payment_settings(self):
        """اختبار إعدادات الدفع"""
        self.assertGreaterEqual(config.MIN_PRODUCT_PRICE, 1)
        self.assertLessEqual(config.MAX_PRODUCT_PRICE, 2500)


class TestSecurity(unittest.TestCase):
    """اختبار الأمان"""
    
    def test_admin_ids_format(self):
        """اختبار تنسيق معرفات الإداريين"""
        self.assertIsInstance(config.ADMIN_IDS, list)
        for admin_id in config.ADMIN_IDS:
            self.assertIsInstance(admin_id, int)
    
    def test_log_functionality(self):
        """اختبار وظيفة السجلات"""
        db = Database(":memory:")
        result = db.add_log('test', 123, 'test_action', 'test details')
        self.assertTrue(result)


def run_tests():
    """تشغيل جميع الاختبارات"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # إضافة الاختبارات
    suite.addTests(loader.loadTestsFromTestCase(TestDonationSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValues))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    
    # تشغيل الاختبارات
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 بدء الاختبارات الشاملة...")
    print("=" * 50)
    
    success = run_tests()
    
    print("=" * 50)
    if success:
        print("✅ جميع الاختبارات نجحت!")
    else:
        print("❌ بعض الاختبارات فشلت!")
    
    exit(0 if success else 1)
