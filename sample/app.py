import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import hashlib  # ✅ Using hashlib for password hashing (instead of bcrypt)
import smtplib  # ✅ Python's built-in email library
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import jsonify, make_response

app = Flask(__name__, static_folder="static", template_folder="templates")

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'rane@2004'  # Change if needed
app.config['MYSQL_DB'] = 'shelico_db'
app.secret_key = 'your_secret_key_here'

mysql = MySQL(app)

# ✅ Manual Hashing Function (Instead of bcrypt)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    user = None
    if 'user_id' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
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




# Configure session lifetime
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # User stays logged in for 7 days

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

@app.route('/commonlogin', methods=['GET', 'POST'])
def common_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # First check admin table
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admin WHERE email=%s AND password=%s", (email, password))
        admin = cursor.fetchone()
        
        if admin:
            session['admin_id'] = admin[0]
            session['name'] = admin[1]
            session['admin_email'] = admin[2]
            session['initial'] = admin[1][0].upper()
            cursor.close()
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # Then check user table
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and user[3] == hash_password(password):
            session.permanent = True
            session['user_id'] = user[0]
            session['user_email'] = user[1]
            session['username'] = user[2]
            session['initial'] = user[2][0].upper()
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
            return redirect(url_for('common_login'))

    return render_template('commonlogin.html')

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


# token for password
@app.route('/enter-token', methods=['GET', 'POST'])
def enter_token():
    if request.method == 'POST':
        email = request.form['email']
        token = request.form['token']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s AND reset_token=%s AND reset_token_expiry > NOW()", 
                       (email, token))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['reset_email'] = email  # Store email in session
            return redirect(url_for('reset_password'))  #  Allow password reset
        else:
            flash("Invalid or expired token!", "error")
            return redirect(url_for('enter_token'))

    return render_template('enter_token.html')



# reset password
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('reset_password'))

        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()  # Secure hashing

        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE users SET password=%s, reset_token=NULL, reset_token_expiry=NULL WHERE email=%s", 
                       (hashed_password, session['reset_email']))
        mysql.connection.commit()
        cursor.close()

        session.pop('reset_email', None)  
        flash('Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clears all session data
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))  # Redirect to home page


@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

# Function to send an email
def send_email(to_email, token):
    from_email = "divinewatchh@gmail.com"  #  Your email
    password = "gxiz gbez cydd nqbp"  # Your app password

    subject = "Your Password Reset Code"
    body = f"Your password reset token is: {token}\n\nEnter this token on the website to reset your password."

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)  # Gmail SMTP Server
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(" Email sent successfully!")
    except Exception as e:
        print(" Error sending email:", str(e))  # Debugging


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    
    # Fetch user details from DB
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name FROM users WHERE id=%s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return render_template('dashboard.html', name=user[0])  # Pass 'name' instead of 'username'
    else:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

@app.route('/ask-query', methods=['POST'])
def ask_query():
    try:
        query_text = request.form.get('queryText')
        visibility = request.form.get('visibility')
        
        # Process the query (save to database, etc.)
        print(f"Received query: {query_text} (Visibility: {visibility})")
        
        return jsonify({
            'status': 'success',
            'message': 'Query submitted successfully!'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


# Add these routes to your existing Flask app

@app.route('/get_helplines')
def get_all_helplines():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM health_helplines
            ORDER BY h_id DESC
        """)
        helplines = cursor.fetchall()
        cursor.close()
        
        # Convert to list of dictionaries
        helplines_list = []
        for hl in helplines:
            helplines_list.append({
                'h_id': hl[0],
                'title': hl[1],
                'description': hl[2],
                'admin_id': hl[3]
            })
        
        return jsonify({
            'status': 'success',
            'helplines': helplines_list
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_myth_cards')
def get_all_myth_cards():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM myth_cards
            ORDER BY myth_id DESC
        """)
        myth_cards = cursor.fetchall()
        cursor.close()
        
        # Convert to list of dictionaries
        myth_cards_list = []
        for mc in myth_cards:
            myth_cards_list.append({
                'myth_id': mc[0],
                'myth': mc[1],
                'fact': mc[2],
                'admin_id': mc[3]
            })
        
        return jsonify({
            'status': 'success',
            'myth_cards': myth_cards_list
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/add_helpline', methods=['POST'])
def add_helpline():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400

        title = data.get('title', '').strip()
        description = data.get('description', '').strip()

        if not title or not description:
            return jsonify({'status': 'error', 'message': 'Title and description are required'}), 400

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO health_helplines (title, description, admin_id) VALUES (%s, %s, %s)",
            (title, description, session['admin_id'])
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Helpline added successfully'
        })

    except Exception as e:
        print(f"Error adding helpline: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to add helpline'
        }), 500




