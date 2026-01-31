# -*- coding: utf-8 -*-
"""
Database Management Module
إدارة قاعدة البيانات
"""

import sqlite3
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class Database:
    """فئة إدارة قاعدة البيانات مع حماية من التعارضات"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_name: str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_name: str):
        if not hasattr(self, 'initialized'):
            self.db_name = db_name
            self.local = threading.local()
            self.initialized = True
            self._create_tables()
    
    def _get_connection(self):
        """الحصول على اتصال خاص بكل thread"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(
                self.db_name,
                check_same_thread=False,
                timeout=30
            )
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def _create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                total_purchases INTEGER DEFAULT 0,
                referrer_id INTEGER,
                referral_count INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                language TEXT DEFAULT 'ar'
            )
        """)
        
        # جدول المنتجات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                type TEXT NOT NULL,
                delivery_content TEXT,
                stock INTEGER DEFAULT -1,
                is_limited INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                category TEXT DEFAULT 'عام',
                image_url TEXT,
                discount_percentage INTEGER DEFAULT 0,
                sales_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول الأكواد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                code_value TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """)
        
        # جدول الطلبات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                payment_id TEXT UNIQUE NOT NULL,
                price INTEGER NOT NULL,
                discount_amount INTEGER DEFAULT 0,
                final_price INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                delivery_status TEXT DEFAULT 'pending',
                delivery_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        
        # جدول السجلات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول الإحصائيات اليومية
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                total_sales INTEGER DEFAULT 0,
                total_revenue INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0
            )
        """)
        
        # جدول معدل الطلبات (للحماية من الفلود)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_id INTEGER PRIMARY KEY,
                request_count INTEGER DEFAULT 0,
                last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0,
                is_temp_banned INTEGER DEFAULT 0,
                temp_ban_until TIMESTAMP
            )
        """)
        
        # جدول الإعدادات القابلة للتعديل
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول الفئات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '📦',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # إنشاء الفهارس لتحسين الأداء
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_codes_product ON codes(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_codes_used ON codes(is_used)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_type ON logs(type)")
        
        conn.commit()
        logger.info("تم إنشاء جداول قاعدة البيانات بنجاح")
    
    # ==================== دوال المستخدمين ====================
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, referrer_id: int = None) -> bool:
        """إضافة مستخدم جديد"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, referrer_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, referrer_id))
            
            if referrer_id:
                cursor.execute("""
                    UPDATE users SET referral_count = referral_count + 1
                    WHERE user_id = ?
                """, (referrer_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"خطأ في إضافة مستخدم: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """الحصول على بيانات مستخدم"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"خطأ في جلب بيانات المستخدم: {e}")
            return None
    
    def update_user_activity(self, user_id: int):
        """تحديث آخر نشاط للمستخدم"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
        except Exception as e:
            logger.error(f"خطأ في تحديث نشاط المستخدم: {e}")
    
    def ban_user(self, user_id: int, reason: str = None) -> bool:
        """حظر مستخدم"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET is_banned = 1, ban_reason = ?
                WHERE user_id = ?
            """, (reason, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في حظر المستخدم: {e}")
            return False
    
    def unban_user(self, user_id: int) -> bool:
        """إلغاء حظر مستخدم"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET is_banned = 0, ban_reason = NULL
                WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في إلغاء حظر المستخدم: {e}")
            return False
    
    def get_all_users(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """الحصول على جميع المستخدمين"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM users ORDER BY join_date DESC"
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب المستخدمين: {e}")
            return []
    
    def get_users_count(self) -> int:
        """عدد المستخدمين الكلي"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM users")
            return cursor.fetchone()['count']
        except Exception as e:
            logger.error(f"خطأ في عد المستخدمين: {e}")
            return 0
    
    # ==================== دوال المنتجات ====================
    
    def add_product(self, name: str, description: str, price: int, 
                    product_type: str, delivery_content: str = None,
                    stock: int = -1, is_limited: int = 0, 
                    category: str = 'عام') -> Optional[int]:
        """إضافة منتج جديد"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO products 
                (name, description, price, type, delivery_content, stock, is_limited, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, description, price, product_type, delivery_content, 
                  stock, is_limited, category))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"خطأ في إضافة منتج: {e}")
            return None
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """الحصول على منتج"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"خطأ في جلب المنتج: {e}")
            return None
    
    def get_active_products(self, category: str = None, 
                           limit: int = None, offset: int = 0) -> List[Dict]:
        """الحصول على المنتجات النشطة"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM products WHERE is_active = 1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب المنتجات: {e}")
            return []
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        """تحديث منتج"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            updates = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['name', 'description', 'price', 'type', 'delivery_content',
                          'stock', 'is_limited', 'is_active', 'category', 'discount_percentage']:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            values.append(product_id)
            query = f"UPDATE products SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"خطأ في تحديث المنتج: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """حذف منتج"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"خطأ في حذف المنتج: {e}")
            return False
    
    def decrease_stock(self, product_id: int) -> bool:
        """تقليل المخزون (مع قفل معاملة آمن)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # بدء معاملة حصرية
            cursor.execute("BEGIN EXCLUSIVE")
            
            cursor.execute("""
                UPDATE products SET stock = stock - 1
                WHERE id = ? AND is_limited = 1 AND stock > 0
            """, (product_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
        except Exception as e:
            conn.rollback()
            logger.error(f"خطأ في تقليل المخزون: {e}")
            return False
    
    # ==================== دوال الأكواد ====================
    
    def add_codes(self, product_id: int, codes: List[str]) -> bool:
        """إضافة أكواد لمنتج"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.executemany("""
                INSERT INTO codes (product_id, code_value)
                VALUES (?, ?)
            """, [(product_id, code) for code in codes])
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في إضافة الأكواد: {e}")
            return False
    
    def get_unused_code(self, product_id: int, user_id: int) -> Optional[str]:
        """الحصول على كود غير مستخدم (مع قفل)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("BEGIN EXCLUSIVE")
            
            cursor.execute("""
                SELECT id, code_value FROM codes
                WHERE product_id = ? AND is_used = 0
                LIMIT 1
            """, (product_id,))
            
            row = cursor.fetchone()
            
            if row:
                code_id = row['id']
                code_value = row['code_value']
                
                cursor.execute("""
                    UPDATE codes
                    SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (user_id, code_id))
                
                conn.commit()
                return code_value
            
            conn.rollback()
            return None
        except Exception as e:
            conn.rollback()
            logger.error(f"خطأ في جلب الكود: {e}")
            return None
    
    def get_available_codes_count(self, product_id: int) -> int:
        """عدد الأكواد المتاحة"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM codes
                WHERE product_id = ? AND is_used = 0
            """, (product_id,))
            
            return cursor.fetchone()['count']
        except Exception as e:
            logger.error(f"خطأ في عد الأكواد: {e}")
            return 0
    
    # ==================== دوال الطلبات ====================
    
    def create_order(self, user_id: int, product_id: int, product_name: str,
                    payment_id: str, price: int, discount_amount: int = 0) -> Optional[int]:
        """إنشاء طلب جديد"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            final_price = price - discount_amount
            
            cursor.execute("""
                INSERT INTO orders 
                (user_id, product_id, product_name, payment_id, price, 
                 discount_amount, final_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, product_id, product_name, payment_id, 
                  price, discount_amount, final_price))
            
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"طلب مكرر: {payment_id}")
            return None
        except Exception as e:
            logger.error(f"خطأ في إنشاء الطلب: {e}")
            return None
    
    def update_order_status(self, order_id: int, status: str, 
                           delivery_status: str = None,
                           delivery_content: str = None) -> bool:
        """تحديث حالة الطلب"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            updates = ["status = ?"]
            values = [status]
            
            if delivery_status:
                updates.append("delivery_status = ?")
                values.append(delivery_status)
            
            if delivery_content:
                updates.append("delivery_content = ?")
                values.append(delivery_content)
            
            if status == 'completed':
                updates.append("completed_at = CURRENT_TIMESTAMP")
            
            values.append(order_id)
            query = f"UPDATE orders SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في تحديث الطلب: {e}")
            return False
    
    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict]:
        """الحصول على طلبات المستخدم"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM orders
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب الطلبات: {e}")
            return []
    
    def get_all_orders(self, limit: int = 50) -> List[Dict]:
        """الحصول على جميع الطلبات"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT o.*, u.username
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                ORDER BY o.created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب الطلبات: {e}")
            return []
    
    def complete_purchase(self, user_id: int, product_id: int, price: int) -> bool:
        """تحديث إحصائيات الشراء"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("BEGIN EXCLUSIVE")
            
            # تحديث بيانات المستخدم
            cursor.execute("""
                UPDATE users 
                SET total_spent = total_spent + ?, 
                    total_purchases = total_purchases + 1
                WHERE user_id = ?
            """, (price, user_id))
            
            # تحديث مبيعات المنتج
            cursor.execute("""
                UPDATE products
                SET sales_count = sales_count + 1
                WHERE id = ?
            """, (product_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"خطأ في إتمام الشراء: {e}")
            return False
    
    # ==================== دوال السجلات ====================
    
    def add_log(self, log_type: str, user_id: int, action: str, 
                details: str = None) -> bool:
        """إضافة سجل"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO logs (type, user_id, action, details)
                VALUES (?, ?, ?, ?)
            """, (log_type, user_id, action, details))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في إضافة السجل: {e}")
            return False
    
    def get_logs(self, log_type: str = None, user_id: int = None, 
                 limit: int = 100) -> List[Dict]:
        """الحصول على السجلات"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            if log_type:
                query += " AND type = ?"
                params.append(log_type)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب السجلات: {e}")
            return []
    
    # ==================== دوال الإحصائيات ====================
    
    def get_statistics(self) -> Dict:
        """الحصول على الإحصائيات العامة"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # عدد المستخدمين
            cursor.execute("SELECT COUNT(*) as count FROM users")
            stats['total_users'] = cursor.fetchone()['count']
            
            # المستخدمون النشطون (آخر 24 ساعة)
            cursor.execute("""
                SELECT COUNT(*) as count FROM users
                WHERE last_activity >= datetime('now', '-1 day')
            """)
            stats['active_users_24h'] = cursor.fetchone()['count']
            
            # إجمالي المبيعات
            cursor.execute("""
                SELECT COALESCE(SUM(final_price), 0) as total
                FROM orders WHERE status = 'completed'
            """)
            stats['total_revenue'] = cursor.fetchone()['total']
            
            # عدد الطلبات
            cursor.execute("SELECT COUNT(*) as count FROM orders")
            stats['total_orders'] = cursor.fetchone()['count']
            
            # الطلبات المكتملة
            cursor.execute("""
                SELECT COUNT(*) as count FROM orders 
                WHERE status = 'completed'
            """)
            stats['completed_orders'] = cursor.fetchone()['count']
            
            # عدد المنتجات
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE is_active = 1")
            stats['active_products'] = cursor.fetchone()['count']
            
            # أكثر المنتجات مبيعاً
            cursor.execute("""
                SELECT id, name, sales_count, price
                FROM products
                WHERE is_active = 1
                ORDER BY sales_count DESC
                LIMIT 5
            """)
            stats['top_products'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
        except Exception as e:
            logger.error(f"خطأ في جلب الإحصائيات: {e}")
            return {}
    
    # ==================== دوال الحماية من الفلود ====================
    
    def check_rate_limit(self, user_id: int, max_requests: int = 20) -> bool:
        """التحقق من معدل الطلبات"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT request_count, last_reset,
                       is_temp_banned, temp_ban_until
                FROM rate_limits
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            
            now = datetime.now()
            
            if row:
                # التحقق من الحظر المؤقت
                if row['is_temp_banned']:
                    if row['temp_ban_until']:
                        ban_until = datetime.fromisoformat(row['temp_ban_until'])
                        if now < ban_until:
                            return False
                        else:
                            # إنهاء الحظر المؤقت
                            cursor.execute("""
                                UPDATE rate_limits
                                SET is_temp_banned = 0, failed_attempts = 0
                                WHERE user_id = ?
                            """, (user_id,))
                            conn.commit()
                
                last_reset = datetime.fromisoformat(row['last_reset'])
                time_diff = (now - last_reset).total_seconds()
                
                # إعادة تعيين العداد كل دقيقة
                if time_diff >= 60:
                    cursor.execute("""
                        UPDATE rate_limits
                        SET request_count = 1, last_reset = ?
                        WHERE user_id = ?
                    """, (now, user_id))
                    conn.commit()
                    return True
                
                # التحقق من تجاوز الحد
                if row['request_count'] >= max_requests:
                    return False
                
                # زيادة العداد
                cursor.execute("""
                    UPDATE rate_limits
                    SET request_count = request_count + 1
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
                return True
            else:
                # إنشاء سجل جديد
                cursor.execute("""
                    INSERT INTO rate_limits (user_id, request_count, last_reset)
                    VALUES (?, 1, ?)
                """, (user_id, now))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"خطأ في فحص معدل الطلبات: {e}")
            return True
    
    def record_failed_attempt(self, user_id: int, max_attempts: int = 5,
                             ban_duration: int = 1800) -> bool:
        """تسجيل محاولة فاشلة"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO rate_limits (user_id, failed_attempts)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    failed_attempts = failed_attempts + 1
            """, (user_id,))
            
            cursor.execute("""
                SELECT failed_attempts FROM rate_limits
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            
            if row and row['failed_attempts'] >= max_attempts:
                ban_until = datetime.now().timestamp() + ban_duration
                cursor.execute("""
                    UPDATE rate_limits
                    SET is_temp_banned = 1,
                        temp_ban_until = ?
                    WHERE user_id = ?
                """, (datetime.fromtimestamp(ban_until), user_id))
                conn.commit()
                return True
            
            conn.commit()
            return False
        except Exception as e:
            logger.error(f"خطأ في تسجيل المحاولة الفاشلة: {e}")
            return False
    
    # ==================== دوال الإعدادات ====================
    
    def get_setting(self, key: str) -> Optional[str]:
        """الحصول على إعداد"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                return row['value']
            return None
        except Exception as e:
            logger.error(f"خطأ في جلب الإعداد: {e}")
            return None
    
    def set_setting(self, key: str, value: str) -> bool:
        """تعيين إعداد"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, value))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في تعيين الإعداد: {e}")
            return False
    
    def get_all_settings(self) -> Dict:
        """الحصول على جميع الإعدادات"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT key, value FROM settings")
            return {row['key']: row['value'] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"خطأ في جلب الإعدادات: {e}")
            return {}
    
    # ==================== دوال الفئات ====================
    
    def add_category(self, name: str, description: str = None, icon: str = '📦') -> bool:
        """إضافة فئة جديدة"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO categories (name, description, icon)
                VALUES (?, ?, ?)
            """, (name, description, icon))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في إضافة الفئة: {e}")
            return False
    
    def get_categories(self) -> List[Dict]:
        """الحصول على الفئات"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM categories WHERE is_active = 1
                ORDER BY name
            """)
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في جلب الفئات: {e}")
            return []
    
    # ==================== دوال التصدير ====================
    
    def export_data(self, table: str) -> List[Dict]:
        """تصدير بيانات جدول"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table}")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في تصدير البيانات: {e}")
            return []
    
    def close(self):
        """إغلاق الاتصال"""
        if hasattr(self.local, 'conn'):
            self.local.conn.close()
