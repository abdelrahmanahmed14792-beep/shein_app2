import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
from zoneinfo import ZoneInfo

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام إدارة طلبات شي إن", page_icon="🛍️", layout="centered")

# دالة لاستخراج رابط الـ URL النقي من النص المشارك من تطبيق شي إن
def extract_url(text):
    if not text:
        return ""
    url_match = re.search(r'https?://[^\s]+', str(text))
    return url_match.group(0) if url_match else str(text).strip()

# 2. إنشاء وتوصيل قاعدة البيانات
def get_db_connection():
    return sqlite3.connect('orders.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # إنشاء الجدول إضافة الأعمدة الجديدة (phone, request_type)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            request_type TEXT DEFAULT '',
            bag_link TEXT NOT NULL,
            order_number TEXT DEFAULT '',
            status TEXT DEFAULT 'قيد الانتظار',
            created_at TEXT
        )
    ''')
    conn.commit()

init_db()

# 3. الشريط الجانبي
st.sidebar.title("📌 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["تقديم طلب جديد", "لوحة التحكم (الأدمن)"])

# ---------------------------------------------------------
# الصفحة الأولى: تقديم طلب جديد (للعملاء)
# ---------------------------------------------------------
if page == "تقديم طلب جديد":
    st.title("🛍️ تسجيل طلب جديد")
    st.write("برجاء تعبئة جميع الخانات التالية لإرسال طلبك:")

    with st.form(key="order_form", clear_on_submit=True):
        customer_name = st.text_input("اسم العميل / اسم الحساب *:")
        phone = st.text_input("رقم الموبايل (المسجل عليه واتساب) *:")
        
        request_type = st.selectbox(
            "نوع الطلب *:", 
            ["-- اختر نوع الطلب --", "طلب اوردر", "طلب تسعير"]
        )
        
        bag_link = st.text_area("رابط أو نص مشاركة حقيبة شي إن *:")
        
        submit_button = st.form_submit_button(label="إرسال الطلب 🚀")

    if submit_button:
        clean_link = extract_url(bag_link)
        
        # التأكد من ملء جميع الخانات بشكل إجباري
        if not customer_name.strip():
            st.error("⚠️ يرجى كتابة اسم العميل.")
        elif not phone.strip():
            st.error("⚠️ يرجى كتابة رقم الواتساب للتواصل.")
        elif request_type == "-- اختر نوع الطلب --":
            st.error("⚠️ يرجى اختيار نوع الطلب (طلب اوردر أو طلب تسعير).")
        elif not clean_link:
            st.error("⚠️ يرجى إضافة رابط الشنطة بشكل صحيح.")
        else:
            # في حال اكتمال كافة البيانات
            now_str = datetime.now(ZoneInfo('Africa/Cairo')).strftime("%Y-%m-%d %I:%M:%S %p")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO orders (customer_name, phone, request_type, bag_link, created_at) 
                   VALUES (?, ?, ?, ?, ?)''',
                (customer_name.strip(), phone.strip(), request_type, clean_link, now_str)
            )
            conn.commit()
            st.success("✅ تم تسجيل طلبك بنجاح! سنقوم بالتواصل معك عبر الواتساب قريباً.")

# ---------------------------------------------------------
# الصفحة الثانية: لوحة التحكم (للأدمن)
# ---------------------------------------------------------
elif page == "لوحة التحكم (الأدمن)":
    st.title("🔐 لوحة التحكم وإدارة الطلبات")

    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        password = st.text_input("أدخل كلمة المرور:", type="password")
        if st.button("تسجيل الدخول"):
            if password == "Ammar":  # يمكنك تغيير كلمة المرور من هنا
                st.session_state["admin_logged_in"] = True
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة")
    else:
        st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"admin_logged_in": False}))
        
        conn = get_db_connection()
        orders_df = pd.read_sql_query(
            "SELECT id, customer_name, phone, request_type, bag_link, order_number, status, created_at FROM orders ORDER BY id DESC", 
            conn
        )

        if not orders_df.empty:
            orders_df['clean_url'] = orders_df['bag_link'].apply(extract_url)

            st.subheader("📋 جدول الطلبات")
            
            st.dataframe(
                orders_df[['id', 'customer_name', 'phone', 'request_type', 'clean_url', 'order_number', 'status', 'created_at']],
                use_container_width=True,
                column_config={
                    "id": "رقم الطلب",
                    "customer_name": "اسم العميل",
                    "phone": "رقم الواتساب 📱",
                    "request_type": "نوع الطلب 📌",
                    "clean_url": st.column_config.LinkColumn(
                        "الرابط المباشر 🔗", 
                        display_text="فتح الرابط 🔗"
                    ),
                    "order_number": "رقم الأوردر",
                    "status": "الحالة",
                    "created_at": "تاريخ ووقت الإرسال ⏰"
                }
            )

            st.divider()
            st.subheader("⚙️ إدارة وتعديل طلب محدد")

            order_list = {f"طلب رقم {row['id']} - {row['customer_name']} ({row['request_type']})": row['id'] for _, row in orders_df.iterrows()}
            selected_label = st.selectbox("اختر الطلب للتعديل أو الفتح:", list(order_list.keys()))
            selected_id = order_list[selected_label]

            current_order = orders_df[orders_df["id"] == selected_id].iloc[0]
            target_url = extract_url(current_order["bag_link"])

            # إظهار زر رابط الشنطة + رابط سريع لفتح محادثة الواتساب مع العميل
            col_link1, col_link2 = st.columns(2)
            with col_link1:
                if target_url.startswith("http"):
                    st.link_button("🔗 فتح رابط الشنطة", target_url, use_container_width=True)
                else:
                    st.warning("⚠️ الرابط غير صالح.")
            
            with col_link2:
                clean_phone = re.sub(r'\D', '', str(current_order['phone']))
                if clean_phone:
                    st.link_button("💬 مراسلة العميل على الواتساب", f"https://wa.me/{clean_phone}", use_container_width=True)

            with st.container(border=True):
                st.markdown(f"**صاحب الطلب:** {current_order['customer_name']}")
                st.markdown(f"**رقم الواتساب:** `{current_order['phone']}`")
                st.markdown(f"**نوع الطلب:** {current_order['request_type']}")
                st.markdown(f"**توقيت الطلب:** {current_order['created_at']}")
                
                new_order_num = st.text_input("رقم الأوردر (Order Number):", value=current_order["order_number"])
                
                status_options = ["قيد الانتظار", "تم الطلب", "تم الشحن", "تم التسليم", "ملغي"]
                current_status_idx = status_options.index(current_order["status"]) if current_order["status"] in status_options else 0
                new_status = st.selectbox("حالة الطلب:", status_options, index=current_status_idx)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("حفظ التعديلات 💾", use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE orders SET order_number = ?, status = ? WHERE id = ?", (new_order_num, new_status, selected_id))
                        conn.commit()
                        st.success("تم تحديث الطلب بنجاح!")
                        st.rerun()

                with col2:
                    if st.button("حذف الطلب 🗑️", type="secondary", use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM orders WHERE id = ?", (selected_id,))
                        conn.commit()
                        st.warning("تم حذف الطلب بنجاح.")
                        st.rerun()
        else:
            st.info("لا توجد طلبات مسجلة حتى الآن.")
