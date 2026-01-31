# -*- coding: utf-8 -*-
"""
Keyboards Module
وحدة لوحات المفاتيح
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict
from config import EMOJI, PRODUCTS_PER_PAGE, PRODUCT_TYPES


class Keyboards:
    """فئة لإنشاء لوحات المفاتيح"""
    
    @staticmethod
    def donation_stars_amounts() -> InlineKeyboardMarkup:
        """أزرار اختيار مبلغ التبرع"""
        keyboard = [
            [
                InlineKeyboardButton("1⭐", callback_data="donate_stars:1"),
                InlineKeyboardButton("5⭐", callback_data="donate_stars:5"),
                InlineKeyboardButton("10⭐", callback_data="donate_stars:10"),
                InlineKeyboardButton("25⭐", callback_data="donate_stars:25")
            ],
            [
                InlineKeyboardButton("50⭐", callback_data="donate_stars:50"),
                InlineKeyboardButton("100⭐", callback_data="donate_stars:100"),
                InlineKeyboardButton("250⭐", callback_data="donate_stars:250"),
                InlineKeyboardButton("500⭐", callback_data="donate_stars:500")
            ],
            [
                InlineKeyboardButton("💬 مبلغ مخصص", callback_data="donate_custom"),
                InlineKeyboardButton("📊 إحصائيات", callback_data="donation_stats")
            ],
            [
                InlineKeyboardButton("⬅️ رجوع", callback_data="start")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
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
            ],
            [
                InlineKeyboardButton(
                    "🎁 تبرع للبوت",
                    callback_data="donate_to_bot"
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
                    "🔁 تعيين خصم للجميع",
                    callback_data="bulk_discount"
                )
            ],
            [
                InlineKeyboardButton(
                    "📥 استيراد CSV",
                    callback_data="import_products_csv"
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
                ],
                [
                    InlineKeyboardButton(
                        "🎯 خصم 10%",
                        callback_data=f"quick_discount:{product_id}:10"
                    ),
                        InlineKeyboardButton(
                            "🧾 إزالة الخصم",
                            callback_data=f"quick_discount:{product_id}:0"
                        )
                ],
                    [
                        InlineKeyboardButton(
                            "🎯 خصم 5%",
                            callback_data=f"quick_discount:{product_id}:5"
                        ),
                        InlineKeyboardButton(
                            "🎯 خصم 20%",
                            callback_data=f"quick_discount:{product_id}:20"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔧 خصم مخصص",
                            callback_data=f"set_custom_discount:{product_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🎯 خصم 50%",
                            callback_data=f"quick_discount:{product_id}:50"
                        )
                    ],
                [
                    InlineKeyboardButton(
                        "🏷️ تغيير الفئة",
                        callback_data=f"change_category:{product_id}"
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
    def category_select(product_id: int) -> InlineKeyboardMarkup:
        """لوحة لاختيار الفئة من القيم المعرفة"""
        keyboard = []
        # PRODUCT_TYPES keys may be many; arrange two per row
        items = list(PRODUCT_TYPES.items())
        row = []
        for key, label in items:
            row.append(InlineKeyboardButton(f"{label}", callback_data=f"set_category:{product_id}:{key}"))
            if len(row) >= 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        # خيار فئة مخصصة
        keyboard.append([
            InlineKeyboardButton("📌 فئة مخصصة", callback_data=f"set_category_custom:{product_id}"),
            InlineKeyboardButton(f"{EMOJI['back']} رجوع", callback_data=f"product:{product_id}")
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
    
    @staticmethod
    def donation_menu() -> InlineKeyboardMarkup:
        """قائمة التبرع"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎁 حملة جديدة",
                    callback_data="create_donation"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 حملاتي",
                    callback_data="my_donations"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏆 أفضل الحملات",
                    callback_data="top_campaigns"
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
    def points_menu() -> InlineKeyboardMarkup:
        """قائمة النقاط"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ استبدال النقاط",
                    callback_data="exchange_points"
                )
            ],
            [
                InlineKeyboardButton(
                    "📜 السجل",
                    callback_data="points_history"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{EMOJI['back']} رجوع",
                    callback_data="my_account"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
