from flask import Flask, render_template, request
from pymysql import connections
import os
import random
import argparse
import requests

app = Flask(__name__)

# --- CONFIGURATION FROM ENV VARIABLES ---
# We retrieve these values from the OS environment.
# This allows Kubernetes to inject them at runtime.
DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER") or "root"
DBPWD = os.environ.get("DBPWD") or "password"
DATABASE = os.environ.get("DATABASE") or "employees"
COLOR_FROM_ENV = os.environ.get("APP_COLOR") or "lime"
DBPORT = int(os.environ.get("DBPORT") or "3306")

# This will hold the URL for the background image to download
BACKGROUND_IMAGE_URL = os.environ.get("BACKGROUND_IMAGE_URL")
MY_NAME = os.environ.get("MY_NAME") or "Group - 6 CLO-835"

# --- DATABASE CONNECTION ---
# db_conn = connections.Connection(
#     host=DBHOST,
#     port=DBPORT,
#     user=DBUSER,
#     password=DBPWD,
#     database=DATABASE,  # This is the correct, non-deprecated name
# )
db_conn = None # Set db_conn to None so the code can proceed
output = {}
table = "employee"

# --- COLOR LOGIC ---
color_codes = {
    "red": "#e74c3c",
    "green": "#16a085",
    "blue": "#89CFF0",
    "blue2": "#30336b",
    "pink": "#f4c2c2",
    "darkblue": "#130f40",
    "lime": "#C1FF9C",
}
SUPPORTED_COLORS = ",".join(color_codes.keys())
COLOR = random.choice(["red", "green", "blue", "blue2", "darkblue", "pink", "lime"])


# --- NEW FUNCTION: Download Background Image ---
def download_background_image():
    """
    Downloads the image from the URL provided in env var and saves it to static/background.jpg
    """
    if BACKGROUND_IMAGE_URL:
        print(f"Downloading background image from: {BACKGROUND_IMAGE_URL}")
        try:
            # Create static directory if it doesn't exist
            if not os.path.exists("static"):
                os.makedirs("static")

            response = requests.get(BACKGROUND_IMAGE_URL)
            if response.status_code == 200:
                with open("static/background.jpg", "wb") as f:
                    f.write(response.content)
                print("Image downloaded successfully.")
            else:
                print(f"Failed to download image. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error downloading image: {e}")
    else:
        print("No BACKGROUND_IMAGE_URL environment variable set.")


# --- ROUTES ---
@app.route("/", methods=["GET", "POST"])
def home():
    # We pass MY_NAME to the HTML template so it renders in the header
    return render_template("addemp.html", color=color_codes[COLOR], my_name=MY_NAME)


@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html", color=color_codes[COLOR], my_name=MY_NAME)


@app.route("/fetchdata", methods=["GET", "POST"])
def FetchData():
    emp_id = request.form["emp_id"]

    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee from employee where emp_id=%s"
    
    # NEW: Implement the check to bypass DB logic if connection is disabled
    if db_conn:
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (emp_id))
            result = cursor.fetchone()
            
            output["emp_id"] = result[0]
            output["first_name"] = result[1]
            output["last_name"] = result[2]
            output["primary_skills"] = result[3]
            output["location"] = result[4]

        except Exception as e:
            print(e)

        finally:
            cursor.close()
            
    else:
        # Placeholder data for local testing when DB is disabled
        output["emp_id"] = emp_id
        output["first_name"] = "Placeholder"
        output["last_name"] = "User"
        output["primary_skills"] = "Cloud Architecture"
        output["location"] = "EKS Cluster"


    return render_template(
        "getempoutput.html",
        id=output["emp_id"],
        fname=output["first_name"],
        lname=output["last_name"],
        interest=output["primary_skills"],
        location=output["location"],
        color=color_codes[COLOR],
        my_name=MY_NAME,
    )

@app.route("/getemp", methods=["GET", "POST"])
def GetEmp():
    return render_template("getemp.html", color=color_codes[COLOR], my_name=MY_NAME)


if __name__ == "__main__":

    # 1. Trigger the image download immediately on startup
    download_background_image()

    # Command line argument logic (Preserving original logic)
    parser = argparse.ArgumentParser()
    parser.add_argument("--color", required=False)
    args = parser.parse_args()

    if args.color:
        print("Color from command line argument =" + args.color)
        COLOR = args.color
        if COLOR_FROM_ENV:
            print(
                "A color was set through environment variable -"
                + COLOR_FROM_ENV
                + ". However, color from command line argument takes precendence."
            )
    elif COLOR_FROM_ENV:
        print(
            "No Command line argument. Color from environment variable ="
            + COLOR_FROM_ENV
        )
        COLOR = COLOR_FROM_ENV
    else:
        print(
            "No command line argument or environment variable. Picking a Random Color ="
            + COLOR
        )

    if COLOR not in color_codes:
        print(
            "Color not supported. Received '"
            + COLOR
            + "' expected one of "
            + SUPPORTED_COLORS
        )
        exit(1)

    # 2. RUN ON PORT 81 (Required by Instructions)
    app.run(host="0.0.0.0", port=81, debug=True)
