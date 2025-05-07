from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import timedelta, datetime
import random

app = Flask(__name__, static_folder="static", template_folder="templates")

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'rane@2004'  # Change if needed
app.config['MYSQL_DB'] = 'shelico_db'
app.secret_key = 'your_secret_key_here'

mysql = MySQL(app)

@app.route('/')
def index():
    user = None
    if 'user_id' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=%s", (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
    
    return render_template('index.html', user=user)

from flask import session

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']  # Get full name
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))

        hashed_password = hash_password(password)

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        
        if user:
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))

        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        
        session['username'] = name  # Store full name in session

        flash('Signup successful! Redirecting...', 'success')
        return redirect(url_for('thankyou'))  

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and user[3] == hash_password(password):  # ✅ Checking hashed password
            session.permanent = True  # 🔹 Make session persistent
            session['user_id'] = user[0]  # Store user ID in session
            session['user_email'] = user[1]  # Store user email for display
            session['username'] = user[2]  # Store user's full name
            session['initial'] = user[2][0].upper()  # Store first letter as profile initial

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # ✅ Redirect to dashboard

        else:
            flash('Invalid email or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/adminlogin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admin WHERE email=%s AND password=%s", (email, password))
        admin = cursor.fetchone()
        cursor.close()

        if admin:
            session['admin_id'] = admin[0]
            session['name'] = admin[1]  # Full name
            session['admin_email'] = admin[2]  # Email
            session['initial'] = admin[1][0].upper()  # First letter of name
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
            return redirect(url_for('admin_login'))

    return render_template('adminlogin.html')

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/admindashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admindashboard.html')

# forgot password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        print(f"📩 Forgot password requested for: {email}")  #Debugging

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            token = ''.join(random.choices("0123456789", k=6))  # Generate 6-digit token
            expiry_time = datetime.now() + timedelta(minutes=30)  

            cursor.execute("UPDATE users SET reset_token=%s, reset_token_expiry=%s WHERE email=%s", 
                           (token, expiry_time, email))
            mysql.connection.commit()
            cursor.close()

            print(f" Generated token: {token}")  #Debugging
            send_email(email, token)  #Send email

            flash("A password reset token has been sent to your email.", "info")
            return redirect(url_for('enter_token'))
        else:
            flash('Email not found!', 'error')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')