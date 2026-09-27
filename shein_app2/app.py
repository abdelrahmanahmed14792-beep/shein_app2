import streamlit as st
import sqlite3
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام جمع أوردرات شي إن", page_icon="🛍️", layout="centered")

# 2. إنشاء وتوصيل قاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('orders.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            bag_link TEXT NOT NULL,
            order_number TEXT DEFAULT '',
            status TEXT DEFAULT 'قيد الانتظار',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

init_db()

# 3. الشريط الجانبي للتنقل
st.sidebar.title("📌 القائمة")
page = st.sidebar.radio("اختر الصفحة:", ["تقديم طلب جديد", "لوحة التحكم (الأدمن)"])

# ---------------------------------------------------------
# الصفحة الأولى: تقديم طلب جديد (للعملاء)
# ---------------------------------------------------------
if page == "تقديم طلب جديد":
    st.title("🛍️ نموذج تسجيل طلبات شي إن")
    st.write("برجاء إدخال اسمك ورابط حقيبة التسوق الخاصة بك")

    with st.form(key="order_form", clear_on_submit=True):
        customer_name = st.text_input("اسم العميل / اسم الحساب:")
        bag_link = st.text_input("رابط شنطة شي إن (Bag Link):")
        submit_button = st.form_submit_button(label="إرسال الطلب 🚀")

    if submit_button:
        if customer_name.strip() and bag_link.strip():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO orders (customer_name, bag_link) VALUES (?, ?)',
                (customer_name, bag_link)
            )
            conn.commit()
            st.success("✅ تم تسجيل طلبك بنجاح! شكراً لك.")
        else:
            st.error("⚠️ يرجى ملء كافة البيانات المطلوبة.")

# ---------------------------------------------------------
# الصفحة الثانية: لوحة التحكم (للأدمن)
# ---------------------------------------------------------
elif page == "لوحة التحكم (الأدمن)":
    st.title("🔐 لوحة تحكم الأدمن")

    # التحقق من كلمة المرور
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        password = st.text_input("أدخل كلمة المرور:", type="password")
        if st.button("تسجيل الدخول"):
            if password == "Ammar":
                st.session_state["admin_logged_in"] = True
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة")
    else:
        st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"admin_logged_in": False}))
        st.subheader("📋 قائمة الطلبات المسجلة")

        conn = get_db_connection()
        orders_df = pd.read_sql_query("SELECT id, customer_name, bag_link, order_number, status, created_at FROM orders ORDER BY id DESC", conn)

        if not orders_df.empty:
            # عرض جدول الطلبات مع إمكانية الضغط على الرابط فتح الصفحة مباشرة
            st.dataframe(
                orders_df,
                use_container_width=True,
                column_config={
                    "id": "رقم الطلب",
                    "customer_name": "اسم العميل",
                    "bag_link": st.column_config.LinkColumn(
                        "رابط الشنطة 🔗", 
                        display_text="فتح الرابط 🔗"  # النص الذي يظهر بدلاً من الرابط الطويل
                    ),
                    "order_number": "رقم الأوردر",
                    "status": "الحالة",
                    "created_at": "تاريخ الطلب"
                }
            )

            st.divider()
            st.subheader("⚙️ تعديل أو معاينة طلب")

            selected_id = st.selectbox("اختر رقم الطلب (ID):", orders_df["id"].tolist())
            
            # جلب بيانات الطلب المختار
            current_order = orders_df[orders_df["id"] == selected_id].iloc[0]

            # إظهار زر مباشر لفتح الرابط بشكل واضح
            st.markdown(f"🔗 **رابط الشنطة المباشر:** [{current_order['bag_link']}]({current_order['bag_link']})")

            new_order_num = st.text_input("رقم الأوردر:", value=current_order["order_number"])
            status_options = ["قيد الانتظار", "تم الطلب", "تم الشحن", "تم التسليم", "ملغي"]
            new_status = st.selectbox("حالة الطلب:", status_options, index=status_options.index(current_order["status"]) if current_order["status"] in status_options else 0)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("تحديث البيانات 💾"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE orders SET order_number = ?, status = ? WHERE id = ?", (new_order_num, new_status, selected_id))
                    conn.commit()
                    st.success("تم تحديث البيانات بنجاح!")
                    st.rerun()

            with col2:
                if st.button("حذف الطلب 🗑️"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM orders WHERE id = ?", (selected_id,))
                    conn.commit()
                    st.warning("تم حذف الطلب!")
                    st.rerun()
        else:
            st.info("لا توجد طلبات مسجلة حالياً.")
