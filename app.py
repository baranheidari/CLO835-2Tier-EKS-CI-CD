from flask import Flask, render_template, request
from pymysql import connections
import os
import random
import argparse
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER") or "root"
DBPWD = os.environ.get("DBPWD") or "password"
DATABASE = os.environ.get("DATABASE") or "employees"
COLOR_FROM_ENV = os.environ.get('APP_COLOR') or "lime"
DBPORT = int(os.environ.get("DBPORT") or "3306")

BACKGROUND_IMAGE_URL = os.environ.get("BACKGROUND_IMAGE_URL")
MY_NAME = os.environ.get("MY_NAME") or "Group - 6 CLO-835"

# --- DATABASE CONNECTION ---
db_conn = connections.Connection(
    host= DBHOST,
    port=DBPORT,
    user= DBUSER,
    password= DBPWD, 
    database= DATABASE
)
output = {}
table = 'employee';

color_codes = {
    "red": "#e74c3c", "green": "#16a085", "blue": "#89CFF0", "blue2": "#30336b",
    "pink": "#f4c2c2", "darkblue": "#130f40", "lime": "#C1FF9C",
}
SUPPORTED_COLORS = ",".join(color_codes.keys())
COLOR = random.choice(["red", "green", "blue", "blue2", "darkblue", "pink", "lime"])

def download_background_image():
    if BACKGROUND_IMAGE_URL:
        print(f"Downloading background image from: {BACKGROUND_IMAGE_URL}")
        try:
            if not os.path.exists('static'):
                os.makedirs('static')
            response = requests.get(BACKGROUND_IMAGE_URL)
            if response.status_code == 200:
                with open('static/background.jpg', 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Error: {e}")

# --- NEW: FUNCTION TO CREATE TABLE ---
def init_db():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS employee (
        emp_id VARCHAR(20),
        first_name VARCHAR(20),
        last_name VARCHAR(20),
        primary_skill VARCHAR(20),
        location VARCHAR(20)
    )
    """
    cursor = db_conn.cursor()
    try:
        cursor.execute(create_table_sql)
        db_conn.commit()
        print("Database table checked/created successfully.")
    finally:
        cursor.close()

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('addemp.html', color=color_codes[COLOR], my_name=MY_NAME)

@app.route("/about", methods=['GET','POST'])
def about():
    return render_template('about.html', color=color_codes[COLOR], my_name=MY_NAME)
    
@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    try:
        cursor.execute(insert_sql,(emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
    finally:
        cursor.close()
    return render_template('addempoutput.html', name=emp_name, color=color_codes[COLOR], my_name=MY_NAME)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("getemp.html", color=color_codes[COLOR], my_name=MY_NAME)

@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']
    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
    cursor = db_conn.cursor()
    try:
        cursor.execute(select_sql,(emp_id))
        result = cursor.fetchone()
        if result:
            output["emp_id"] = result[0]
            output["first_name"] = result[1]
            output["last_name"] = result[2]
            output["primary_skills"] = result[3]
            output["location"] = result[4]
    except Exception as e:
        print(e)
    finally:
        cursor.close()
    return render_template("getempoutput.html", id=output.get("emp_id"), fname=output.get("first_name"),
                           lname=output.get("last_name"), interest=output.get("primary_skills"), location=output.get("location"), color=color_codes[COLOR], my_name=MY_NAME)

if __name__ == '__main__':
    download_background_image()
    init_db() # <--- Run the table creation logic on startup
    app.run(host='0.0.0.0',port=81,debug=True)

