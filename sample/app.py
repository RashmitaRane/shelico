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
# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

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

        # hashed_password = hash_password(password)

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        
        if user:
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))

        # cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))

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

        # if user and user[3] == hash_password(password):  # ✅ Checking hashed password/
        if user and user[3] == password: 
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

        # hashed_password = hashlib.sha256(new_password.encode()).hexdigest()  # Secure hashing

        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE users SET password=%s, reset_token=NULL, reset_token_expiry=NULL WHERE email=%s", 
                    #    (hashed_password, session['reset_email']))
                     (new_password, session['reset_email']))
       
        mysql.connection.commit()
        cursor.close()

        session.pop('reset_email', None)  
        flash('Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

#route for admin forgot password
@app.route('/admin/forgot-password', methods=['GET', 'POST'])
def admin_forgot_password():
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        # Get admin email from database
        cursor.execute("SELECT email FROM admin LIMIT 1")
        admin = cursor.fetchone()
        
        if not admin:
            flash('Admin account not found!', 'error')
            return redirect(url_for('admin_forgot_password'))
        
        admin_email = admin[0]  # Get the admin's email from DB
        token = ''.join(random.choices("0123456789", k=6))
        expiry_time = datetime.now() + timedelta(minutes=30)
        
        # Store token in admin table
        cursor.execute("""
            UPDATE admin 
            SET reset_token=%s, reset_token_expiry=%s 
            WHERE email=%s
        """, (token, expiry_time, admin_email))
        mysql.connection.commit()
        cursor.close()
        
        # Send email to ADMIN's email address
        send_email(admin_email, token)
        
        flash(f"A password reset token has been sent to {admin_email}", "info")
        return redirect(url_for('admin_enter_token'))
    
    return render_template('admin_forgot_password.html')


@app.route('/admin/enter-token', methods=['GET', 'POST'])
def admin_enter_token():
    if request.method == 'POST':
        token = request.form['token']
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT email FROM admin 
            WHERE reset_token=%s AND reset_token_expiry > NOW()
        """, (token,))
        admin = cursor.fetchone()
        cursor.close()
        
        if admin:
            session['admin_reset_email'] = admin[0]
            return redirect(url_for('admin_reset_password'))
        else:
            flash("Invalid or expired token!", "error")
            return redirect(url_for('admin_enter_token'))
    
    # Get admin email from database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email FROM admin LIMIT 1")
    admin_email = cursor.fetchone()[0]
    cursor.close()
    
    return render_template('enter_token.html', email=admin_email, is_admin=True, show_email_input=False)

#  route for admin password reset
@app.route('/admin/reset-password', methods=['GET', 'POST'])
def admin_reset_password():
    if 'admin_reset_email' not in session:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('admin_reset_password'))
        
        hashed_password = hash_password(new_password)
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE admin 
            SET password=%s, reset_token=NULL, reset_token_expiry=NULL 
            WHERE email=%s
        """, (hashed_password, session['admin_reset_email']))
        mysql.connection.commit()
        cursor.close()
        
        session.pop('admin_reset_email', None)
        flash('Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('admin_login'))
    
    return render_template('reset_password.html', is_admin=True)


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
    password = "ubsc ioal fxfy kijm"  # Your app password

    subject = "Your Password Reset Code"
    body = f"Your password reset token is: {token}\n\nEnter this token on the website to reset your password."

    # This token will expire in 30 minutes

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
    cursor.execute("SELECT name FROM users WHERE user_id=%s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return render_template('dashboard.html', name=user[0])  # Pass 'name' instead of 'username'
    else:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

# In your Flask app.py (or wherever your routes are defined)

@app.route('/ask-query', methods=['POST'])
def ask_query():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please login to post a query'})
    
    data = request.get_json()
    query_text = data.get('queryText')
    visibility = data.get('visibility')
    
    if not query_text:
        return jsonify({'status': 'error', 'message': 'Query text cannot be empty'})
    
    try:
        # Insert query into database
        cursor = db.connection.cursor()
        cursor.execute(
            "INSERT INTO health_queries (user_id, query, visibility) VALUES (%s, %s, %s)",
            (session['user_id'], query_text, visibility)
        )
        db.connection.commit()
        
        return jsonify({'status': 'success', 'message': 'Query posted successfully'})
    except Exception as e:
        db.connection.rollback()
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/submit_query', methods=['POST'])
def submit_query():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in first'}), 401

    try:
        data = request.get_json()
        query_text = data.get('queryText', '').strip()
        visibility = data.get('visibility', 'public')

        if not query_text:
            return jsonify({'status': 'error', 'message': 'Query text is required'}), 400

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO health_queries (user_id, query, visibility) VALUES (%s, %s, %s)",
            (session['user_id'], query_text, visibility)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Query submitted successfully!'
        })

    except Exception as e:
        print("Error submitting query:", str(e))
        return jsonify({'status': 'error', 'message': 'Database error'}), 500

