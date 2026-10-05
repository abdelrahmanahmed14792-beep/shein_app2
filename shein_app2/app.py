import streamlit as st
import pandas as pd
import re
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام إدارة طلبات شي إن", page_icon="🛍️", layout="centered")

# 2. الربط مع Google Sheets
@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

def get_sheet():
    client = get_gspread_client()
    # فتح الملف باسمه في Google Drive
    sheet = client.open("Shein_Orders").sheet1
    return sheet

def load_orders():
    sheet = get_sheet()
    records = sheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=[
            'id', 'customer_name', 'phone', 'request_type', 
            'bag_link', 'order_number', 'total_price', 'status', 'created_at'
        ])
    df = pd.DataFrame(records)
    # تحويل العمود id لإصلاح القراءات الرقمية
    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
    return df

def extract_url(text):
    if not text:
        return ""
    url_match = re.search(r'https?://[^\s]+', str(text))
    return url_match.group(0) if url_match else str(text).strip()

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
        
        if not customer_name.strip():
            st.error("⚠️ يرجى كتابة اسم العميل.")
        elif not phone.strip():
            st.error("⚠️ يرجى كتابة رقم الواتساب للتواصل.")
        elif request_type == "-- اختر نوع الطلب --":
            st.error("⚠️ يرجى اختيار نوع الطلب (طلب اوردر أو طلب تسعير).")
        elif not clean_link:
            st.error("⚠️ يرجى إضافة رابط الشنطة بشكل صحيح.")
        else:
            sheet = get_sheet()
            orders_df = load_orders()
            
            # تحديد رقم الطلب الجديد
            new_id = int(orders_df['id'].max() + 1) if not orders_df.empty and orders_df['id'].max() > 0 else 1
            now_str = datetime.now(ZoneInfo('Africa/Cairo')).strftime("%Y-%m-%d %I:%M:%S %p")

            new_row = [
                new_id, customer_name.strip(), str(phone.strip()), 
                request_type, clean_link, "", "", "قيد الانتظار", now_str
            ]
            
            sheet.append_row(new_row)
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
            if password == "Ammar":
                st.session_state["admin_logged_in"] = True
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة")
    else:
        st.sidebar.button("تسجيل الخروج", on_click=lambda: st.session_state.update({"admin_logged_in": False}))
        
        orders_df = load_orders()

        if not orders_df.empty:
            orders_df['clean_url'] = orders_df['bag_link'].apply(extract_url)
            # ترتيب الطلبات تنازلياً من الأحدث للأقدم
            orders_df = orders_df.sort_values(by="id", ascending=False)

            st.subheader("📋 جدول الطلبات")
            
            st.dataframe(
                orders_df[['id', 'customer_name', 'phone', 'request_type', 'clean_url', 'total_price', 'order_number', 'status', 'created_at']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "رقم الطلب 🆔",
                    "customer_name": "اسم العميل",
                    "phone": "رقم الواتساب 📱",
                    "request_type": "نوع الطلب 📌",
                    "clean_url": st.column_config.LinkColumn("الرابط المباشر 🔗", display_text="فتح الرابط 🔗"),
                    "total_price": "سعر الباج 💰",
                    "order_number": "رقم الأوردر",
                    "status": "الحالة",
                    "created_at": "تاريخ الإرسال ⏰"
                }
            )

            st.divider()
            st.subheader("⚙️ إدارة وتعديل طلب محدد")

            order_list = {f"طلب رقم {row['id']} - {row['customer_name']} ({row['request_type']})": row['id'] for _, row in orders_df.iterrows()}
            selected_label = st.selectbox("اختر الطلب للتعديل أو الفتح:", list(order_list.keys()))
            selected_id = order_list[selected_label]

            current_order = orders_df[orders_df["id"] == selected_id].iloc[0]
            target_url = extract_url(current_order["bag_link"])

            # تجهيز رقم الهاتف بصيغة الواتساب الدولية
            clean_phone = re.sub(r'\D', '', str(current_order['phone']))
            if clean_phone.startswith('01'):
                clean_phone = '20' + clean_phone[1:]
            elif not clean_phone.startswith('20') and len(clean_phone) == 10:
                clean_phone = '20' + clean_phone

            col_b1, col_b2, col_b3 = st.columns(3)
            
            with col_b1:
                if target_url.startswith("http"):
                    st.link_button("🔗 اظهار اللينك", target_url, use_container_width=True)
                else:
                    st.warning("⚠️ الرابط غير صالح.")

            with col_b2:
                if clean_phone:
                    st.link_button("💬 مراسلة على واتساب", f"https://wa.me/{clean_phone}", use_container_width=True)

            with col_b3:
                if clean_phone:
                    full_name = str(current_order['customer_name']).strip()
                    first_name = full_name.split()[0] if full_name else "يا جميل"
                    price_val = current_order['total_price'] if current_order['total_price'] else "لم يحدد بعد"
                    
                    msg_text = f"ازيك يا {first_name} ، يارب تكوني بخير ❤️ ، سعر الباج اللي انتي باعتاهالي بالكامل هو {price_val} ، تحبي اعملك اوردر ؟\n\nرابط الباج المطلوب:\n{target_url}"
                    encoded_msg = urllib.parse.quote(msg_text)
                    st.link_button("📩 ارسال سعر الباج للعميل", f"https://wa.me/{clean_phone}?text={encoded_msg}", use_container_width=True)

            with st.container(border=True):
                st.markdown(f"**صاحب الطلب:** {current_order['customer_name']}")
                st.markdown(f"**رقم الواتساب:** `{current_order['phone']}`")
                st.markdown(f"**نوع الطلب:** {current_order['request_type']}")
                st.markdown(f"**توقيت الطلب:** {current_order['created_at']}")
                
                new_price = st.text_input("سعر الباج بالكامل (جنيه/دولار):", value=str(current_order["total_price"] if pd.notnull(current_order["total_price"]) else ""))
                new_order_num = st.text_input("رقم الأوردر (Order Number):", value=str(current_order["order_number"] if pd.notnull(current_order["order_number"]) else ""))
                
                status_options = ["قيد الانتظار", "تم الطلب", "تم الشحن", "تم التسليم", "ملغي"]
                current_status_idx = status_options.index(current_order["status"]) if current_order["status"] in status_options else 0
                new_status = st.selectbox("حالة الطلب:", status_options, index=current_status_idx)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("حفظ التعديلات 💾", use_container_width=True):
                        sheet = get_sheet()
                        cell = sheet.find(str(selected_id), in_column=1)
                        if cell:
                            row_idx = cell.row
                            # تعديل قيم الأعمدة (Order Number, Price, Status)
                            sheet.update_cell(row_idx, 6, new_order_num)
                            sheet.update_cell(row_idx, 7, new_price)
                            sheet.update_cell(row_idx, 8, new_status)
                            st.success("تم تحديث البيانات والسعر بنجاح!")
                            st.rerun()

                with col2:
                    if st.button("حذف الطلب 🗑️", type="secondary", use_container_width=True):
                        sheet = get_sheet()
                        cell = sheet.find(str(selected_id), in_column=1)
                        if cell:
                            sheet.delete_rows(cell.row)
                            st.warning("تم حذف الطلب بنجاح.")
                            st.rerun()
        else:
            st.info("لا توجد طلبات مسجلة حتى الآن.")
