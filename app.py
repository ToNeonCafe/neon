import sqlite3
import qrcode
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

# --- ΡΥΘΜΙΣΕΙΣ ΑΣΦΑΛΕΙΑΣ ---
USER_DATA = {
    "admin": "neon2024"
}

@auth.verify_password
def verify(username, password):
    if username in USER_DATA and USER_DATA[username] == password:
        return username

# --- ΣΥΝΔΕΣΗ ΜΕ ΤΗ ΒΑΣΗ (ΔΙΟΡΘΩΜΕΝΗ ΓΙΑ RENDER) ---
def get_db_connection():
    # Χρησιμοποιούμε τον κατάλογο /tmp γιατί εκεί επιτρέπει το Render την εγγραφή αρχείων
    conn = sqlite3.connect('/tmp/menu.db')
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

def generate_qr():
    # Εδώ είναι το Live Link σου στο Render
    url = "https://toneon-cafe.onrender.com" 
    qr = qrcode.make(url)
    # Αποθήκευση στον φάκελο static για να είναι προσβάσιμο
    if not os.path.exists('static'):
        os.makedirs('static')
    qr.save(os.path.join('static', 'menu_qr.png'))

@app.route('/')
def index():
    init_db() # Δημιουργεί τη βάση αν δεν υπάρχει
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu")
    all_items = cursor.fetchall()
    conn.close()

    custom_order = ["Καφέδες-Ροφήματα", "Αναψυκτικά", "Χυμοί", "Τσάι", "Μπύρες(Φιάλη)", "Μπύρα(Βαρέλι)", "Κρασί", "Αλκοολούχα Ποτά", "Φαγητά"]
    sorted_items = sorted(all_items, key=lambda x: custom_order.index(x[1]) if x[1] in custom_order else 999)

    return render_template('index.html', items=sorted_items)

@app.route('/admin', methods=['GET', 'POST'])
@auth.login_required
def admin():
    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        image_url = request.form['image_url']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO menu (category, name, price, description, image_url) VALUES (?, ?, ?, ?, ?)', 
                       (category, name, price, description, image_url))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('admin.html')

@app.route('/dashboard')
@auth.login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu")
    all_items = cursor.fetchall()
    conn.close()
    
    custom_order = ["Καφέδες-Ροφήματα", "Αναψυκτικά", "Χυμοί", "Τσάι", "Μπύρες(Φιάλη)", "Μπύρα(Βαρέλι)", "Κρασί", "Αλκοολούχα Ποτά", "Φαγητά"]
    sorted_items = sorted(all_items, key=lambda x: custom_order.index(x[1]) if x[1] in custom_order else 999)
    
    return render_template('dashboard.html', items=sorted_items)

@app.route('/delete/<int:item_id>')
@auth.login_required
def delete_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/update_price/<int:item_id>', methods=['POST'])
@auth.login_required
def update_price(item_id):
    new_price = request.form['price']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE menu SET price = ? WHERE id = ?", (new_price, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    generate_qr()
    app.run(debug=True)