@app.route('/get_queries')
def get_queries():
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT q.query_id, q.query, q.visibility, q.status, q.created_at, 
                   u.user_id, u.name as username
            FROM health_queries q
            JOIN users u ON q.user_id = u.user_id
            ORDER BY q.created_at DESC
        """)
        
        queries = cursor.fetchall()
        cursor.close()
        
        queries_list = []
        for q in queries:
            queries_list.append({
                'query_id': q[0],
                'query': q[1],
                'visibility': q[2],
                'status': q[3],
                'created_at': q[4].strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': q[5],
                'username': q[6]
            })
        
        return jsonify({
            'status': 'success',
            'queries': queries_list
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
@app.route('/get_query_responses/<int:query_id>')
def get_query_responses(query_id):
    try:
        cursor = mysql.connection.cursor()
        
        # Get the query and responses
        cursor.execute("""
            SELECT q.query_id, q.query, q.created_at, u.user_id, u.name as username,
                   r.response_id, r.response, r.created_at as response_date,
                   a.name as admin_name
            FROM health_queries q
            JOIN users u ON q.user_id = u.user_id
            LEFT JOIN query_response r ON q.query_id = r.query_id
            LEFT JOIN admin a ON r.admin_id = a.admin_id
            WHERE q.query_id = %s
            ORDER BY r.created_at DESC
        """, (query_id,))
        
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            return jsonify({'status': 'error', 'message': 'Query not found'}), 404
        
        # Format the response
        query_data = {
            'query_id': results[0][0],
            'query': results[0][1],
            'created_at': results[0][2].strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': results[0][3],
            'username': results[0][4]
        }
        
        responses = []
        for row in results:
            if row[5]:  # If there's a response_id
                responses.append({
                    'response_id': row[5],
                    'response': row[6],
                    'created_at': row[7].strftime('%Y-%m-%d %H:%M:%S'),
                    'admin_name': row[8]
                })
        
        return jsonify({
            'status': 'success',
            'query': query_data,
            'responses': responses
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update_response', methods=['POST'])
def update_response():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    cursor = mysql.connection.cursor()
    try:
        response_id = request.form.get('response_id')
        response_text = request.form.get('response_text', '').strip()

        if not response_id or not response_text:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        # Verify ownership
        cursor.execute(
            "SELECT query_id FROM query_response WHERE response_id = %s AND admin_id = %s",
            (response_id, session['admin_id'])
        )
        result = cursor.fetchone()
        if not result:
            return jsonify({'status': 'error', 'message': 'Response not found'}), 404

        query_id = result[0]

        # Update response
        cursor.execute(
            "UPDATE query_response SET response = %s WHERE response_id = %s",
            (response_text, response_id)
        )
        
        # Ensure status is set to replied
        cursor.execute(
            "UPDATE health_queries SET status = 'replied' WHERE query_id = %s",
            (query_id,)
        )
        
        mysql.connection.commit()
        return jsonify({'status': 'success', 'message': 'Response updated successfully'})

    except Exception as e:
        mysql.connection.rollback()
        print(f"Error updating response: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()

@app.route('/submit_response', methods=['POST'])
def submit_response():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    cursor = mysql.connection.cursor()
    try:
        query_id = request.form['query_id']
        response_text = request.form['response_text'].strip()

        # Insert response
        cursor.execute(
            "INSERT INTO query_response (query_id, admin_id, response) VALUES (%s, %s, %s)",
            (query_id, session['admin_id'], response_text)
        )
        
        # Update query status to 'replied'
        cursor.execute(
            "UPDATE health_queries SET status = 'replied' WHERE query_id = %s",
            (query_id,)
        )
        
        mysql.connection.commit()
        return jsonify({
            'status': 'success', 
            'message': 'Response submitted successfully',
            'new_status': 'replied'
        })

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()

@app.route('/delete_response', methods=['POST'])
def delete_response():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:

        data = request.get_json()
        response_id = data.get('response_id')
        query_id = data.get('query_id')

        cursor = mysql.connection.cursor()

        # Delete the response
        cursor.execute("DELETE FROM query_response WHERE response_id = %s", (response_id,))
        mysql.connection.commit()

        # Check if there are any other responses left for this query
        cursor.execute("SELECT COUNT(*) FROM query_response WHERE query_id = %s", (query_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            # No responses left, update status to pending
            cursor.execute("UPDATE health_queries SET status = 'pending' WHERE query_id = %s", (query_id,))
            mysql.connection.commit()

        cursor.close()
        return jsonify({
        'status': 'success', 
        'message': 'Response deleted successfully',
        'query_status': 'pending' if count == 0 else 'replied' 
    })

    except Exception as e:
        mysql.connection.rollback()
        print("Error deleting response:", str(e))
        return jsonify({'status': 'error', 'message': 'Database error'})


@app.route('/get_helplines')
def get_all_helplines():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT h_id, title, location, description 
            FROM health_helplines
            WHERE admin_id = %s
            ORDER BY h_id DESC
        """, (session['admin_id'],))
        helplines = cursor.fetchall()
        cursor.close()
        
        helplines_list = []
        for hl in helplines:
            helplines_list.append({
                'h_id': hl[0],
                'title': hl[1],
                'location': hl[2] if hl[2] else 'N/A',
                'description': hl[3]
            })
        
        return jsonify({
            'status': 'success',
            'helplines': helplines_list
        })
        
    except Exception as e:
        print(f"Error fetching helplines: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': 'Failed to load helplines: ' + str(e)
        }), 500

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
        location = data.get('location', '').strip()
        description = data.get('description', '').strip()

        if not title or not description:
            return jsonify({'status': 'error', 'message': 'Title and description are required'}), 400

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO health_helplines (title, location, description, admin_id) VALUES (%s, %s, %s, %s)",
            (title, location, description, session['admin_id'])
        )
        mysql.connection.commit()
        
        # Get the ID of the newly inserted helpline
        helpline_id = cursor.lastrowid
        
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Helpline added successfully',
            'h_id': helpline_id
        })

    except Exception as e:
        print(f"Error adding helpline: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to add helpline: ' + str(e)
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
        location = data.get('location', '').strip()
        description = data.get('description', '').strip()

        if not h_id or not title or not description:
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

        cursor = mysql.connection.cursor()
        
        # Verify ownership before update
        cursor.execute(
            "SELECT admin_id FROM health_helplines WHERE h_id=%s",
            (h_id,)
        )
        result = cursor.fetchone()
        
        if not result or result[0] != session['admin_id']:
            cursor.close()
            return jsonify({
                'status': 'error',
                'message': 'Helpline not found or not owned by you'
            }), 404

        cursor.execute(
            "UPDATE health_helplines SET title=%s, location=%s, description=%s WHERE h_id=%s",
            (title, location, description, h_id)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Helpline updated successfully',
            'h_id': h_id
        })

    except Exception as e:
        print(f"Error updating helpline: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update helpline: ' + str(e)
        }), 500



