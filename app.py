from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.serving import WSGIRequestHandler
import sqlite3



connection = None
cursor = None

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
        connection.commit()
    return connection, cursor

@app.route('/')
def index():
    connection, cursor = get_db()
    cursor.execute("SELECT * FROM records")
    records = cursor.fetchall()
    return render_template('info.html', records=records)

@app.route('/add_criminal', methods=['POST'])
def add_criminal():
    if request.method == 'POST':
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
def search_criminal():
    if request.method == 'POST':
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
def update():
    if request.method == 'POST':
        connection, cursor = get_db()
        criminal_id = int(request.form['update_id'])
        name = request.form['update_name']
        age = request.form['update_age']
        blood_group = request.form['update_blood_group']
        crime = request.form['update_crime']
        location = request.form['update_location']
        status = request.form['update_status']
        
        # Create the SET part of the SQL query dynamically based on the provided values
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
        if location:
            set_values.append("area_of_crime=?")
            bind_values.append(location)
        if status:
            set_values.append("status=?")
            bind_values.append(status)
        
        # Construct the SET clause for the SQL query
        set_clause = ", ".join(set_values)
        
        # Construct the SQL query
        query = "UPDATE records SET {} WHERE id=?".format(set_clause)
        
        # Execute the query and commit changes
        try:
            bind_values.append(criminal_id)  # Add criminal_id to the bind_values
            cursor.execute(query, tuple(bind_values))  # Convert bind_values to tuple
            connection.commit()
            flash("Criminal record updated successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")

        return redirect(url_for('index'))


@app.route('/delete_criminal', methods=['POST'])
def delete_criminal():
    if request.method == 'POST':
        connection, cursor = get_db()
        delete_by = request.form['delete_by']
        delete_input = request.form['delete_input']
        
        query = f"DELETE FROM records WHERE {delete_by} LIKE ?"
        cursor.execute(query, ('%' + delete_input + '%',))
        
        flash("Record deleted successfully!", "success")
        
        return redirect(url_for('index'))