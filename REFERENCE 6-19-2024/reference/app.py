import numpy as np
import io
import csv
import base64
from flask import Flask, request, render_template, redirect, session, url_for
import pyodbc
import bcrypt
import random
import string
import math
from flask import jsonify
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'secret_key'

# SQL Server Config

def connection():
    s = 'DESKTOP-D02M258\SQLEXPRESS' #Your server name 
    d = 'Ujsurvey' 
    u = 'Jbs' #Your login
    p = 'Password@123' #Your login password
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p
    conn = pyodbc.connect(cstr)
    return conn


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
mail = Mail(app)

@app.route("/administrator")
def main():
    cars = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dbo.Questions")
    for row in cursor.fetchall():
        cars.append({"Survey_ID": row[0], "Question_Index": row[1], "Question_Text": row[2], "Next_QuestionIndex": row[3]})
    conn.close()
    return render_template("administrator.html", cars = cars)



class User:
    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode(
            'utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))



def create_user_table():
    connection = sqlite3.connect('cwttdatabase.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            userPhoto BLOB,
            is_active BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    connection.commit()
    connection.close()


create_user_table()


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        user_photo = request.files['user_photo']

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        connection = sqlite3.connect('cwttdatabase.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            connection.close()
            return render_template('register.html', error='User with this email already exists')

        hashed_password = bcrypt.hashpw(password.encode(
            'utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Read the photo data and convert it to binary
        user_photo_data = user_photo.read()

        cursor.execute('INSERT INTO User (name, email, password, userPhoto, is_active) VALUES (?, ?, ?, ?, ?)',
                       (name, email, hashed_password, user_photo_data, False))
        connection.commit()
        connection.close()

        return render_template('register.html', message='Registration successful! Please wait until your account is activated by an administrator.')

    return render_template('register.html')


Administrators = {
    'admin1@gmail.com': bcrypt.hashpw('admin1'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
    'admin2@gmail.com': bcrypt.hashpw('admin2'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
    'admin3@gmail.com': bcrypt.hashpw('admin3'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the user is an administrator
        if email in Administrators and bcrypt.checkpw(password.encode('utf-8'), Administrators[email].encode('utf-8')):
            session['email'] = email
            return redirect('/administrator')

        connection = sqlite3.connect('cwttdatabase.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            if user[5]:  # Check if the user account is active
                session['email'] = user[2]
                return redirect('/userAccount')
            else:
                error_message = "Your account is not yet activated. Please wait until an administrator activates your account."
                return render_template('login.html', error=error_message)
        else:
            error_message = "Invalid credentials. Please make sure to enter the correct email and password."
            return render_template('login.html', error=error_message)

    return render_template('login.html')


@app.route('/administrator')
def dashboardAdministrator():
    if session.get('email'):
        connection = sqlite3.connect('cwttdatabase.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (session['email'],))
        user = cursor.fetchone()
        connection.close()
        return render_template('administrator.html', user=user)

    return redirect('/login')


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['newpassword']
        confirm_new_password = request.form['confnewpassword']

        if new_password != confirm_new_password:
            return render_template('forgotpassword.html', error='Passwords do not match')

        connection = sqlite3.connect('cwttdatabase.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (email,))
        user = cursor.fetchone()

        if user:
            hashed_password = bcrypt.hashpw(new_password.encode(
                'utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('UPDATE User SET password=? WHERE email=?', (hashed_password, email))
            connection.commit()
            connection.close()
            return redirect('/login')
        else:
            connection.close()
            return render_template('forgotpassword.html', error='No user found with that email')

    return render_template('forgotpassword.html')


@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if session.get('email'):
        connection = sqlite3.connect('cwttdatabase.db')
        cursor = connection.cursor()
        cursor.execute('SELECT id, name, email, is_active FROM User')
        registered_users = cursor.fetchall()
        connection.close()
        return render_template('administrator.html', registered_users=registered_users)
    return redirect('/login')


@app.route('/activate_deactivate_user', methods=['GET', 'POST'])
def activate_deactivate_user():
    if session.get('email'):
        connection = sqlite3.connect('cwttdatabase.db')
        cursor = connection.cursor()

        if request.method == 'POST':
            record_id = request.form['record_id']
            action = request.form['action']

            print(f"Record ID: {record_id}, Action: {action}")  # Debugging statement

            if action == 'activate':
                cursor.execute('UPDATE User SET is_active = 1 WHERE id = ?', (record_id,))
                connection.commit()
                cursor.execute('SELECT email FROM User WHERE id = ?', (record_id,))
                user_email = cursor.fetchone()
                if user_email:
                    send_activation_email(user_email[0])
                else:
                    print(f"No user found with ID: {record_id}")  # Debugging statement
            elif action == 'deactivate':
                cursor.execute('DELETE FROM User WHERE id = ?', (record_id,))
                connection.commit()

        cursor.execute('SELECT id, name, email, is_active FROM User')
        registered_users = cursor.fetchall()
        connection.close()
        return render_template('administrator.html', registered_users=registered_users)
    return redirect('/login')


def send_activation_email(to_email):
    msg = Message('ACCOUNT ACTIVATION', sender='your_email@gmail.com', recipients=[to_email])
    msg.body = 'Your account has been activated. You can now use your credentials to login.'
    mail.send(msg)


if __name__ == '__main__':
    app.run(debug=True)
