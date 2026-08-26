from flask import Flask, request, redirect, session, send_file
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "tudiheal2026machakos_secure_key_change_this"

STYLE = """
<style>
body{font-family:Arial; background:#f4f6f9; margin:0;}
.btn{padding:6px 12px; background:#007bff; color:white; text-decoration:none; border-radius:4px; display:inline-block; margin:2px;}
.btn-green{background:#28a745;}.btn-red{background:#dc3545;}
table{width:100%; background:white; border-collapse:collapse;}
th,td{padding:8px; border:1px solid #ddd; text-align:left;}
input,select{padding:8px; margin:5px; width:90%;}
.card{background:white; padding:15px; margin:10px; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1);}
</style>
"""

def init_db():
    conn=sqlite3.connect('clinic.db')
    c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, age TEXT, gender TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, title TEXT, amount REAL, date TEXT, created_by TEXT)")
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password,role,created_at) VALUES (?,?,?,?)", ('admin','admin','admin', datetime.now().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()

init_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user' not in session: return redirect('/login')
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('role')!='admin': return "<h3>Admin Only! <a href='/'>Home</a></h3>"
        return f(*args, **kwargs)
    return wrap

@app.route('/')
@login_required
def home():
    return f'<html><head>{STYLE}</head><body style="padding:20px;"><h1>Tudiheal V3.1 - Machakos Clinic</h1><p>User: {session.get("user")} | Role: {session.get("role")}</p><div class="card"><a class="btn" href="/patients">Patients</a> <a class="btn" href="/expenses">Expenses</a> <a class="btn btn-green" href="/users">Users Admin Only - Edit/Delete Password</a> <a class="btn btn-red" href="/logout">Logout</a></div><div class="card"><h3>Security Status: {"SECURE - Custom Password" if session.get("user")!="admin" else "NOT SECURE - Still using admin/admin - CHANGE NOW!"}</h3><p>Backup DB: <a href="/backup">Download clinic.db</a></p></div></body></html>'

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form.get('username'); p=request.form.get('password')
        conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)); row=c.fetchone(); conn.close()
        if row:
            session['user']=row[1]; session['role']=row[3]; return redirect('/')
        else: return "<h3>Wrong password! <a href='/login'>Try again</a></h3>"
    return f'<html><head>{STYLE}</head><body style="padding:20px;"><h2>Tudiheal Login V3.1</h2><form method="POST"><input name="username" placeholder="Username e.g. denis" required><br><input type="password" name="password" placeholder="Password e.g. Tudiheal0796@2026!" required><br><button class="btn btn-green">Login</button></form><p>Default: admin / admin - CHANGE AFTER LOGIN!</p></body></html>'

@app.route('/logout')
def logout():
    session.clear(); return redirect('/login')

@app.route('/users')
@login_required
@admin_required
def users_list():
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM users"); rows=c.fetchall(); conn.close()
    html=f'<html><head>{STYLE}</head><body style="padding:15px;"><h2>Users - Edit/Delete Password - V3.1</h2><a href="/users/add" class="btn btn-green">+ Add User</a> <a href="/" class="btn">Home</a><br><br><table><tr><th>ID</th><th>Username</th><th>Password</th><th>Role</th><th>Action</th></tr>'
    for r in rows:
        html+=f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><a class="btn" href="/users/edit/{r[0]}">Edit/Change Password</a> <a class="btn btn-red" href="/users/delete/{r[0]}" onclick="return confirm(\'Delete {r[1]}?\')">Delete</a></td></tr>'
    html+='</table><br><div class="card"><h3>How to secure:</h3><p>1. Click Edit on admin -> Change password to <b>Tudiheal0796@2026!</b><br>2. Save in notebook safe!<br>3. Then Add new user: denis / Tudiheal@2026!Machakos</p></div></body></html>'
    return html

