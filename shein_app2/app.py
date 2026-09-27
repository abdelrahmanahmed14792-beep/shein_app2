from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_shein_app'

# كلمة سر لوحة التحكم (الادمن)
ADMIN_PASSWORD = 'Ammar'

def get_db_connection():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS client_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            shein_link TEXT NOT NULL,
            created_date TEXT NOT NULL,
            status TEXT DEFAULT 'جديد',
            order_number TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

# 1. صفحة إدخال البيانات للعميل
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        client_name = request.form.get('client_name')
        shein_link = request.form.get('shein_link')

        if not client_name or not shein_link:
            flash('يرجى ملء جميع الحقول المطلوبة.', 'danger')
            return redirect(url_for('index'))

        # تاريخ اليوم تلقائياً
        today_date = datetime.now().strftime('%Y-%m-%d')

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO client_orders (client_name, shein_link, created_date, status, order_number) VALUES (?, ?, ?, ?, ?)',
            (client_name, shein_link, today_date, 'جديد', '')
        )
        conn.commit()
        conn.close()

        flash('تم إرسال طلبك بنجاح!', 'success')
        return redirect(url_for('index'))

    return render_template('index.html')

# 2. صفحة تسجيل الدخول للأدمن
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('تم تسجيل الدخول بنجاح.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('كلمة السر غير صحيحة!', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

# 3. تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('تم تسجيل الخروج.', 'info')
    return redirect(url_for('login'))

# 4. لوحة التحكم (محمية بكلمة السر Ammar)
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        flash('يرجى تسجيل الدخول أولاً للوصول إلى لوحة التحكم.', 'warning')
        return redirect(url_for('login'))

    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db_connection()
    query = 'SELECT * FROM client_orders WHERE 1=1'
    params = []

    if search_query:
        query += ' AND client_name LIKE ?'
        params.append(f'%{search_query}%')

    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)

    query += ' ORDER BY id DESC'

    orders = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('admin.html', orders=orders, search_query=search_query, status_filter=status_filter)

# 5. تحديث حالة الطلب ورقم الأوردر
@app.route('/admin/update/<int:order_id>', methods=['POST'])
def update_order(order_id):
    if not session.get('logged_in'):
        flash('غير مسموح بهذا الإجراء.', 'danger')
        return redirect(url_for('login'))

    order_number = request.form.get('order_number', '').strip()
    status = request.form.get('status', 'جديد')

    conn = get_db_connection()
    conn.execute(
        'UPDATE client_orders SET order_number = ?, status = ? WHERE id = ?',
        (order_number, status, order_id)
    )
    conn.commit()
    conn.close()

    flash('تم تحديث البيانات بنجاح.', 'success')
    return redirect(url_for('admin', search=request.args.get('search', ''), status=request.args.get('status', '')))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)