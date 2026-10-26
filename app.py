from flask import Flask, request, redirect, session
import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tudiheal2026_secure_123")

STYLE = """<style>body{font-family:Arial;background:#f4f6f9;margin:0}.btn{padding:6px 12px;background:#007bff;color:white;text-decoration:none;border-radius:4px;margin:2px;display:inline-block}.btn-green{background:#28a745}.btn-red{background:#dc3545}table{width:100%;background:white;border-collapse:collapse}th,td{padding:8px;border:1px solid #ddd}input,select{padding:8px;margin:5px;width:90%}.card{background:white;padding:15px;margin:10px;border-radius:8px}</style>"""

def init_db():
    conn=sqlite3.connect('clinic.db'); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, age TEXT, gender TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, title TEXT, amount REAL, date TEXT, created_by TEXT)")
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (NULL,?,?,?,?)", ('admin', generate_password_hash('admin'), 'admin', datetime.now().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()
init_db()

def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if 'user' not in session: return redirect('/login')
        return f(*a, **k)
    return wrap
def admin_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if session.get('role')!='admin': return "<h3>Admin Only! <a href='/'>Home</a></h3>"
        return f(*a, **k)
    return wrap

@app.route('/')
@login_required
def home(): return f'<html><head>{STYLE}</head><body style="padding:20px"><h1>Tudiheal V3.2 Secure</h1><p>{session.get("user")} | {session.get("role")}</p><div class="card"><a class="btn" href="/patients">Patients</a> <a class="btn" href="/expenses">Expenses</a> <a class="btn btn-green" href="/users">Users</a> <a class="btn btn-red" href="/logout">Logout</a></div></body></html>'

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form.get('username'); p=request.form.get('password')
        conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM users WHERE username=?", (u,)); r=c.fetchone(); conn.close()
        if r and check_password_hash(r[2], p): session['user']=r[1]; session['role']=r[3]; return redirect('/')
        else: return "<h3>Wrong password! <a href='/login'>Try again</a></h3>"
    return f'<html><head>{STYLE}</head><body style="padding:20px"><h2>Login V3.2</h2><form method="POST"><input name="username" placeholder="Username" required><br><input type="password" name="password" placeholder="Password" required><br><button class="btn btn-green">Login</button></form><p>Default: admin / admin</p></body></html>'

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/users')
@login_required
@admin_required
def users_list():
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM users"); rows=c.fetchall(); conn.close()
    h=f'<html><head>{STYLE}</head><body style="padding:15px"><h2>Users V3.2</h2><a href="/users/add" class="btn btn-green">+ Add</a> <a href="/" class="btn">Home</a><br><br><table><tr><th>ID</th><th>User</th><th>Role</th><th>Action</th></tr>'
    for r in rows: h+=f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[3]}</td><td><a class="btn" href="/users/edit/{r[0]}">Edit</a> <a class="btn btn-red" href="/users/delete/{r[0]}">Del</a></td></tr>'
    h+='</table></body></html>'; return h

@app.route('/users/add', methods=['GET','POST'])
@login_required
@admin_required
def users_add():
    if request.method=='POST':
        conn=sqlite3.connect('clinic.db'); c=conn.cursor()
        try:
            c.execute("INSERT INTO users VALUES (NULL,?,?,?,?)", (request.form.get('username'), generate_password_hash(request.form.get('password')), request.form.get('role'), datetime.now().strftime("%Y-%m-%d"))); conn.commit()
        except: conn.close(); return "<h3>Username exists! <a href='/users'>Back</a></h3>"
        conn.close(); return redirect('/users')
    return f'<html><head>{STYLE}</head><body style="padding:20px"><h2>Add User</h2><form method="POST"><input name="username" required placeholder="Username"><br><input name="password" type="password" required placeholder="Password"><br><select name="role"><option>admin</option><option>user</option><option>doctor</option><option>lab</option></select><br><button class="btn btn-green">Create</button></form></body></html>'

