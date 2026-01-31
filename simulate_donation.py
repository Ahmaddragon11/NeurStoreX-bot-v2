from database import Database

# استخدم قاعدة بيانات in-memory للمحاكاة
db = Database(":memory:")

# إنشاء مستخدمين افتراضيين
try:
    db.add_user(111, username='owner', first_name='Owner')
    db.add_user(222, username='contrib', first_name='Contributor')
except Exception:
    pass

# إنشاء حملة تبرع مع خيارات
donation_id = db.create_donation(donor_id=111, amount=100, description='حملة اختبار', options=[5,10,20,50])
print('donation_id:', donation_id)

donation = db.get_donation(donation_id)
print('donation record:', donation)

# محاكاة مساهمة
ok = db.add_donation_contribution(donation_id, contributor_id=222, amount=20)
print('add_contribution_ok:', ok)

donation_after = db.get_donation(donation_id)
print('donation after contribution:', donation_after)

# جلب سجلات المساهمات
conn = db._get_connection()
cur = conn.cursor()
cur.execute('SELECT * FROM donation_records WHERE donation_id = ?', (donation_id,))
rows = cur.fetchall()
print('donation_records:', [dict(r) for r in rows])

# جلب نقاط المستخدم المساهم
points = db.get_user_points(222)
print('contributor points:', points)

# تحقق من أن total_received زاد
print('total_received matches sum of records:', donation_after['total_received'] == sum(r['amount'] for r in rows))