@app.route('/update_myth_card', methods=['POST'])
def update_myth_card():
    try:
        if 'admin_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
            
        data = request.get_json()
        myth_id = data.get('myth_id')
        myth = data.get('myth', '').strip()
        fact = data.get('fact', '').strip()

        if not myth_id or not myth or not fact:
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

        cursor = mysql.connection.cursor()
        
        # Verify ownership before update
        cursor.execute(
            "SELECT myth_id FROM myth_cards WHERE myth_id=%s AND admin_id=%s",
            (myth_id, session['admin_id'])
        )
        if not cursor.fetchone():
            cursor.close()
            return jsonify({
                'status': 'error',
                'message': 'Myth card not found or not owned by you'
            }), 404

        # Perform the update
        cursor.execute(
            "UPDATE myth_cards SET myth=%s, fact=%s WHERE myth_id=%s",
            (myth, fact, myth_id)
        )
        mysql.connection.commit()
        
        # Get the updated record
        cursor.execute(
            "SELECT myth_id, myth, fact FROM myth_cards WHERE myth_id=%s",
            (myth_id,)
        )
        updated_card = cursor.fetchone()
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Myth card updated successfully',
            'myth_card': {
                'myth_id': updated_card[0],
                'myth': updated_card[1],
                'fact': updated_card[2]
            }
        })

    except Exception as e:
        print(f"Error updating myth card: {str(e)}")
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
        
        # Verify ownership before deletion
        cursor.execute(
            "SELECT admin_id FROM health_helplines WHERE h_id = %s",
            (h_id,)
        )
        result = cursor.fetchone()
        
        if not result or result[0] != session['admin_id']:
            cursor.close()
            return jsonify({
                'status': 'error', 
                'message': 'Helpline not found or not owned by you'
            }), 404

        cursor.execute(
            "DELETE FROM health_helplines WHERE h_id = %s",
            (h_id,)
        )
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'status': 'success', 
            'message': 'Helpline deleted successfully'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_myth_card', methods=['POST'])
