from flask import Flask, render_template, request
from pymysql import connections
import os
import random
import argparse
import requests

app = Flask(__name__)

# --- CONFIGURATION FROM ENV VARIABLES ---
DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER") or "root"
DBPWD = os.environ.get("DBPWD") or "password"
DATABASE = os.environ.get("DATABASE") or "employees"
COLOR_FROM_ENV = os.environ.get('APP_COLOR') or "lime"
DBPORT = int(os.environ.get("DBPORT") or "3306")

BACKGROUND_IMAGE_URL = os.environ.get("BACKGROUND_IMAGE_URL")
MY_NAME = os.environ.get("MY_NAME") or "Group - 6 CLO-835"

# --- DATABASE CONNECTION (Initial global attempt) ---
# We make this a global variable, but we will wrap its use in a check.
db_conn = None 

# --- CONNECTION HELPER FUNCTION ---
def get_db_connection():
    """Checks if the global connection is alive and reconnects if it's broken."""
    global db_conn
    try:
        # Check if connection is None or if the connection is closed
        if db_conn is None or not db_conn.ping(reconnect=True):
            print("Attempting to reconnect to database...")
            db_conn = connections.Connection(
                host= DBHOST,
                port=DBPORT,
                user= DBUSER,
                password= DBPWD, 
                database= DATABASE
            )
            print("Database connection re-established.")
            # Run table initialization after reconnection to ensure table exists
            init_db()
        return db_conn
    except Exception as e:
        print(f"FATAL: Could not establish database connection: {e}")
        return None

# --- INITIALIZATION FUNCTIONS ---
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
            print(f"Error downloading image: {e}")

# Function to auto-create the table (fixes ProgrammingError)
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
    conn = get_db_connection() # Use the helper function to get connection
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(create_table_sql)
            conn.commit()
            print("Database table checked/created successfully.")
        except Exception as e:
            print(f"Error during DB init: {e}")
        finally:
            cursor.close()

# --- ROUTES (Modified to use get_db_connection()) ---
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('addemp.html', my_name=MY_NAME) # Removed color for simplification

@app.route("/about", methods=['GET','POST'])
def about():
    return render_template('about.html', my_name=MY_NAME)
    
@app.route("/addemp", methods=['POST'])
def AddEmp():
    conn = get_db_connection() # CRITICAL: Get connection here
    if conn is None:
        return "Database Unavailable", 503
        
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = conn.cursor()
    try:
        cursor.execute(insert_sql,(emp_id, first_name, last_name, primary_skill, location))
        conn.commit()
        emp_name = "" + first_name + " " + last_name
    finally:
        cursor.close()
    return render_template('addempoutput.html', name=emp_name, my_name=MY_NAME)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("getemp.html", my_name=MY_NAME)

@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    conn = get_db_connection() # CRITICAL: Get connection here
    if conn is None:
        return "Database Unavailable", 503
        
    emp_id = request.form['emp_id']
    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
    
    cursor = conn.cursor()
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
        print(f"Error fetching data: {e}")
    finally:
        cursor.close()
    return render_template("getempoutput.html", id=output.get("emp_id"), fname=output.get("first_name"),
                           lname=output.get("last_name"), interest=output.get("primary_skills"), location=output.get("location"), my_name=MY_NAME)

if __name__ == '__main__':
    download_background_image()
    # Initial connection attempt and table creation
    get_db_connection() 
    app.run(host='0.0.0.0',port=81,debug=True)
