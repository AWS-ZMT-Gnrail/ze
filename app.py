from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
import random
import string
import os
import re

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # المفتاح السري للجلسات
app.config['UPLOAD_FOLDER'] = 'uploads'  # مجلد رفع الملفات

# إنشاء قاعدة البيانات والجداول
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # جدول الأكواد
    cursor.execute('''CREATE TABLE IF NOT EXISTS codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        expiry_date TEXT,
        user_name TEXT,
        active BOOLEAN
    )''')
    # جدول الفيديوهات
    cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_url TEXT
    )''')
    # جدول البث عبر Google Meet
    cursor.execute('''CREATE TABLE IF NOT EXISTS meet_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link TEXT
    )''')
    # جدول رفع ملفات PDF
    cursor.execute('''CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        file_path TEXT
    )''')
    conn.commit()
    conn.close()

# استدعاء إنشاء قاعدة البيانات
init_db()

# دالة لتحويل رابط يوتيوب العادي إلى رابط التضمين
def convert_to_embed_url(youtube_url):
    youtube_regex = r'(https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+))'
    match = re.match(youtube_regex, youtube_url)
    
    if match:
        video_id = match.group(2)
        embed_url = f'https://www.youtube.com/embed/{video_id}'
        return embed_url
    else:
        return None

# صفحة تسجيل الدخول
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        code = request.form['code']

        # التحقق من كود الأدمن
        if code == '15241524':  # كود الأدمن
            session['admin'] = True  # إنشاء جلسة للأدمن
            return redirect(url_for('admin'))  # توجيه للأدمن

        # التحقق من كود المستخدم
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date, user_name, active FROM codes WHERE code = ?", (code,))
        result = cursor.fetchone()
        conn.close()

        if result:
            expiry_date = datetime.strptime(result[0], "%Y-%m-%d")
            if expiry_date >= datetime.now() and result[2]:  # التحقق من كون الكود فعالًا
                session['user'] = code
                return redirect(url_for('user_page'))  # توجيه إلى صفحة المستخدم
            else:
                flash('انتهت صلاحية الكود أو الكود غير مفعل، الرجاء التواصل مع الإدارة.', 'danger')
        else:
            flash('الكود غير صحيح أو لا يوجد في قاعدة البيانات.', 'danger')
    return render_template('login.html')

# صفحة المستخدم
@app.route('/user')
def user_page():
    if 'user' not in session:
        return redirect(url_for('login'))

    # استرجاع الفيديوهات وملفات PDF وروابط Google Meet من قاعدة البيانات
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT video_url FROM videos")
    videos = cursor.fetchall()
    
    cursor.execute("SELECT file_name, file_path FROM pdfs")
    pdf_files = cursor.fetchall()

    cursor.execute("SELECT link FROM meet_links")
    meet_links = cursor.fetchall()
    
    conn.close()
    
    return render_template('user.html', videos=videos, pdf_files=pdf_files, meet_links=meet_links)

# صفحة الإدارة
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        return redirect(url_for('login'))

    generated_code = None  # متغير لتخزين الكود العشوائي

    if request.method == 'POST':
        # رفع الفيديو
        if 'video_url' in request.form:
            video_url = request.form['video_url']
            embed_url = convert_to_embed_url(video_url)
            if embed_url:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO videos (video_url) VALUES (?)", (embed_url,))
                conn.commit()
                conn.close()
                flash('تمت إضافة الفيديو بنجاح.', 'success')
            else:
                flash("يرجى إدخال رابط الفيديو الصحيح من YouTube.", "danger")
        
        # إنشاء كود جديد
        elif 'generate_code' in request.form:
            random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            expiry_date = datetime.now() + timedelta(days=30)  # مدة الكود 30 يومًا
            user_name = request.form['user_name']  # اسم صاحب الكود
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO codes (code, expiry_date, user_name, active) VALUES (?, ?, ?, ?)",
                           (random_code, expiry_date.strftime("%Y-%m-%d"), user_name, True))
            conn.commit()
            conn.close()
            generated_code = random_code  # حفظ الكود في المتغير
            flash(f'تم إنشاء الكود بنجاح.', 'success')

        # رفع ملف PDF
        elif 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                filename = pdf_file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf_file.save(file_path)
                
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO pdfs (file_name, file_path) VALUES (?, ?)", (filename, file_path))
                conn.commit()
                conn.close()
                flash('تم رفع ملف PDF بنجاح.', 'success')
        
        # إضافة رابط بث Google Meet
        elif 'meet_link' in request.form:
            meet_link = request.form['meet_link']
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO meet_links (link) VALUES (?)", (meet_link,))
            conn.commit()
            conn.close()
            flash('تم إضافة رابط Google Meet بنجاح.', 'success')

        # تعطيل أو تفعيل كود
        elif 'toggle_code' in request.form:
            code_id = request.form['toggle_code']
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT active FROM codes WHERE id = ?", (code_id,))
            result = cursor.fetchone()
            if result:
                new_status = not result[0]  # التبديل بين التفعيل والتعطيل
                cursor.execute("UPDATE codes SET active = ? WHERE id = ?", (new_status, code_id))
                conn.commit()
            conn.close()
            flash('تم تحديث حالة الكود بنجاح.', 'success')
    
    # استرجاع الأكواد
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, user_name, expiry_date, active FROM codes")
    codes = cursor.fetchall()
    conn.close()

    return render_template('admin.html', generated_code=generated_code, codes=codes)

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