@app.route('/users/edit/<int:uid>', methods=['GET','POST'])
@login_required
@admin_required
def users_edit(uid):
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM users WHERE id=?", (uid,)); u=c.fetchone()
    if not u: conn.close(); return "Not found"
    if request.method=='POST':
        c.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?", (request.form.get('username'), generate_password_hash(request.form.get('password')), request.form.get('role'), uid)); conn.commit(); conn.close(); return redirect('/users')
    conn.close()
    return f'<html><head>{STYLE}</head><body style="padding:20px"><h2>Edit Password</h2><form method="POST"><input name="username" value="{u[1]}" required><br><input name="password" type="password" placeholder="Password MPYA" required><br><select name="role"><option value="admin" {"selected" if u[3]=="admin" else ""}>admin</option><option value="user">user</option><option value="doctor">doctor</option><option value="lab">lab</option></select><br><button class="btn btn-green">Update</button></form></body></html>'

@app.route('/users/delete/<int:uid>')
@login_required
@admin_required
def users_delete(uid):
    if uid==1: return "<h3>Cannot delete ID 1! <a href='/users'>Back</a></h3>"
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("DELETE FROM users WHERE id=?", (uid,)); conn.commit(); conn.close(); return redirect('/users')

@app.route('/patients')
@login_required
def patients():
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM patients ORDER BY id DESC"); rows=c.fetchall(); conn.close()
    h=f'<html><head>{STYLE}</head><body style="padding:15px"><h2>Patients</h2><a href="/patients/add" class="btn btn-green">+ Add</a> <a href="/">Home</a><table><tr><th>Name</th><th>Phone</th></tr>'; 
    for r in rows: h+=f'<tr><td>{r[1]}</td><td>{r[2]}</td></tr>'
    h+='</table></body></html>'; return h

@app.route('/patients/add', methods=['GET','POST'])
@login_required
def patients_add():
    if request.method=='POST':
        conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("INSERT INTO patients VALUES (NULL,?,?,?,?,?)", (request.form.get('name'), request.form.get('phone'), request.form.get('age'), request.form.get('gender'), datetime.now().strftime("%Y-%m-%d"))); conn.commit(); conn.close(); return redirect('/patients')
    return f'<html><head>{STYLE}</head><body style="padding:20px"><h2>Add Patient</h2><form method="POST"><input name="name" placeholder="Name" required><br><input name="phone" placeholder="Phone"><br><button class="btn btn-green">Save</button></form></body></html>'

@app.route('/expenses')
@login_required
def expenses():
    conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("SELECT * FROM expenses ORDER BY id DESC"); rows=c.fetchall(); conn.close()
    h=f'<html><head>{STYLE}</head><body style="padding:15px"><h2>Expenses</h2><a href="/expenses/add" class="btn btn-green">+ Add</a> <a href="/">Home</a><table><tr><th>Title</th><th>Amount</th></tr>';
    for r in rows: h+=f'<tr><td>{r[1]}</td><td>{r[2]}</td></tr>'
    h+='</table></body></html>'; return h

@app.route('/expenses/add', methods=['GET','POST'])
@login_required
def expenses_add():
    if request.method=='POST':
        conn=sqlite3.connect('clinic.db'); c=conn.cursor(); c.execute("INSERT INTO expenses VALUES (NULL,?,?,?,?)", (request.form.get('title'), request.form.get('amount'), request.form.get('date'), session.get('user'))); conn.commit(); conn.close(); return redirect('/expenses')
    return f'<html><head>{STYLE}</head><body style="padding:20px"><h2>Add Expense</h2><form method="POST"><input name="title" required><br><input name="amount" type="number" required><br><input name="date" type="date" value="{datetime.now().strftime("%Y-%m-%d")}" required><br><button class="btn btn-green">Save</button></form></body></html>'

if __name__=='__main__':
    port=int(os.environ.get("PORT",5000)); app.run(host='0.0.0.0', port=port)
