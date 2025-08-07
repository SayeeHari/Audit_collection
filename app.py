from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import timedelta
import os
import pandas as pd
import json

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, 'file.json')

USERS_FILE = 'users.json'

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(minutes=10)

UPLOAD_FOLDER = 'uploads'
EXCEL_FILE = 'data.xlsx'
ALLOWED_EXTENSIONS = {'pdf', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user(email, username, password):
    users = load_users()
    print("Before saving:", users)
    users[email] = {
        "username": username,
        "password": password}
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
    print("After saving:", users)



@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        if not all([email, username, password]):
            return render_template('register.html', error='All fields are required')
        save_user(email, username, password)
        return redirect(url_for('login'))
    return render_template('register.html')

def allowed_file(filename, filetype):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS and \
           filename.lower().endswith(filetype)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            return render_template('login.html', error='Email and Password required')
        users = load_users()
        if email in users and users[email]['password']== password:
            session['user'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        print("POST request received on /index")
        org_name = request.form['org_name']
        audit_date = request.form['audit_date']
        asset_type = request.form['asset_type']
        auditor_name = request.form['auditor_name']
        location = request.form['location']
        standard = request.form['standard']
        excel_file = request.files['excel_file']
        pdf_file = request.files['pdf_file']

        print("Form Values collected")
        excel_file = request.files.get('excel_file')
        pdf_file = request.files.get('pdf_file')

        if not excel_file or not allowed_file(excel_file.filename, 'xlsx'):
            print("❌ Invalid or missing Excel file")
            return "Invalid Excel file."

        if not pdf_file or not allowed_file(pdf_file.filename, 'pdf'):
            print("❌ Invalid or missing PDF file")
            return "Invalid PDF file."

        excel_filename = secure_filename(excel_file.filename)
        pdf_filename = secure_filename(pdf_file.filename)

        if not allowed_file(excel_filename, 'xlsx') or not allowed_file(pdf_filename, 'pdf'):
            return "Invalid file format. Upload Excel (.xlsx) and PDF (.pdf) only."

        # Save uploaded files
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

        excel_file.save(excel_path)
        pdf_file.save(pdf_path)

        print("Files saved to:", excel_path, pdf_path)

       
        new_row = {
            "Organization Name": org_name,
            "Audit Date": audit_date,
            "Asset Type": asset_type,
            "Auditor Name": auditor_name,
            "Location": location,
            "Standard": standard,
            "Excel File": excel_filename,
            "PDF File": pdf_filename
        }

       
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_excel(EXCEL_FILE, index=False)
        print("Excel file updated")

        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                try:
                    json_data = json.load(f)
                except json.JSONDecodeError:
                    json_data = []
        else:
            json_data = []

        print("New row to be saved:", new_row)
        print("Existing JSON data before append:", json_data)
        print("SAving to Excel file:",EXCEL_FILE)

        json_data.append(new_row)

        with open(JSON_FILE, 'w') as f:
            json.dump(json_data, f, indent=4)
        print("JSON file updated")


        return render_template('success.html')


    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('register'))

@app.route('/success')
def success():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('success.html')

@app.route('/view_report')
def view_report():
    if 'user' not in session:
        return redirect(url_for('login'))

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            try:
                json_data = json.load(f)
                if json_data:
                    last_row = json_data[-1]
                else:
                    last_row = {}
            except json.JSONDecodeError:
                last_row = {}
    else:
        last_row = {}

    return render_template('report.html', record=last_row)




print("Running Flask app...")

if __name__ == '__main__':
    app.run(debug=True)