@app.route('/users/add', methods=['GET','POST'])
@login_required
@admin_required
def users_add():
    if request.method=='POST':
        conn=sqlite3.connect('clinic.db'); c=conn.cursor()
        try:
            c.execute("INSERT INTO users (username,password,role,created_at) VALUES (?,?,?,?)", (request.form.get('username'), request.form.get('password'), request.form.get('role'), datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
        except: return "<h3>Username exists! <a href='/users'>Back</a></h3>"
        conn.close(); return redirect('/users')
    return f'<html><head>{STYLE}</head><body style="padding:20px;"><h2>Add User - Admin Only</h2><form method="POST"><input name="username" placeholder="Username e.g. denis" required><br><input name="password" placeholder="Password e.g. Tudiheal0796@2026!" required><br><select name="role"><option>admin</option><option>user</option><option>doctor</option><option>lab</option></select><br><button class="btn btn-green">Create</button></form><a href="/users">Back to Users</a></body></html>'

@app.route('/users/edit/<int:uid>', methods=['GET','POST'])
@login_required
@admin_required
def users_edit(uid):
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM users WHERE id=?", (uid,)); u=c.fetchone()
    if not u: conn.close(); return "User not found"
    if request.method=='POST':
        c.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?", (request.form.get('username'), request.form.get('password'), request.form.get('role'), uid))
        conn.commit(); conn.close(); return redirect('/users')
    conn.close()
    return f'<html><head>{STYLE}</head><body style="padding:20px;"><h2>Edit User - Change Password V3.1</h2><form method="POST"><label>Username:</label><br><input name="username" value="{u[1]}" required><br><label>Password - CHANGE HERE:</label><br><input name="password" value="{u[2]}" required><br><label>Role:</label><br><select name="role"><option value="admin" {"selected" if u[3]=="admin" else ""}>admin</option><option value="user" {"selected" if u[3]=="user" else ""}>user</option><option value="doctor" {"selected" if u[3]=="doctor" else ""}>doctor</option><option value="lab" {"selected" if u[3]=="lab" else ""}>lab</option></select><br><button class="btn btn-green">Update Password</button></form><a href="/users">Back</a></body></html>'

@app.route('/users/delete/<int:uid>')
@login_required
@admin_required
def users_delete(uid):
    if uid==1: return "<h3>Cannot delete main admin ID 1! Edit password instead. <a href='/users'>Back</a></h3>"
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("DELETE FROM users WHERE id=?", (uid,)); conn.commit(); conn.close()
    return redirect('/users')

@app.route('/expenses')
@login_required
def expenses():
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM expenses ORDER BY id DESC"); rows=c.fetchall(); conn.close()
    html=f'<html><head>{STYLE}</head><body style="padding:15px;"><h2>Expenses</h2><a href="/expenses/add" class="btn btn-green">+ Add Expense</a> <a href="/">Home</a><br><br><table><tr><th>ID</th><th>Title</th><th>Amount</th><th>Date</th></tr>'
    for r in rows: html+=f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>'
    html+='</table></body></html>'
    return html

@app.route('/expenses/add', methods=['GET','POST'])
@login_required
def expenses_add():
    if request.method=='POST':
        conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("INSERT INTO expenses (title,amount,date,created_by) VALUES (?,?,?,?)", (request.form.get('title'), request.form.get('amount'), request.form.get('date'), session.get('user')))
        conn.commit(); conn.close(); return redirect('/expenses')
    return f'<html><head>{STYLE}</head><body style="padding:20px;"><h2>Add Expense</h2><form method="POST"><input name="title" placeholder="Title" required><br><input name="amount" type="number" placeholder="Amount" required><br><input name="date" type="date" value="{datetime.now().strftime("%Y-%m-%d")}" required><br><button class="btn btn-green">Save</button></form></body></html>'

@app.route('/patients')
@login_required
def patients():
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM patients ORDER BY id DESC"); rows=c.fetchall(); conn.close()
    html=f'<html><head>{STYLE}</head><body style="padding:15px;"><h2>Patients</h2><a href="/patients/add" class="btn btn-green">+ Add Patient</a> <a href="/">Home</a><br><br><table><tr><th>ID</th><th>Name</th><th>Phone</th><th>Date</th></tr>'
    for r in rows: html+=f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[4]}</td></tr>'
    html+='</table></body></html>'
    return html

@app.route('/patients/add', methods=['GET','POST'])
@login_required
def patients_add():
    if request.method=='POST':
        conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("INSERT INTO patients (name,phone,age,gender,created_at) VALUES (?,?,?,?,?)", (request.form.get('name'), request.form.get('phone'), request.form.get('age'), request.form.get('gender'), datetime.now().strftime("%Y-%m-%d")))
        conn.commit(); conn.close(); return redirect('/patients')
    return f'<html><head>{STYLE}</head><body style="padding:20px;"><h2>Add Patient</h2><form method="POST"><input name="name" placeholder="Name" required><br><input name="phone" placeholder="Phone"><br><input name="age" placeholder="Age"><br><select name="gender"><option>Male</option><option>Female</option></select><br><button class="btn btn-green">Save</button></form></body></html>'

@app.route('/backup')
@login_required
@admin_required
def backup():
    if os.path.exists('clinic.db'): return send_file('clinic.db', as_attachment=True)
    return "No DB found"

if __name__=='__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)