from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.serving import WSGIRequestHandler
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

connection = None
cursor = None

# Database connection
def get_db():
    global connection, cursor
    if connection is None:
        connection = sqlite3.connect("criminal_records.db")
        cursor = connection.cursor()
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS records (
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            age INTEGER,
                            blood_group TEXT,
                            crime TEXT,
                            area_of_crime TEXT,
                            state_of_crime TEXT,
                            status TEXT)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            username TEXT UNIQUE,
                            password TEXT,
                            email TEXT UNIQUE)""")
        connection.commit()
    return connection, cursor

# Redirect to login if not authenticated
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home_page():
    return render_template('home.html')

@app.route('/database')
@login_required
def database():
    return render_template('info.html')

@app.route('/aboutus')
@login_required
def aboutus():
    return render_template('aboutus.html')

@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')

@app.route('/emergency')
@login_required
def emergency():
    return render_template('emergency.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/quick_search', methods=['POST'])
def quick_search():
    if request.method == 'POST':
        location = request.form['location']
        connection, cursor = get_db()
        cursor.execute("SELECT * FROM records WHERE area_of_crime LIKE ? OR state_of_crime LIKE ?", ('%' + location + '%', '%' + location + '%'))
        records = cursor.fetchall()
        if records:
            flash("Search results:", "info")
        else:
            flash("No records found matching the search criteria.", "warning")
        return render_template('home.html', records=records)
    
@app.route('/profile')
@login_required
def profile():
    connection, cursor = get_db()
    cursor.execute("SELECT * FROM users WHERE username=?", (session['username'],))
    user = cursor.fetchone()
    if user:
        user_data = {
            'username': user[1],
            'email': user[3]
        }
        return render_template('profile.html', user=user_data)
    else:
        flash("User not found.", "danger")
        return redirect(url_for('home_page'))
    

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    connection, cursor = get_db()
    cursor.execute("SELECT * FROM users WHERE username=?", (session['username'],))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        response = {'success': False, 'message': 'An error occurred.'}
        
        new_username = request.form.get('new_username', '')
        new_email = request.form.get('new_email', '')
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Update username and email
        try:
            cursor.execute("UPDATE users SET username=?, email=? WHERE id=?", (new_username, new_email, session['user_id']))
            connection.commit()
            response['message'] = "Profile updated successfully!"
            response['success'] = True
            
            # Update session username if it has changed
            if session['username'] != new_username:
                session['username'] = new_username
        except Exception as e:
            response['message'] = f"An error occurred: {e}"
        
        # Change password if new password fields are provided
        if current_password and new_password and new_password == confirm_password:
            cursor.execute("SELECT * FROM users WHERE id=?", (session['user_id'],))
            user_data = cursor.fetchone()
            
            if user_data and check_password_hash(user_data[2], current_password):
                hashed_password = generate_password_hash(new_password, method='sha256')
                try:
                    cursor.execute("UPDATE users SET password=? WHERE id=?", (hashed_password, session['user_id']))
                    connection.commit()
                    response['message'] += " Password updated successfully!"
                    response['success'] = True
                except Exception as e:
                    response['message'] += f" An error occurred: {e}"
            else:
                response['message'] = "Invalid current password. Password not updated."
        elif new_password != confirm_password:
            response['message'] = "New password and confirm password do not match. Password not updated."
        
        return jsonify(response)
    
    if user:
        user_data = {
            'username': user[1],
            'email': user[3]
        }
        return render_template('edit_profile.html', user=user_data)
    else:
        flash("User not found.", "danger")
        return redirect(url_for('home_page'))



@app.route('/index')
def index():
    connection, cursor = get_db()
    cursor.execute("SELECT * FROM records")
    records = cursor.fetchall()
    return render_template('info.html', records=records)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        connection, cursor = get_db()
        username = request.form['username']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for('home_page'))
        else:
            flash("Invalid username or password.", "danger")
    
    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        connection, cursor = get_db()
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
    
        if request.form['password'] != request.form['confirm_password']:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(password, method='sha256')
        
        try:
            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                           (username, hashed_password, email))
            connection.commit()
            
            # Set session variables for the logged-in user
            session['username'] = username
            session['logged_in'] = True
            
            # Flash message for successful signup
            flash("Account created successfully!", "success")
            return redirect(url_for('home_page'))  # Redirect to home page after successful signup
        except sqlite3.IntegrityError:
            flash("Username or email already exists.", "danger")
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        connection, cursor = get_db()
        username_email = request.form['username_email']
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Check if passwords match
        if request.form['password'] != request.form['confirm_password']:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('forgot_password'))

        # Hash the new password
        hashed_password = generate_password_hash(new_password, method='sha256')

        # Check if the provided username or email exists in the database
        cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username_email, username_email))
        user = cursor.fetchone()

        if user:
            # Update the user's password
            cursor.execute("UPDATE users SET password=? WHERE id=?", (hashed_password, user[0]))
            connection.commit()

            flash("Password updated successfully! You can now log in with your new password.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid username or email.", "danger")
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

form_data = []

@app.route('/submit-form', methods=['POST'])
def submit_form():
    data = {
        'first': request.form['first'],
        'last': request.form['last'],
        'email': request.form['email'],
        'message': request.form['message']
    }
    form_data.append(data)
    return redirect(url_for('display_data'))

@app.route('/display-data')
def display_data():
    return render_template('display_data.html', form_data=form_data)


@app.route('/add_criminal', methods=['POST'])
@login_required
def add_criminal():
    connection, cursor = get_db()
    name = request.form['name']
    age = request.form['age']
    blood_group = request.form['blood_group']
    crime = request.form['crime']
    area_of_crime = request.form['area_of_crime']
    state_of_crime = request.form['state_of_crime']
    status = request.form['status']
    
    cursor.execute("INSERT INTO records(name, age, blood_group, crime, area_of_crime, state_of_crime, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
           (name, age, blood_group, crime, area_of_crime, state_of_crime, status))
    connection.commit()
    flash("Record added successfully!", "success")
    
    return redirect(url_for('index'))

@app.route('/search_criminal', methods=['POST'])
@login_required
def search_criminal():
    connection, cursor = get_db()
    search_by = request.form['search_by']
    search_input = request.form['search_input']

    query = f"SELECT * FROM records WHERE {search_by} LIKE ?"
    cursor.execute(query, ('%' + search_input + '%',))
    records = cursor.fetchall()
    
    if records:
        flash("Search results:", "info")
        for record in records:
            flash(str(record), "info")
    else:
        flash("No records found matching the search criteria.", "warning")
        
    return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
@login_required
def update():
    connection, cursor = get_db()
    criminal_id = int(request.form['update_id'])
    name = request.form['update_name']
    age = request.form['update_age']
    blood_group = request.form['update_blood_group']
    crime = request.form['update_crime']
    area_of_crime = request.form['update_area']
    state_of_crime = request.form['update_state']
    status = request.form['update_status']
    
    cursor.execute("SELECT * FROM records WHERE id=?", (criminal_id,))
    existing_record = cursor.fetchone()
    if existing_record is None:
        flash("Error: Criminal ID not found.", "danger")
        return redirect(url_for('index'))
    
    set_values = []
    bind_values = []
    if name:
        set_values.append("name=?")
        bind_values.append(name)
    if age:
        set_values.append("age=?")
        bind_values.append(age)
    if blood_group:
        set_values.append("blood_group=?")
        bind_values.append(blood_group)
    if crime:
        set_values.append("crime=?")
        bind_values.append(crime)
    if area_of_crime:
        set_values.append("area_of_crime=?")
        bind_values.append(area_of_crime)
    if state_of_crime:
        set_values.append("state_of_crime=?")
        bind_values.append(state_of_crime)
    if status:
        set_values.append("status=?")
        bind_values.append(status)
    
    set_clause = ", ".join(set_values)
    
    query = "UPDATE records SET {} WHERE id=?".format(set_clause)
    
    try:
        bind_values.append(criminal_id)  
        cursor.execute(query, tuple(bind_values))  
        connection.commit()
        flash("Criminal record updated successfully!", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for('index'))

@app.route('/delete_criminal', methods=['POST'])
@login_required
def delete_criminal():
    connection, cursor = get_db()
    delete_by = request.form['delete_by']
    delete_input = request.form['delete_input']
    
    query = f"DELETE FROM records WHERE {delete_by} LIKE ?"
    cursor.execute(query, ('%' + delete_input + '%',))
    
    if cursor.rowcount == 0:
        flash("Error: No matching records found for deletion.", "danger")
    else:
        flash("Record deleted successfully!", "success")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Use a single-threaded Flask server to avoid SQLite threading issues
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(debug=True, threaded=False)