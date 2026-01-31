# -*- coding: utf-8 -*-
"""
Keyboards Module
وحدة لوحات المفاتيح
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict
from config import EMOJI, PRODUCTS_PER_PAGE


class Keyboards:
    """فئة لإنشاء لوحات المفاتيح"""
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """القائمة الرئيسية"""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{EMOJI['store']} المنتجات",
                    callback_data="browse_products"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['purchases']} مشترياتي",
                    callback_data="my_purchases"
                ),
                InlineKeyboardButton(
                    f"{EMOJI['orders']} طلباتي",
                    callback_data="my_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['account']} حسابي",
                    callback_data="my_account"
                ),
                InlineKeyboardButton(
                    f"{EMOJI['help']} المساعدة",
                    callback_data="help"
                )
            ]
        ]
        
        if is_admin:
            keyboard.append([
                InlineKeyboardButton(
                    f"{EMOJI['settings']} لوحة التحكم",
                    callback_data="admin_panel"
                )
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        """لوحة تحكم المسؤول"""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{EMOJI['products']} إدارة المنتجات",
                    callback_data="admin_products"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['stats']} الإحصائيات",
                    callback_data="admin_stats"
                ),
                InlineKeyboardButton(
                    f"{EMOJI['users']} المستخدمون",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['orders']} الطلبات",
                    callback_data="admin_orders"
                ),
                InlineKeyboardButton(
                    f"{EMOJI['security']} السجلات",
                    callback_data="admin_logs"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['settings']} الإعدادات",
                    callback_data="admin_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} العودة للقائمة",
                    callback_data="start"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_products() -> InlineKeyboardMarkup:
        """قائمة إدارة المنتجات"""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{EMOJI['add']} إضافة منتج",
                    callback_data="add_product_start"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['edit']} تعديل منتج",
                    callback_data="edit_product_list"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['delete']} حذف منتج",
                    callback_data="delete_product_list"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['search']} عرض جميع المنتجات",
                    callback_data="view_all_products"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data="admin_panel"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def product_types() -> InlineKeyboardMarkup:
        """أنواع المنتجات"""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{EMOJI['file']} ملف",
                    callback_data="product_type:file"
                ),
                InlineKeyboardButton(
                    f"{EMOJI['image']} صورة",
                    callback_data="product_type:image"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['text']} نص",
                    callback_data="product_type:text"
                ),
                InlineKeyboardButton(
                    f"{EMOJI['code']} كود",
                    callback_data="product_type:code"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['balance']} رصيد",
                    callback_data="product_type:balance"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['cancel']} إلغاء",
                    callback_data="admin_products"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def stock_type() -> InlineKeyboardMarkup:
        """نوع المخزون"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "♾️ غير محدود",
                    callback_data="stock_type:unlimited"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔢 محدود",
                    callback_data="stock_type:limited"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['cancel']} إلغاء",
                    callback_data="admin_products"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_action(callback_yes: str, callback_no: str) -> InlineKeyboardMarkup:
        """تأكيد إجراء"""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{EMOJI['confirm']} نعم",
                    callback_data=callback_yes
                ),
                InlineKeyboardButton(
                    f"{EMOJI['cancel']} لا",
                    callback_data=callback_no
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def products_list(products: List[Dict], page: int = 0, 
                     callback_prefix: str = "product") -> InlineKeyboardMarkup:
        """قائمة المنتجات مع pagination"""
        keyboard = []
        
        start = page * PRODUCTS_PER_PAGE
        end = start + PRODUCTS_PER_PAGE
        page_products = products[start:end]
        
        # عرض المنتجات
        for product in page_products:
            # أيقونة حسب نوع المنتج
            icon = EMOJI.get(product['type'], EMOJI['products'])
            
            # حالة المخزون
            if product['is_limited']:
                stock_info = f" [{product['stock']}]"
            else:
                stock_info = " [♾️]"
            
            button_text = f"{icon} {product['name']} - {product['price']}⭐{stock_info}"
            
            keyboard.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"{callback_prefix}:{product['id']}"
                )
            ])
        
        # أزرار التنقل
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    "◀️ السابق",
                    callback_data=f"page:{callback_prefix}:{page-1}"
                )
            )
        
        if end < len(products):
            nav_buttons.append(
                InlineKeyboardButton(
                    "▶️ التالي",
                    callback_data=f"page:{callback_prefix}:{page+1}"
                )
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # زر الرجوع
        keyboard.append([
            InlineKeyboardButton(
                f"{EMOJI['back']} رجوع",
                callback_data="start"
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def product_detail(product_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
        """تفاصيل المنتج"""
        keyboard = []
        
        if not is_admin:
            # زر الشراء للمستخدمين
            keyboard.append([
                InlineKeyboardButton(
                    f"{EMOJI['star']} شراء الآن",
                    callback_data=f"buy:{product_id}"
                )
            ])
        else:
            # أزرار الإدارة
            keyboard.extend([
                [
                    InlineKeyboardButton(
                        f"{EMOJI['edit']} تعديل",
                        callback_data=f"edit_product:{product_id}"
                    ),
                    InlineKeyboardButton(
                        f"{EMOJI['delete']} حذف",
                        callback_data=f"delete_product:{product_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "👁️ إخفاء/إظهار",
                        callback_data=f"toggle_product:{product_id}"
                    )
                ]
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"{EMOJI['back']} رجوع",
                callback_data="browse_products"
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_settings() -> InlineKeyboardMarkup:
        """إعدادات المسؤول"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔧 وضع الصيانة",
                    callback_data="toggle_maintenance"
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 إرسال رسالة جماعية",
                    callback_data="broadcast_message"
                )
            ],
            [
                InlineKeyboardButton(
                    "💾 نسخ احتياطي",
                    callback_data="backup_database"
                ),
                InlineKeyboardButton(
                    "📊 تصدير البيانات",
                    callback_data="export_data"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 إدارة الخصومات",
                    callback_data="manage_discounts"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔗 نظام الإحالة",
                    callback_data="referral_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data="admin_panel"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_users_actions(user_id: int) -> InlineKeyboardMarkup:
        """إجراءات على المستخدم"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🚫 حظر",
                    callback_data=f"ban_user:{user_id}"
                ),
                InlineKeyboardButton(
                    "✅ إلغاء الحظر",
                    callback_data=f"unban_user:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "💰 إضافة رصيد",
                    callback_data=f"add_balance:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 عرض السجل",
                    callback_data=f"user_logs:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data="admin_users"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def export_options() -> InlineKeyboardMarkup:
        """خيارات التصدير"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 المستخدمين",
                    callback_data="export:users"
                )
            ],
            [
                InlineKeyboardButton(
                    "📦 المنتجات",
                    callback_data="export:products"
                )
            ],
            [
                InlineKeyboardButton(
                    "🧾 الطلبات",
                    callback_data="export:orders"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 الإحصائيات",
                    callback_data="export:stats"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data="admin_settings"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button(callback_data: str = "start") -> InlineKeyboardMarkup:
        """زر رجوع بسيط"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data=callback_data
                )
            ]
        ])
    
    @staticmethod
    def edit_product_menu(product_id: int) -> InlineKeyboardMarkup:
        """قائمة تعديل المنتج"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✏️ الاسم",
                    callback_data=f"edit_product_name:{product_id}"
                ),
                InlineKeyboardButton(
                    "📝 الوصف",
                    callback_data=f"edit_product_desc:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⭐ السعر",
                    callback_data=f"edit_product_price:{product_id}"
                ),
                InlineKeyboardButton(
                    "📦 المخزون",
                    callback_data=f"edit_product_stock:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 الخصم",
                    callback_data=f"edit_product_discount:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📄 المحتوى",
                    callback_data=f"edit_product_content:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data=f"product:{product_id}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def categories_list(categories: List[Dict]) -> InlineKeyboardMarkup:
        """قائمة الفئات"""
        keyboard = []
        
        for category in categories:
            keyboard.append([
                InlineKeyboardButton(
                    f"{category.get('icon', '📦')} {category['name']}",
                    callback_data=f"category:{category['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                "📦 جميع المنتجات",
                callback_data="category:all"
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"{EMOJI['back']} رجوع",
                callback_data="start"
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def my_account_menu() -> InlineKeyboardMarkup:
        """قائمة حسابي"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 رصيدي",
                    callback_data="my_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    "⭐ مشترياتي",
                    callback_data="my_purchases"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔗 رابط الإحالة",
                    callback_data="my_referral"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 إحصائياتي",
                    callback_data="my_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data="start"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def order_detail(order_id: int, show_receipt: bool = True) -> InlineKeyboardMarkup:
        """تفاصيل الطلب"""
        keyboard = []
        
        if show_receipt:
            keyboard.append([
                InlineKeyboardButton(
                    "🧾 عرض الإيصال",
                    callback_data=f"receipt:{order_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"{EMOJI['back']} رجوع",
                callback_data="my_orders"
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
