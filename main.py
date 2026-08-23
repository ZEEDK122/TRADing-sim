from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import yfinance as yf

app = Flask(__name__)
app.secret_key = 'سر_قوي_غيره_هنا'
app.config['SESSION_COOKIE_SECURE'] = False
DB = 'trading_sim.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, balance REAL, password TEXT, is_admin INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symbol TEXT, direction TEXT, lot REAL, entry_price REAL, status TEXT, profit REAL DEFAULT 0)''')
    c.execute("SELECT * FROM users WHERE email='admin@demo.com'")
    if not c.fetchone():
        hashed = generate_password_hash("admin123")
        c.execute("INSERT INTO users (name, email, balance, password, is_admin) VALUES (?,?,?,?,?)", ('المدير', 'admin@demo.com', 100000, hashed, 1))
    conn.commit(); conn.close()
init_db()

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name,email,password = request.form['name'],request.form['email'],request.form['password']
        hashed = generate_password_hash(password)
        try:
            conn = sqlite3.connect(DB); c = conn.cursor()
            c.execute("INSERT INTO users (name, email, balance, password, is_admin) VALUES (?,?,?,?,?)", (name, email,50,100,150,200,300,500,1000, 10000,hashed, 0))
            conn.commit(); conn.close()
            return "تم التسجيل! <a href='/'>دخول</a>"
        except: return "الايميل مستخدم"
    return '<h2>تسجيل</h2><form method=POST>الاسم:<input name=name required><br>ايميل:<input name=email required><br>باسوورد:<input name=password type=password required><br><button>تسجيل</button></form>'

@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email,password = request.form['email'],request.form['password']
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,)); user = c.fetchone(); conn.close()
        if user and check_password_hash(user[4], password):
            session['user_id'] = user[0]; session['is_admin'] = user[5]; return redirect('/dashboard')
        return "خطأ"
    return '<h2>دخول</h2><form method=POST>ايميل:<input name=email><br>باسوورد:<input name=password type=password><br><button>دخول</button></form><a href=/register>تسجيل</a>'

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/')
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)); user = c.fetchone(); conn.close()
    return f"<h2>مرحبا {user[1]}</h2><p>الرصيد: {user[3]}$ وهمي</p><a href=/deposit>ايداع</a> | <a href=/withdraw>سحب</a> | <a href=/chart>شارت</a> | <a href=/bot>كود</a>"

@app.route('/deposit', methods=['GET','POST'])
def deposit():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE users SET balance = balance +? WHERE id=?", (amount, session['user_id']))
        conn.commit(); conn.close(); return redirect('/dashboard')
    return '<form method=POST>المبلغ:<input name=amount><button>ايداع وهمي</button></form>'

@app.route('/withdraw', methods=['GET','POST'])
def withdraw():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("UPDATE users SET balance = balance -? WHERE id=?", (amount, session['user_id']))
        conn.commit(); conn.close(); return redirect('/dashboard')
    return '<form method=POST>المبلغ:<input name=amount><button>سحب وهمي</button></form>'

@app.route('/chart')
def chart():
    return '''<h2>شارت TradingView</h2><script src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({"symbol": "FX:EURUSD", "width": "100%", "height": 500})</script>'''

@app.route('/bot', methods=['GET','POST'])
def bot():
    if request.method == 'POST':
        symbol,direction,lot = request.form['symbol'],request.form['direction'],float(request.form['lot'])
        price = yf.Ticker(symbol).history(period="1d")['Close'].iloc[-1]
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute("INSERT INTO trades (user_id, symbol, direction, lot, entry_price, status) VALUES (?,?,?,?,?,'مفتوحة')",(session['user_id'], symbol, direction, lot, price))
        conn.commit(); conn.close()
        return f"تم! صفقة {direction} {symbol} <a href=/dashboard>رجوع</a>"
    return '<h2>تشغيل كود الصفقة</h2><form method=POST>الرمز:<input name=symbol value=EURUSD=X><br>الاتجاه:<select name=direction><option>شراء</option><option>بيع</option></select><br>اللوت:<input name=lot value=0.1><br><button>تنفيذ</button></form>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