def delete_myth_card():
    try:
        # 1. Authentication Check
        if 'admin_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access. Please log in as admin.'
            }), 401

        # 2. Input Validation
        data = request.get_json()
        myth_id = data.get('myth_id')
        
        if not myth_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing myth card ID'
            }), 400

        cursor = mysql.connection.cursor()

        # 3. Verify record exists and belongs to admin
        cursor.execute("""
            SELECT myth_id FROM myth_cards 
            WHERE myth_id = %s AND admin_id = %s
        """, (myth_id, session['admin_id']))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({
                'status': 'error',
                'message': 'Myth card not found or not owned by you'
            }), 404

        # 4. Perform deletion
        cursor.execute("""DELETE FROM myth_cards WHERE myth_id = %s """, (myth_id,))
        
        mysql.connection.commit()
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Myth card deleted successfully'
        })

    except Exception as e:
        print(f"Error deleting myth card: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to delete myth card'
        }), 500

@app.route('/get_helpline')
def get_helpline():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    h_id = request.args.get('id')
    if not h_id:
        return jsonify({'status': 'error', 'message': 'Missing helpline ID'}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT h_id, title, location, description FROM health_helplines WHERE h_id = %s AND admin_id = %s", (h_id, session['admin_id']))
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return jsonify({'status': 'error', 'message': 'Helpline not found'}), 404

    return jsonify({
        'status': 'success',
        'helpline': {
            'h_id': result[0],
            'title': result[1],
            'location': result[2],
            'description': result[3]
        }
    })

@app.route('/get_myth_card')
def get_myth_card():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    myth_id = request.args.get('id')
    if not myth_id:
        return jsonify({'status': 'error', 'message': 'Missing myth card ID'}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT myth_id, myth, fact FROM myth_cards WHERE myth_id = %s AND admin_id = %s", (myth_id, session['admin_id']))
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return jsonify({'status': 'error', 'message': 'Myth card not found'}), 404

    return jsonify({
        'status': 'success',
        'myth_card': {
            'myth_id': result[0],
            'myth': result[1],
            'fact': result[2]
        }
    })


@app.route('/user/get_helplines')
def user_get_helplines():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT h_id, title, location, description 
            FROM health_helplines
            ORDER BY h_id DESC
        """)
        helplines = cursor.fetchall()
        cursor.close()
        
        helplines_list = []
        for hl in helplines:
            helplines_list.append({
                'h_id': hl[0],
                'title': hl[1],
                'location': hl[2] if hl[2] else 'N/A',
                'description': hl[3]
            })
        
        return jsonify({
            'status': 'success',
            'helplines': helplines_list
        })
        
    except Exception as e:
        print(f"Error fetching helplines: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': 'Failed to load helplines. Please try again later.'
        }), 500

@app.route('/user/get_myth_cards')
def user_get_myth_cards():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM myth_cards ORDER BY myth_id DESC")
        myth_cards = cursor.fetchall()
        cursor.close()
        
        myth_cards_list = []
        for mc in myth_cards:
            myth_cards_list.append({
                'myth_id': mc[0],
                'myth': mc[1],
                'fact': mc[2]
            })
        
        return jsonify({
            'status': 'success',
            'myth_cards': myth_cards_list
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_dashboard_stats')
def get_dashboard_stats():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        cursor = mysql.connection.cursor()

        # Count helplines
        cursor.execute("SELECT COUNT(*) FROM health_helplines")
        total_helplines = cursor.fetchone()[0]

        # Count myth cards
        cursor.execute("SELECT COUNT(*) FROM myth_cards")
        total_myths = cursor.fetchone()[0]

        # Count stories posted today
        cursor.execute("SELECT COUNT(*) FROM stories")
        total_stories = cursor.fetchone()[0]

         # Count all regular users 
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # Fetch recent 5 posts from all tables
        cursor.execute("""
            SELECT 'Helpline' AS type, title AS content, created_at FROM health_helplines
            UNION ALL
            SELECT 'Myth Card' AS type, myth AS content, created_at FROM myth_cards
            UNION ALL
            SELECT 'Story' AS type, title AS content, created_at FROM stories
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_rows = cursor.fetchall()

        recent_activities = []
        for row in recent_rows:
            activity_type, content, created_at = row
            if activity_type == 'Helpline':
                icon = 'bxs-phone-call'
            elif activity_type == 'Myth Card':
                icon = 'bxs-ghost'
            else:  # Story
                icon = 'bxs-book-alt'
                
            recent_activities.append({
                'icon': icon,
                'title': f'{activity_type} Posted',
                'description': content,
                'time': created_at.strftime('%d %b %Y %I:%M %p')
            })

        cursor.close()

        return jsonify({
            'status': 'success',
            'total_helplines': total_helplines,
            'total_myths': total_myths,
            'pending_queries': 0,  # You can implement this later if needed
            'new_stories': total_stories,
            'total_users': total_users,
            'recent_activities': recent_activities
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/post_story', methods=['POST'])
def post_story():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in first'}), 401

    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        story_text = data.get('storyText', '').strip()

        if not story_text:
            return jsonify({'status': 'error', 'message': 'Story text is required'}), 400

        if not title:
            title = f"Story by {session['username']}"

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO stories (user_id, title, story) VALUES (%s, %s, %s)",
            (session['user_id'], title, story_text)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({
            'status': 'success',
            'message': 'Story posted successfully!',
            'update_dashboard': True  # Add this flag
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_stories')
def get_stories():
    try:
        cursor = mysql.connection.cursor()
        
        # Basic query without any external dependencies
        cursor.execute("""
            SELECT s.story_id, s.title, s.story, s.created_at, u.user_id, u.name
            FROM stories s
            JOIN users u ON s.user_id = u.user_id
            ORDER BY s.created_at DESC
        """)
        
        stories = []
        for row in cursor.fetchall():
            stories.append({
                'story_id': row[0],
                'title': row[1] or 'Untitled',
                'story': row[2],
                'created_at': row[3].strftime('%Y-%m-%d'),
                'user_id': row[4],
                'username': row[5] or 'Anonymous'
            })
        
        cursor.close()
        return jsonify({'status': 'success', 'stories': stories})
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Database error'}), 500

@app.route('/get_user_stories')
def get_user_stories():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in first'}), 401

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT s.story_id, s.title, s.story, s.created_at, u.user_id, u.name as username
            FROM stories s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.user_id = %s
            ORDER BY s.created_at DESC
        """, (session['user_id'],))
        
        stories = []
        for row in cursor.fetchall():
            stories.append({
                'story_id': row[0],
                'title': row[1] or 'Untitled',
                'story': row[2],
                'created_at': row[3].strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': row[4],
                'username': row[5]
            })
        
        cursor.close()
        return jsonify({'status': 'success', 'stories': stories})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_user_queries')
def get_user_queries():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in first'}), 401

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT q.query_id, q.query, q.visibility, q.status, q.created_at, 
                   u.user_id, u.name as username
            FROM health_queries q
            JOIN users u ON q.user_id = u.user_id
            WHERE q.user_id = %s
            ORDER BY q.created_at DESC
        """, (session['user_id'],))
        
        queries = []
        for row in cursor.fetchall():
            queries.append({
                'query_id': row[0],
                'query': row[1],
                'visibility': row[2],
                'status': row[3],
                'created_at': row[4].strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': row[5],
                'username': row[6]
            })
        
        cursor.close()
        return jsonify({'status': 'success', 'queries': queries})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
if __name__ == '__main__':
    app.run(debug=True)