@app.route('/add_myth_card', methods=['POST'])
def add_myth_card():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400

        myth = data.get('myth', '').strip()
        fact = data.get('fact', '').strip()

        if not myth or not fact:
            return jsonify({'status': 'error', 'message': 'Myth and fact are required'}), 400

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO myth_cards (myth, fact, admin_id) VALUES (%s, %s, %s)",
            (myth, fact, session['admin_id'])
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Myth card added successfully'
        })

    except Exception as e:
        print(f"Error adding myth card: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to add myth card'
        }), 500

# Add these new routes
# Add these routes to your Flask app if not already present


@app.route('/update_helpline', methods=['POST'])
def update_helpline():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        data = request.get_json()
        h_id = data.get('h_id')
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()

        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE health_helplines SET title=%s, description=%s WHERE h_id=%s AND admin_id=%s",
            (title, description, h_id, session['admin_id'])
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'status': 'success', 'message': 'Helpline updated'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/update_myth_card', methods=['POST'])
def update_myth_card():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        data = request.get_json()
        myth_id = data.get('myth_id')
        myth = data.get('myth', '').strip()
        fact = data.get('fact', '').strip()

        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE myth_cards SET myth=%s, fact=%s WHERE myth_id=%s AND admin_id=%s",
            (myth, fact, myth_id, session['admin_id'])
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'status': 'success', 'message': 'Myth card updated'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_helpline', methods=['POST'])
def delete_helpline():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        data = request.get_json()
        h_id = data.get('h_id')
        
        if not h_id:
            return jsonify({'status': 'error', 'message': 'Missing helpline ID'}), 400

        cursor = mysql.connection.cursor()
        
        # First check if the helpline exists and belongs to this admin
        cursor.execute(
            "SELECT * FROM health_helplines WHERE h_id=%s AND admin_id=%s",
            (h_id, session['admin_id'])
        )
        helpline = cursor.fetchone()
        
        if not helpline:
            cursor.close()
            return jsonify({'status': 'error', 'message': 'Helpline not found or not authorized'}), 404

        # Delete the helpline
        cursor.execute(
            "DELETE FROM health_helplines WHERE h_id=%s AND admin_id=%s",
            (h_id, session['admin_id'])
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'status': 'success', 'message': 'Helpline deleted successfully'})

    except Exception as e:
        print(f"Error deleting helpline: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to delete helpline'}), 500

@app.route('/delete_myth_card', methods=['POST'])
def delete_myth_card():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        data = request.get_json()
        myth_id = data.get('myth_id')
        
        if not myth_id:
            return jsonify({'status': 'error', 'message': 'Missing myth card ID'}), 400

        cursor = mysql.connection.cursor()
        
        # First check if the myth card exists and belongs to this admin
        cursor.execute(
            "SELECT * FROM myth_cards WHERE myth_id=%s AND admin_id=%s",
            (myth_id, session['admin_id'])
        )
        myth_card = cursor.fetchone()
        
        if not myth_card:
            cursor.close()
            return jsonify({'status': 'error', 'message': 'Myth card not found or not authorized'}), 404

        # Delete the myth card
        cursor.execute(
            "DELETE FROM myth_cards WHERE myth_id=%s AND admin_id=%s",
            (myth_id, session['admin_id'])
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'status': 'success', 'message': 'Myth card deleted successfully'})

    except Exception as e:
        print(f"Error deleting myth card: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to delete myth card'}), 500
        
if __name__ == '__main__':
    app.run(debug=True)
