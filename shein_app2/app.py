import streamlit as st
import sqlite3
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# 1️⃣ رقم الواتساب المخصص لاستقبال الطلبات (بدون علامة +)
YOUR_WHATSAPP_NUMBER = "201021157789"

st.set_page_config(page_title="نظام طلبات شي إن", page_icon="🛍️", layout="centered")

# 2️⃣ إنشاء وتجهيز قاعدة بيانات SQLite
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            item_link TEXT NOT NULL,
            order_date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 3️⃣ الواجهة الرئيسية للتطبيق
st.title("🛍️ نظام تسجيل طلبات شي إن")
st.write("قم بملء البيانات التالية لتأكيد طلبك والانتقال المباشر إلى الواتساب.")

# نموذج تسجيل البيانات
with st.form("order_form", clear_on_submit=False):
    name = st.text_input("الاسم بالكامل 👤")
    phone = st.text_input("رقم الهاتف / الواتساب 📞")
    item_link = st.text_input("رابط القطعة أو الباج (Item Link) 🔗")
    
    submit_button = st.form_submit_button("تسجيل الطلب والتحويل للواتساب 🚀")

# 4️⃣ معالجة البيانات وإعادة التوجيه المباشر
if submit_button:
    if name.strip() and phone.strip() and item_link.strip():
        # تسجيل التاريخ والوقت الحالي
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. حفظ البيانات في قاعدة البيانات أولاً
        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute("INSERT INTO orders (customer_name, phone, item_link, order_date) VALUES (?, ?, ?, ?)",
                  (name.strip(), phone.strip(), item_link.strip(), now_str))
        conn.commit()
        conn.close()
        
        # 2. صياغة وتشفير نص الرسالة للواتساب
        message_text = f"""📦 *طلب جديد من التطبيق*

👤 *الاسم:* {name.strip()}
📞 *الرقم:* {phone.strip()}
🔗 *رابط القطعة:* {item_link.strip()}
📅 *تاريخ وساعة الطلب:* {now_str}
"""
        encoded_message = urllib.parse.quote(message_text)
        whatsapp_url = f"https://wa.me/{YOUR_WHATSAPP_NUMBER}?text={encoded_message}"
        
        st.success("تم تسجيل الطلب في قاعدة البيانات! جاري تحويلك للواتساب... ⏳")
        
        # 3. إعادة التوجيه التلقائي والمباشر للواتساب باستخدام JavaScript
        js_redirect = f"""
            <script>
                window.open("{whatsapp_url}", "_blank");
            </script>
        """
        components.html(js_redirect, height=0)

    else:
        st.error("⚠️ يرجى التأكد من ملء جميع الحقول المطلوبة (الاسم، الرقم، ورابط القطعة).")
