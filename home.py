from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
import os

app = Flask(__name__)

# Secret key
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Path to the database file
DB_FILE = os.path.join(os.path.dirname(__file__), 'criminal_records.db')

# Database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.before_first_request
def initialize_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        age INTEGER,
                        blood_group TEXT,
                        crime TEXT,
                        area_of_crime TEXT,
                        state_of_crime TEXT,
                        status TEXT)""")
    db.commit()

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM records")
    records = cursor.fetchall()
    return render_template('info.html', records=records)

@app.route('/quick_search', methods=['POST'])
def quick_search():
    if request.method == 'POST':
        location = request.form['location']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM records WHERE area_of_crime LIKE ? OR state_of_crime LIKE ?", ('%' + location + '%', '%' + location + '%'))
        records = cursor.fetchall()
        if records:
            flash("Search results:", "info")
        else:
            flash("No records found matching the search criteria.", "warning")
        return render_template('info.html', records=records)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
