# =========================================================
# CROP YIELD AI - FLASK APPLICATION
# =========================================================
# Roles:
#   1. Admin
#   2. Farmer
#
# Features:
#   - Login / Register
#   - Farmer Dashboard
#   - Normal Crop Yield Prediction
#   - AI Crop Yield Prediction
#   - Prediction History
#   - Analytics
#   - Solutions Page
#   - Live Crop Information
#   - Live Weather
#   - YouTube Crop Videos
#   - Agriculture News
#   - Location Search
#   - Dataset Auto Reload
#   - Admin Dashboard
# =========================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

import sqlite3
import os
import joblib
import pandas as pd
import requests
import feedparser
import html

from functools import wraps
from datetime import datetime


from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = "crop_yield_ai_secret_key_2026"


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# PATHS
# =========================================================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "best_model.pkl"
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "data",
    "combined_crop_yield.csv"
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "users.db"
)


# =========================================================
# API SETTINGS
# =========================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org"
)

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

GOOGLE_NEWS_RSS_URL = (
    "https://news.google.com/rss/search"
)

YOUTUBE_SEARCH_URL = (
    "https://www.youtube.com/results"
)


# =========================================================
# GLOBAL DATASET VARIABLES
# =========================================================

df = None

dataset_modified_time = None


# =========================================================
# LOAD DATASET
# =========================================================

def load_dataset(force=False):

    global df
    global dataset_modified_time

    if not os.path.exists(DATASET_PATH):

        raise FileNotFoundError(
            "\nDataset not found:\n"
            + DATASET_PATH
            + "\n\n"
            "Please place combined_crop_yield.csv "
            "inside the data folder."
        )

    current_modified_time = os.path.getmtime(
        DATASET_PATH
    )

    # -----------------------------------------------------
    # Do not reload if file has not changed
    # -----------------------------------------------------

    if (
        not force
        and df is not None
        and dataset_modified_time
        == current_modified_time
    ):

        return df

    print("=" * 70)
    print("Loading Crop Yield Dataset...")
    print("=" * 70)

    try:

        new_df = pd.read_csv(
            DATASET_PATH
        )

        new_df.columns = (
            new_df.columns
            .astype(str)
            .str.strip()
            .str.lower()
        )

        df = new_df

        dataset_modified_time = (
            current_modified_time
        )

        print(
            "Dataset loaded successfully."
        )

        print(
            "Dataset shape:",
            df.shape
        )

        print(
            "Dataset columns:",
            df.columns.tolist()
        )

        return df

    except Exception as e:

        print(
            "Dataset loading error:",
            e
        )

        raise RuntimeError(
            "Unable to load dataset:\n"
            + str(e)
        )


# =========================================================
# CHECK MODEL
# =========================================================

if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        "\nModel not found:\n"
        + MODEL_PATH
        + "\n\n"
        "Please run train_model.py first."
    )


# =========================================================
# LOAD MODEL
# =========================================================

print("=" * 70)
print("Loading Crop Yield AI model...")
print("=" * 70)

try:

    model = joblib.load(
        MODEL_PATH
    )

    print(
        "Model loaded successfully."
    )

except Exception as e:

    raise RuntimeError(
        "Unable to load model:\n"
        + str(e)
    )


# =========================================================
# INITIAL DATASET LOAD
# =========================================================

load_dataset()


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db()

    cursor = conn.cursor()

    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL

        )
        """
    )

    # -----------------------------------------------------
    # PREDICTIONS TABLE
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL,

            state TEXT,

            district TEXT,

            location TEXT,

            latitude REAL,

            longitude REAL,

            crop TEXT,

            season TEXT,

            year REAL,

            month REAL,

            area REAL,

            rainfall_mm REAL,

            temperature_c REAL,

            humidity_percent REAL,

            soil_moisture_percent REAL,

            soil_ph REAL,

            prediction REAL,

            estimated_production REAL,

            prediction_type TEXT DEFAULT 'normal',

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    # -----------------------------------------------------
    # DEFAULT ADMIN
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        ("admin",)
    )

    admin = cursor.fetchone()

    if admin is None:

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                "admin",
                generate_password_hash(
                    "admin123"
                ),
                "admin"
            )
        )

    conn.commit()

    conn.close()


# =========================================================
# DATABASE MIGRATION
# =========================================================

def add_database_columns():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "PRAGMA table_info(predictions)"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    required_columns = {

        "location": "TEXT",

        "latitude": "REAL",

        "longitude": "REAL",

        "prediction_type": "TEXT"

    }

    for column, datatype in (
        required_columns.items()
    ):

        if column not in columns:

            cursor.execute(
                f"""
                ALTER TABLE predictions
                ADD COLUMN {column}
                {datatype}
                """
            )

            print(
                f"Added database column: {column}"
            )

    conn.commit()

    conn.close()


# =========================================================
# DATABASE SETUP
# =========================================================

init_db()

add_database_columns()


# =========================================================
# REMOVE GOVERNMENT USER
# =========================================================

def remove_government_user():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM users
        WHERE
            (
                username = ?
                OR username = ?
            )
            AND
            (
                role = ?
                OR role = ?
            )
        """,
        (
            "govt",
            "government",
            "govt",
            "government"
        )
    )

    conn.commit()

    conn.close()


remove_government_user()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)
    def decorated_function(
        *args,
        **kwargs
    ):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return decorated_function


# =========================================================
# ROLE REQUIRED
# =========================================================

def role_required(required_role):

    def decorator(function):

        @wraps(function)
        def decorated_function(
            *args,
            **kwargs
        ):

            if "user_id" not in session:

                return redirect(
                    url_for("login")
                )

            if session.get("role") != required_role:

                return redirect(
                    url_for("dashboard")
                )

            return function(
                *args,
                **kwargs
            )

        return decorated_function

    return decorator


# =========================================================
# UNIQUE DATA
# =========================================================

def get_unique_values(column):

    current_df = load_dataset()

    if column not in current_df.columns:

        return []

    values = (
        current_df[column]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )

    return sorted(values)


# =========================================================
# YEARS
# =========================================================

def get_years():

    current_df = load_dataset()

    years = []

    if "year" in current_df.columns:

        numeric_years = (
            pd.to_numeric(
                current_df["year"],
                errors="coerce"
            )
            .dropna()
        )

        years = (
            numeric_years
            .astype(int)
            .unique()
            .tolist()
        )

    if 2026 not in years:

        years.append(2026)

    return sorted(
        set(years)
    )


# =========================================================
# DROPDOWN DATA
# =========================================================

def get_dropdown_data():

    states = get_unique_values(
        "state"
    )

    districts = get_unique_values(
        "district"
    )

    crops = get_unique_values(
        "crop"
    )

    seasons = get_unique_values(
        "season"
    )

    years = get_years()

    return (
        states,
        districts,
        crops,
        seasons,
        years
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter username and password."
            )

            return render_template(
                "login.html"
            )

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                username,
                password,
                role
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user is not None:

            if user["role"] not in (
                "admin",
                "farmer"
            ):

                flash(
                    "This account type is not allowed."
                )

                return render_template(
                    "login.html"
                )

            if check_password_hash(
                user["password"],
                password
            ):

                session.clear()

                session["user_id"] = (
                    user["id"]
                )

                session["username"] = (
                    user["username"]
                )

                session["role"] = (
                    user["role"]
                )

                return redirect(
                    url_for("dashboard")
                )

        flash(
            "Invalid username or password."
        )

    return render_template(
        "login.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not username:

            flash(
                "Username is required."
            )

            return render_template(
                "register.html"
            )

        if len(username) < 3:

            flash(
                "Username must contain at least 3 characters."
            )

            return render_template(
                "register.html"
            )

        if not password:

            flash(
                "Password is required."
            )

            return render_template(
                "register.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters."
            )

            return render_template(
                "register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match."
            )

            return render_template(
                "register.html"
            )

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        existing_user = (
            cursor.fetchone()
        )

        if existing_user:

            conn.close()

            flash(
                "Username already exists."
            )

            return render_template(
                "register.html"
            )

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                generate_password_hash(
                    password
                ),
                "farmer"
            )
        )

        conn.commit()

        conn.close()

        flash(
            "Registration successful. You can now login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# DASHBOARD ROUTER
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    role = session.get(
        "role"
    )

    if role == "admin":

        return redirect(
            url_for("admin_dashboard")
        )

    if role == "farmer":

        return redirect(
            url_for("farmer_dashboard")
        )

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# FARMER DASHBOARD
# =========================================================

@app.route("/farmer")
@role_required("farmer")
def farmer_dashboard():

    (
        states,
        districts,
        crops,
        seasons,
        years
    ) = get_dropdown_data()

    return render_template(
        "farmer_dashboard.html",

        username=session["username"],

        states=states,

        districts=districts,

        crops=crops,

        seasons=seasons,

        years=years
    )


# =========================================================
# SOLUTIONS PAGE
# =========================================================

@app.route(
    "/solutions",
    methods=["GET"]
)
@role_required("farmer")
def solutions():

    # -----------------------------------------------------
    # CURRENT CROP
    # -----------------------------------------------------

    crop = request.args.get(
        "crop",
        ""
    ).strip()

    # If no crop selected, use first dataset crop
    if not crop:

        crops = get_unique_values(
            "crop"
        )

        if crops:

            crop = crops[0]

        else:

            crop = "Rice"

    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    location = request.args.get(
        "location",
        ""
    ).strip()

    state = request.args.get(
        "state",
        ""
    ).strip()

    district = request.args.get(
        "district",
        ""
    ).strip()

    latitude_value = request.args.get(
        "latitude",
        ""
    ).strip()

    longitude_value = request.args.get(
        "longitude",
        ""
    ).strip()

    latitude = None
    longitude = None

    # -----------------------------------------------------
    # TRY COORDINATES
    # -----------------------------------------------------

    try:

        if latitude_value:

            latitude = float(
                latitude_value
            )

        if longitude_value:

            longitude = float(
                longitude_value
            )

    except ValueError:

        latitude = None
        longitude = None

    # -----------------------------------------------------
    # GEOCODE LOCATION
    # -----------------------------------------------------

    if (
        latitude is None
        or longitude is None
    ):

        if location:

            geo = geocode_location(
                location
            )

            if geo:

                latitude = geo[
                    "latitude"
                ]

                longitude = geo[
                    "longitude"
                ]

                if not state:

                    state = geo.get(
                        "state",
                        ""
                    )

                if not district:

                    district = geo.get(
                        "district",
                        ""
                    )

        # -------------------------------------------------
        # DEFAULT INDIA LOCATION
        # -------------------------------------------------

        if (
            latitude is None
            or longitude is None
        ):

            latitude = 20.5937

            longitude = 78.9629

            if not location:

                location = "India"

    # -----------------------------------------------------
    # WEATHER
    # -----------------------------------------------------

    weather = get_current_weather(
        latitude,
        longitude
    )

    # -----------------------------------------------------
    # HISTORICAL DATA
    # -----------------------------------------------------

    historical = get_historical_analysis(
        crop=crop,
        state=state,
        district=district
    )

    # -----------------------------------------------------
    # NEWS
    # -----------------------------------------------------

    news = get_agriculture_news(
        crop=crop,
        location=location
    )

    # -----------------------------------------------------
    # YOUTUBE VIDEOS
    # -----------------------------------------------------

    youtube_videos = get_youtube_videos(
        crop=crop,
        location=location
    )

    # -----------------------------------------------------
    # DATASET INFORMATION
    # -----------------------------------------------------

    current_df = load_dataset()

    dataset_records = len(
        current_df
    )

    dataset_crops = get_unique_values(
        "crop"
    )

    return render_template(

        "solutions.html",

        username=session[
            "username"
        ],

        crop=crop,

        location=location,

        state=state,

        district=district,

        latitude=latitude,

        longitude=longitude,

        weather=weather,

        historical=historical,

        news=news,

        youtube_videos=youtube_videos,

        dataset_records=dataset_records,

        dataset_crops=dataset_crops
    )


# =========================================================
# YOUTUBE CROP VIDEOS
# =========================================================

def get_youtube_videos(
    crop,
    location=""
):

    videos = []

    # -----------------------------------------------------
    # Search query
    # -----------------------------------------------------

    query = (
        f"{crop} farming "
        f"{location} India"
    ).strip()

    # -----------------------------------------------------
    # YouTube search page
    # -----------------------------------------------------

    search_url = (
        YOUTUBE_SEARCH_URL
        + "?search_query="
        + requests.utils.quote(query)
    )

    # -----------------------------------------------------
    # We provide reliable search links
    # rather than scraping YouTube.
    # -----------------------------------------------------

    videos.append({

        "title":
            f"{crop} Farming and Cultivation",

        "description":
            f"Latest YouTube videos about {crop} farming.",

        "link":
            search_url

    })

    videos.append({

        "title":
            f"{crop} Crop Growing Guide",

        "description":
            f"Learn modern techniques for growing {crop}.",

        "link":
            (
                YOUTUBE_SEARCH_URL
                + "?search_query="
                + requests.utils.quote(
                    f"{crop} cultivation farming"
                )
            )

    })

    videos.append({

        "title":
            f"{crop} Farming Latest Videos",

        "description":
            f"Latest videos and farming information for {crop}.",

        "link":
            (
                YOUTUBE_SEARCH_URL
                + "?search_query="
                + requests.utils.quote(
                    f"{crop} agriculture latest"
                )
            )

    })

    return videos


# =========================================================
# PREDICTION HISTORY
# =========================================================

@app.route("/history")
@role_required("farmer")
def history():

    history_data = []

    conn = None

    try:

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                state,
                district,
                location,
                crop,
                season,
                year,
                month,
                area,
                rainfall_mm,
                temperature_c,
                humidity_percent,
                soil_moisture_percent,
                soil_ph,
                prediction,
                estimated_production,
                prediction_type,
                created_at

            FROM predictions

            WHERE username = ?

            ORDER BY id DESC
            """,
            (
                session["username"],
            )
        )

        rows = cursor.fetchall()

        for row in rows:

            location = row[
                "location"
            ]

            if not location:

                location_parts = []

                if row["district"]:

                    location_parts.append(
                        str(
                            row["district"]
                        )
                    )

                if row["state"]:

                    location_parts.append(
                        str(
                            row["state"]
                        )
                    )

                location = ", ".join(
                    location_parts
                )

            if not location:

                location = "Not specified"

            prediction_type = (
                row["prediction_type"]
                or "normal"
            )

            prediction_type = str(
                prediction_type
            ).upper()

            history_data.append({

                "id":
                    row["id"],

                "date":
                    row["created_at"],

                "crop":
                    row["crop"]
                    or "Unknown",

                "location":
                    location,

                "area":
                    row["area"],

                "prediction":
                    row["prediction"],

                "estimated_production":
                    row[
                        "estimated_production"
                    ],

                "type":
                    prediction_type,

                "state":
                    row["state"]
                    or "",

                "district":
                    row["district"]
                    or "",

                "season":
                    row["season"]
                    or "",

                "year":
                    row["year"],

                "month":
                    row["month"],

                "rainfall":
                    row["rainfall_mm"],

                "temperature":
                    row["temperature_c"],

                "humidity":
                    row[
                        "humidity_percent"
                    ],

                "soil_moisture":
                    row[
                        "soil_moisture_percent"
                    ],

                "soil_ph":
                    row["soil_ph"]

            })

    except Exception as e:

        print(
            "History error:",
            e
        )

        flash(
            "Unable to load prediction history."
        )

    finally:

        if conn is not None:

            conn.close()

    return render_template(
        "history.html",

        username=session[
            "username"
        ],

        history=history_data
    )


# =========================================================
# HISTORY ALIAS
# =========================================================

@app.route("/farmer/history")
@role_required("farmer")
def farmer_history():

    return redirect(
        url_for("history")
    )

@app.route("/about")
def about():
    return render_template("farmer/about.html")
# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
@role_required("farmer")
def analytics():

    conn = get_db()

    cursor = conn.cursor()

    username = session[
        "username"
    ]

    cursor.execute(
        """
        SELECT
            crop,
            COUNT(*) AS count

        FROM predictions

        WHERE username = ?

        GROUP BY crop

        ORDER BY count DESC
        """,
        (username,)
    )

    crop_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            crop,
            AVG(prediction)
            AS avg_prediction

        FROM predictions

        WHERE username = ?

        GROUP BY crop

        ORDER BY avg_prediction DESC
        """,
        (username,)
    )

    avg_crop_rows = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT
            COALESCE(
                prediction_type,
                'normal'
            ) AS prediction_type,

            COUNT(*) AS count

        FROM predictions

        WHERE username = ?

        GROUP BY prediction_type

        ORDER BY count DESC
        """,
        (username,)
    )

    type_rows = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT
            year,
            COUNT(*) AS count

        FROM predictions

        WHERE username = ?

        GROUP BY year

        ORDER BY year
        """,
        (username,)
    )

    year_rows = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT
            rainfall_mm,
            prediction

        FROM predictions

        WHERE username = ?

        AND rainfall_mm IS NOT NULL

        AND prediction IS NOT NULL

        ORDER BY id
        """,
        (username,)
    )

    rainfall_rows = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT
            temperature_c,
            prediction

        FROM predictions

        WHERE username = ?

        AND temperature_c IS NOT NULL

        AND prediction IS NOT NULL

        ORDER BY id
        """,
        (username,)
    )

    temperature_rows = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM predictions

        WHERE username = ?
        """,
        (username,)
    )

    total_predictions = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        """
        SELECT AVG(prediction)

        FROM predictions

        WHERE username = ?
        """,
        (username,)
    )

    average_prediction = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        """
        SELECT MAX(prediction)

        FROM predictions

        WHERE username = ?
        """,
        (username,)
    )

    best_prediction = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        """
        SELECT SUM(
            estimated_production
        )

        FROM predictions

        WHERE username = ?
        """,
        (username,)
    )

    total_production = (
        cursor.fetchone()[0]
    )

    conn.close()

    crop_labels = [
        row["crop"] or "Unknown"
        for row in crop_rows
    ]

    crop_counts = [
        row["count"]
        for row in crop_rows
    ]

    avg_crop_labels = [
        row["crop"] or "Unknown"
        for row in avg_crop_rows
    ]

    avg_crop_values = [

        round(
            float(
                row["avg_prediction"]
                or 0
            ),
            4
        )

        for row in avg_crop_rows
    ]

    type_labels = [

        str(
            row[
                "prediction_type"
            ]
            or "normal"
        ).upper()

        for row in type_rows
    ]

    type_counts = [

        row["count"]

        for row in type_rows
    ]

    year_labels = []

    year_counts = []

    for row in year_rows:

        if row["year"] is not None:

            year_labels.append(
                str(
                    int(
                        float(
                            row["year"]
                        )
                    )
                )
            )

        else:

            year_labels.append(
                "Unknown"
            )

        year_counts.append(
            row["count"]
        )

    rainfall_values = [

        [
            float(
                row[
                    "rainfall_mm"
                ]
                or 0
            ),

            float(
                row[
                    "prediction"
                ]
                or 0
            )
        ]

        for row in rainfall_rows
    ]

    temperature_values = [

        [
            float(
                row[
                    "temperature_c"
                ]
                or 0
            ),

            float(
                row[
                    "prediction"
                ]
                or 0
            )
        ]

        for row in temperature_rows
    ]

    return render_template(

        "analytics.html",

        username=username,

        crop_labels=crop_labels,

        crop_counts=crop_counts,

        avg_crop_labels=avg_crop_labels,

        avg_crop_values=avg_crop_values,

        type_labels=type_labels,

        type_counts=type_counts,

        year_labels=year_labels,

        year_counts=year_counts,

        rainfall_values=rainfall_values,

        temperature_values=temperature_values,

        total_predictions=
            total_predictions,

        average_prediction=
            round(
                float(
                    average_prediction
                    or 0
                ),
                4
            ),

        best_prediction=
            round(
                float(
                    best_prediction
                    or 0
                ),
                4
            ),

        total_production=
            round(
                float(
                    total_production
                    or 0
                ),
                4
            )
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@role_required("admin")
def admin_dashboard():

    current_df = load_dataset()

    total_rows = len(
        current_df
    )

    total_states = (

        current_df[
            "state"
        ].dropna().nunique()

        if "state"
        in current_df.columns

        else 0

    )

    total_districts = (

        current_df[
            "district"
        ].dropna().nunique()

        if "district"
        in current_df.columns

        else 0

    )

    total_crops = (

        current_df[
            "crop"
        ].dropna().nunique()

        if "crop"
        in current_df.columns

        else 0

    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        "SELECT COUNT(*) FROM predictions"
    )

    total_predictions = (
        cursor.fetchone()[0]
    )

    conn.close()

    return render_template(

        "admin_dashboard.html",

        username=session[
            "username"
        ],

        total_rows=total_rows,

        total_states=total_states,

        total_districts=
            total_districts,

        total_crops=
            total_crops,

        total_users=
            total_users,

        total_predictions=
            total_predictions
    )


# =========================================================
# DATASET STATUS API
# =========================================================

@app.route(
    "/api/dataset-status"
)
@role_required("farmer")
def dataset_status():

    current_df = load_dataset()

    return jsonify({

        "success":
            True,

        "records":
            len(current_df),

        "crops":
            get_unique_values(
                "crop"
            ),

        "states":
            get_unique_values(
                "state"
            ),

        "districts":
            get_unique_values(
                "district"
            ),

        "last_updated":
            datetime.fromtimestamp(
                os.path.getmtime(
                    DATASET_PATH
                )
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    })


# =========================================================
# FORCE DATASET RELOAD
# =========================================================

@app.route(
    "/api/reload-dataset",
    methods=["POST"]
)
@role_required("admin")
def reload_dataset():

    try:

        load_dataset(
            force=True
        )

        return jsonify({

            "success":
                True,

            "message":
                "Dataset reloaded successfully.",

            "records":
                len(df)

        })

    except Exception as e:

        return jsonify({

            "success":
                False,

            "message":
                str(e)

        }), 500


# =========================================================
# MODEL FEATURES
# =========================================================

def get_model_features():

    try:

        if hasattr(
            model,
            "named_steps"
        ):

            if (
                "preprocessor"
                in model.named_steps
            ):

                preprocessor = (
                    model.named_steps[
                        "preprocessor"
                    ]
                )

                if hasattr(
                    preprocessor,
                    "feature_names_in_"
                ):

                    return list(
                        preprocessor
                        .feature_names_in_
                    )

            if hasattr(
                model,
                "feature_names_in_"
            ):

                return list(
                    model.feature_names_in_
                )

        if hasattr(
            model,
            "feature_names_in_"
        ):

            return list(
                model.feature_names_in_
            )

    except Exception as e:

        print(
            "Feature detection error:",
            e
        )

    return []


# =========================================================
# CREATE MODEL INPUT
# =========================================================

def create_prediction_dataframe(

    state,
    district,
    crop,
    season,
    year,
    month,
    area,
    rainfall,
    temperature,
    humidity,
    soil_moisture,
    soil_ph

):

    values = {

        "state":
            state,

        "district":
            district,

        "crop":
            crop,

        "season":
            season,

        "year":
            year,

        "month":
            month,

        "area":
            area,

        "rainfall_mm":
            rainfall,

        "temperature_c":
            temperature,

        "humidity_percent":
            humidity,

        "soil_moisture_percent":
            soil_moisture,

        "soil_ph":
            soil_ph

    }

    input_df = pd.DataFrame(
        [values]
    )

    training_features = (
        get_model_features()
    )

    if training_features:

        for column in training_features:

            if column not in input_df.columns:

                input_df[column] = 0

        input_df = input_df.reindex(
            columns=training_features
        )

    return input_df


# =========================================================
# NORMAL PREDICTION
# =========================================================

@app.route(
    "/predict",
    methods=["POST"]
)
@role_required("farmer")
def predict():

    state = request.form.get(
        "state",
        ""
    ).strip()

    district = request.form.get(
        "district",
        ""
    ).strip()

    crop = request.form.get(
        "crop",
        ""
    ).strip()

    season = request.form.get(
        "season",
        ""
    ).strip()

    year_value = request.form.get(
        "year",
        ""
    ).strip()

    month_value = request.form.get(
        "month",
        ""
    ).strip()

    area_value = request.form.get(
        "area",
        ""
    ).strip()

    rainfall_value = request.form.get(
        "rainfall_mm",
        "0"
    ).strip()

    temperature_value = request.form.get(
        "temperature_c",
        "0"
    ).strip()

    humidity_value = request.form.get(
        "humidity_percent",
        "0"
    ).strip()

    soil_moisture_value = request.form.get(
        "soil_moisture_percent",
        "0"
    ).strip()

    soil_ph_value = request.form.get(
        "soil_ph",
        "0"
    ).strip()

    if not state:

        flash(
            "Please select State."
        )

        return redirect(
            url_for(
                "farmer_dashboard"
            )
        )

    if not district:

        flash(
            "Please select District."
        )

        return redirect(
            url_for(
                "farmer_dashboard"
            )
        )

    if not crop:

        flash(
            "Please select Crop."
        )

        return redirect(
            url_for(
                "farmer_dashboard"
            )
        )

    if not season:

        flash(
            "Please select Season."
        )

        return redirect(
            url_for(
                "farmer_dashboard"
            )
        )

    try:

        year = float(
            year_value
        )

        month = float(
            month_value
        )

        area = float(
            area_value
        )

        rainfall = float(
            rainfall_value or 0
        )

        temperature = float(
            temperature_value or 0
        )

        humidity = float(
            humidity_value or 0
        )

        soil_moisture = float(
            soil_moisture_value or 0
        )

        soil_ph = float(
            soil_ph_value or 0
        )

    except ValueError:

        flash(
            "Please enter valid numeric values."
        )

        return redirect(
            url_for(
                "farmer_dashboard"
            )
        )

    if area <= 0:

        flash(
            "Area must be greater than zero."
        )

        return redirect(
            url_for(
                "farmer_dashboard"
            )
        )

    input_df = create_prediction_dataframe(

        state,
        district,
        crop,
        season,
        year,
        month,
        area,
        rainfall,
        temperature,
        humidity,
        soil_moisture,
        soil_ph

    )

    try:

        prediction = float(
            model.predict(
                input_df
            )[0]
        )

    except Exception as e:

        return render_template(

            "result.html",

            prediction=None,

            error=str(e),

            username=session[
                "username"
            ],

            data={

                "state":
                    state,

                "district":
                    district,

                "crop":
                    crop,

                "season":
                    season,

                "year":
                    year,

                "month":
                    month,

                "area":
                    area

            }

        )

    prediction = max(
        0.0,
        prediction
    )

    estimated_production = (
        prediction * area
    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        INSERT INTO predictions
        (
            username,
            state,
            district,
            crop,
            season,
            year,
            month,
            area,
            rainfall_mm,
            temperature_c,
            humidity_percent,
            soil_moisture_percent,
            soil_ph,
            prediction,
            estimated_production,
            prediction_type
        )

        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,

        (

            session[
                "username"
            ],

            state,

            district,

            crop,

            season,

            year,

            month,

            area,

            rainfall,

            temperature,

            humidity,

            soil_moisture,

            soil_ph,

            prediction,

            estimated_production,

            "normal"

        )
    )

    conn.commit()

    conn.close()

    return render_template(

        "result.html",

        username=session[
            "username"
        ],

        prediction=round(
            prediction,
            4
        ),

        estimated_production=round(
            estimated_production,
            4
        ),

        data={

            "state":
                state,

            "district":
                district,

            "crop":
                crop,

            "season":
                season,

            "year":
                year,

            "month":
                month,

            "area":
                area,

            "rainfall_mm":
                rainfall,

            "temperature_c":
                temperature,

            "humidity_percent":
                humidity,

            "soil_moisture_percent":
                soil_moisture,

            "soil_ph":
                soil_ph

        }

    )


# =========================================================
# AI PREDICTION PAGE
# =========================================================

@app.route(
    "/ai-prediction",
    methods=["GET"]
)
@role_required("farmer")
def ai_prediction():

    crops = get_unique_values(
        "crop"
    )

    return render_template(

        "ai_prediction.html",

        username=session[
            "username"
        ],

        crops=crops

    )


# =========================================================
# LOCATION SEARCH
# =========================================================

@app.route("/map/search")
@role_required("farmer")
def map_search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({

            "success":
                False,

            "results":
                []

        })

    try:

        response = requests.get(

            NOMINATIM_URL + "/search",

            params={

                "q":
                    query,

                "format":
                    "json",

                "addressdetails":
                    1,

                "limit":
                    5,

                "countrycodes":
                    "in"

            },

            headers={

                "User-Agent":
                    "CropYieldAI/1.0"

            },

            timeout=15

        )

        response.raise_for_status()

        results = response.json()

        cleaned = []

        for item in results:

            cleaned.append({

                "display_name":
                    item.get(
                        "display_name",
                        ""
                    ),

                "latitude":
                    item.get(
                        "lat"
                    ),

                "longitude":
                    item.get(
                        "lon"
                    ),

                "type":
                    item.get(
                        "type",
                        ""
                    )

            })

        return jsonify({

            "success":
                True,

            "results":
                cleaned

        })

    except Exception as e:

        print(
            "Map search error:",
            e
        )

        return jsonify({

            "success":
                False,

            "results":
                [],

            "error":
                str(e)

        })


# =========================================================
# REVERSE GEOCODING
# =========================================================

@app.route("/map/reverse")
@role_required("farmer")
def map_reverse():

    latitude = request.args.get(
        "lat",
        ""
    ).strip()

    longitude = request.args.get(
        "lon",
        ""
    ).strip()

    if not latitude or not longitude:

        return jsonify({

            "success":
                False,

            "message":
                "Coordinates required."

        })

    try:

        response = requests.get(

            NOMINATIM_URL + "/reverse",

            params={

                "lat":
                    latitude,

                "lon":
                    longitude,

                "format":
                    "json",

                "addressdetails":
                    1

            },

            headers={

                "User-Agent":
                    "CropYieldAI/1.0"

            },

            timeout=15

        )

        response.raise_for_status()

        data = response.json()

        address = data.get(
            "address",
            {}
        )

        location = (

            address.get(
                "village"
            )

            or address.get(
                "town"
            )

            or address.get(
                "city"
            )

            or address.get(
                "municipality"
            )

            or address.get(
                "suburb"
            )

            or address.get(
                "county"
            )

            or "Selected Location"

        )

        state = address.get(
            "state",
            ""
        )

        district = (

            address.get(
                "state_district"
            )

            or address.get(
                "district"
            )

            or address.get(
                "county"
            )

            or ""

        )

        return jsonify({

            "success":
                True,

            "location":
                location,

            "state":
                state,

            "district":
                district,

            "display_name":
                data.get(
                    "display_name",
                    ""
                )

        })

    except Exception as e:

        print(
            "Reverse geocoding error:",
            e
        )

        return jsonify({

            "success":
                False,

            "message":
                str(e)

        })


# =========================================================
# GEOCODE LOCATION
# =========================================================

def geocode_location(
    location
):

    try:

        response = requests.get(

            NOMINATIM_URL + "/search",

            params={

                "q":
                    location,

                "format":
                    "json",

                "limit":
                    1,

                "addressdetails":
                    1,

                "countrycodes":
                    "in"

            },

            headers={

                "User-Agent":
                    "CropYieldAI/1.0"

            },

            timeout=15

        )

        response.raise_for_status()

        results = response.json()

        if not results:

            return None

        item = results[0]

        latitude = float(
            item["lat"]
        )

        longitude = float(
            item["lon"]
        )

        address = item.get(
            "address",
            {}
        )

        state = address.get(
            "state",
            ""
        )

        district = (

            address.get(
                "state_district"
            )

            or address.get(
                "district"
            )

            or address.get(
                "county"
            )

            or ""

        )

        return {

            "latitude":
                latitude,

            "longitude":
                longitude,

            "state":
                state,

            "district":
                district,

            "display_name":
                item.get(
                    "display_name",
                    location
                )

        }

    except Exception as e:

        print(
            "Geocoding error:",
            e
        )

        return None


# =========================================================
# CURRENT WEATHER
# =========================================================

def get_current_weather(
    latitude,
    longitude
):

    try:

        response = requests.get(

            OPEN_METEO_URL,

            params={

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "current":
                    ",".join([

                        "temperature_2m",

                        "relative_humidity_2m",

                        "precipitation",

                        "rain",

                        "showers"

                    ]),

                "hourly":
                    "soil_moisture_0_to_1cm",

                "forecast_days":
                    1,

                "timezone":
                    "auto"

            },

            timeout=20

        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        hourly = data.get(
            "hourly",
            {}
        )

        temperature = current.get(
            "temperature_2m"
        )

        humidity = current.get(
            "relative_humidity_2m"
        )

        precipitation = current.get(
            "precipitation",
            0
        )

        rain = current.get(
            "rain",
            0
        )

        showers = current.get(
            "showers",
            0
        )

        rainfall = max(

            float(
                precipitation or 0
            ),

            float(
                rain or 0
            ),

            float(
                showers or 0
            )

        )

        soil_values = hourly.get(
            "soil_moisture_0_to_1cm",
            []
        )

        soil_moisture = None

        if soil_values:

            valid_values = [

                float(x)

                for x in soil_values

                if x is not None

            ]

            if valid_values:

                soil_moisture = (

                    sum(
                        valid_values
                    )

                    /

                    len(
                        valid_values
                    )

                ) * 100

        return {

            "temperature":
                round(
                    float(
                        temperature or 0
                    ),
                    2
                ),

            "rainfall":
                round(
                    rainfall,
                    2
                ),

            "humidity":
                round(
                    float(
                        humidity or 0
                    ),
                    2
                ),

            "soil_moisture":
                round(
                    float(
                        soil_moisture or 0
                    ),
                    2
                ),

            "source":
                "Open-Meteo"

        }

    except Exception as e:

        print(
            "Weather API error:",
            e
        )

        return {

            "temperature":
                0,

            "rainfall":
                0,

            "humidity":
                0,

            "soil_moisture":
                0,

            "source":
                "Weather data unavailable",

            "error":
                str(e)

        }

@app.route("/careers")
@login_required
@role_required("farmer")
def careers():
    return render_template(
        "careers.html",
        username=session.get("username")
    )
# =========================================================
# HISTORICAL CROP ANALYSIS
# =========================================================

def get_historical_analysis(

    crop,
    state="",
    district=""

):

    current_df = load_dataset()

    result = {

        "records":
            0,

        "average_yield":
            0,

        "maximum_yield":
            0,

        "minimum_yield":
            0,

        "latest_year":
            None

    }

    if "crop" not in current_df.columns:

        return result

    temp = current_df.copy()

    temp["crop_clean"] = (

        temp["crop"]

        .astype(str)

        .str.strip()

        .str.lower()

    )

    crop_clean = (

        str(crop)

        .strip()

        .lower()

    )

    temp = temp[
        temp["crop_clean"]
        == crop_clean
    ]

    if (
        state
        and "state"
        in temp.columns
    ):

        state_temp = temp[

            temp["state"]

            .astype(str)

            .str.strip()

            .str.lower()

            ==

            str(state)

            .strip()

            .lower()

        ]

        if len(
            state_temp
        ) > 0:

            temp = state_temp

    if (
        district
        and "district"
        in temp.columns
    ):

        district_temp = temp[

            temp["district"]

            .astype(str)

            .str.strip()

            .str.lower()

            ==

            str(district)

            .strip()

            .lower()

        ]

        if len(
            district_temp
        ) > 0:

            temp = district_temp

    yield_column = None

    if "yield" in temp.columns:

        yield_column = "yield"

    elif (
        "yield_ton_ha"
        in temp.columns
    ):

        yield_column = (
            "yield_ton_ha"
        )

    if yield_column is None:

        return result

    temp["yield_numeric"] = (

        pd.to_numeric(

            temp[
                yield_column
            ],

            errors="coerce"

        )

    )

    temp = temp.dropna(

        subset=[
            "yield_numeric"
        ]

    )

    if len(temp) == 0:

        return result

    result["records"] = len(
        temp
    )

    result["average_yield"] = round(

        float(

            temp[
                "yield_numeric"
            ].mean()

        ),

        4

    )

    result["maximum_yield"] = round(

        float(

            temp[
                "yield_numeric"
            ].max()

        ),

        4

    )

    result["minimum_yield"] = round(

        float(

            temp[
                "yield_numeric"
            ].min()

        ),

        4

    )

    if "year" in temp.columns:

        years = pd.to_numeric(

            temp["year"],

            errors="coerce"

        ).dropna()

        if len(years) > 0:

            result[
                "latest_year"
            ] = int(
                years.max()
            )

    return result

@app.route("/for-whom")
@login_required
@role_required("farmer")
def for_whom():
    return render_template(
        "for_whom.html",
        username=session.get("username")
    )

# =========================================================
# AGRICULTURE NEWS
# =========================================================

def get_agriculture_news(
    crop,
    location
):

    news = []

    search_query = (

        f"{crop} agriculture "
        f"{location} India"

    )

    try:

        response = requests.get(

            GOOGLE_NEWS_RSS_URL,

            params={

                "q":
                    search_query,

                "hl":
                    "en-IN",

                "gl":
                    "IN",

                "ceid":
                    "IN:en"

            },

            headers={

                "User-Agent":
                    "CropYieldAI/1.0"

            },

            timeout=15

        )

        response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

        for entry in feed.entries[:6]:

            title = entry.get(
                "title",
                ""
            )

            link = entry.get(
                "link",
                "#"
            )

            published = entry.get(
                "published",
                ""
            )

            if title:

                news.append({

                    "title":
                        html.unescape(
                            title
                        ),

                    "link":
                        link,

                    "published":
                        published

                })

    except Exception as e:

        print(
            "News error:",
            e
        )

    return news


# =========================================================
# AI ANALYSIS
# =========================================================

def generate_ai_analysis(

    crop,
    location,
    prediction,
    historical,
    weather

):

    average_yield = float(

        historical.get(
            "average_yield",
            0
        )
        or 0

    )

    temperature = float(

        weather.get(
            "temperature",
            0
        )
        or 0

    )

    rainfall = float(

        weather.get(
            "rainfall",
            0
        )
        or 0

    )

    humidity = float(

        weather.get(
            "humidity",
            0
        )
        or 0

    )

    soil_moisture = float(

        weather.get(
            "soil_moisture",
            0
        )
        or 0

    )

    if average_yield > 0:

        difference = (

            prediction
            - average_yield

        )

        percentage = (

            difference
            / average_yield

        ) * 100

    else:

        percentage = 0

    if percentage >= 10:

        yield_status = (

            "The predicted yield is above "
            "the historical average."

        )

    elif percentage <= -10:

        yield_status = (

            "The predicted yield is below "
            "the historical average."

        )

    else:

        yield_status = (

            "The predicted yield is close "
            "to the historical average."

        )

    weather_points = []

    if temperature > 35:

        weather_points.append(

            "High temperature may increase "
            "crop water stress."

        )

    elif temperature > 0:

        weather_points.append(

            "The current temperature has been "
            "included in the AI assessment."

        )

    if rainfall > 10:

        weather_points.append(

            "Recent precipitation is relatively high."

        )

    else:

        weather_points.append(

            "Recent precipitation is relatively low."

        )

    if humidity > 80:

        weather_points.append(

            "High humidity can increase the risk "
            "of some crop diseases."

        )

    if soil_moisture > 0:

        if soil_moisture < 15:

            weather_points.append(

                "Soil moisture appears low; "
                "irrigation monitoring is important."

            )

        elif soil_moisture > 40:

            weather_points.append(

                "Soil moisture appears relatively high."

            )

        else:

            weather_points.append(

                "Soil moisture is within a moderate range."

            )

    analysis = (

        f"For {crop} at {location}, the AI model "
        f"predicts approximately "
        f"{prediction:.4f} ton/ha. "
        f"{yield_status}"

    )

    if average_yield > 0:

        analysis += (

            f" The historical average used for comparison "
            f"is {average_yield:.4f} ton/ha."

        )

    analysis += (

        " Current environmental information was also "
        "considered for the AI assessment."

    )

    explanation = (

        f"The prediction is generated from the trained "
        f"crop-yield model using the available crop, "
        f"location, area and environmental features. "
        f"The historical dataset contains "
        f"{historical.get('records', 0)} relevant records. "
        + " ".join(
            weather_points
        )

    )

    recommendations = []

    if (
        soil_moisture > 0
        and soil_moisture < 15
    ):

        recommendations.append(

            "Monitor soil moisture and consider "
            "irrigation if required."

        )

    if rainfall < 2:

        recommendations.append(

            "Monitor rainfall and irrigation "
            "requirements closely."

        )

    if temperature > 35:

        recommendations.append(

            "Provide appropriate water management "
            "during hot conditions."

        )

    if humidity > 80:

        recommendations.append(

            "Monitor the crop for disease symptoms "
            "because of high humidity."

        )

    recommendations.append(

        "Continue monitoring local weather conditions "
        "before major farm decisions."

    )

    recommendations.append(

        "Use local agricultural department guidance "
        "for crop-specific actions."

    )

    recommendation = " ".join(
        recommendations
    )

    return (

        analysis,

        explanation,

        recommendation

    )


# =========================================================
# AI PREDICTION
# =========================================================

@app.route(
    "/ai-predict",
    methods=["POST"]
)
@role_required("farmer")
def ai_predict():

    location = request.form.get(
        "location",
        ""
    ).strip()

    crop = request.form.get(
        "crop",
        ""
    ).strip()

    area_value = request.form.get(
        "area",
        ""
    ).strip()

    latitude_value = request.form.get(
        "latitude",
        ""
    ).strip()

    longitude_value = request.form.get(
        "longitude",
        ""
    ).strip()

    if not location:

        flash(
            "Please select or enter a location."
        )

        return redirect(
            url_for("ai_prediction")
        )

    if not crop:

        flash(
            "Please select a crop."
        )

        return redirect(
            url_for("ai_prediction")
        )

    try:

        area = float(
            area_value
        )

        if area <= 0:

            raise ValueError

    except ValueError:

        flash(
            "Please enter a valid area."
        )

        return redirect(
            url_for("ai_prediction")
        )

    latitude = None

    longitude = None

    try:

        if latitude_value:

            latitude = float(
                latitude_value
            )

        if longitude_value:

            longitude = float(
                longitude_value
            )

    except ValueError:

        latitude = None

        longitude = None

    detected_state = ""

    detected_district = ""

    if (
        latitude is None
        or longitude is None
    ):

        geo = geocode_location(
            location
        )

        if geo is None:

            flash(
                "Unable to find this location."
            )

            return redirect(
                url_for("ai_prediction")
            )

        latitude = geo[
            "latitude"
        ]

        longitude = geo[
            "longitude"
        ]

        detected_state = geo.get(
            "state",
            ""
        )

        detected_district = geo.get(
            "district",
            ""
        )

    weather = get_current_weather(

        latitude,

        longitude

    )

    temperature = float(

        weather.get(
            "temperature",
            0
        )
        or 0

    )

    rainfall = float(

        weather.get(
            "rainfall",
            0
        )
        or 0

    )

    humidity = float(

        weather.get(
            "humidity",
            0
        )
        or 0

    )

    soil_moisture = float(

        weather.get(
            "soil_moisture",
            0
        )
        or 0

    )

    now = datetime.now()

    year = float(
        now.year
    )

    month = float(
        now.month
    )

    state = detected_state

    district = detected_district

    if state:

        state_matches = [

            x

            for x in get_unique_values(
                "state"
            )

            if x.lower()
            == state.lower()

        ]

        if state_matches:

            state = state_matches[0]

    if month in [
        6,
        7,
        8,
        9,
        10
    ]:

        season = "Kharif"

    elif month in [
        11,
        12,
        1,
        2,
        3
    ]:

        season = "Rabi"

    else:

        season = "Whole Year"

    dataset_seasons = get_unique_values(
        "season"
    )

    if dataset_seasons:

        season_matches = [

            x

            for x in dataset_seasons

            if x.lower()
            == season.lower()

        ]

        if season_matches:

            season = (
                season_matches[0]
            )

        else:

            season = (
                dataset_seasons[0]
            )

    input_df = create_prediction_dataframe(

        state=state,

        district=district,

        crop=crop,

        season=season,

        year=year,

        month=month,

        area=area,

        rainfall=rainfall,

        temperature=temperature,

        humidity=humidity,

        soil_moisture=soil_moisture,

        soil_ph=0.0

    )

    print("=" * 70)

    print(
        "AI PREDICTION"
    )

    print(
        "Location:",
        location
    )

    print(
        "Crop:",
        crop
    )

    print(
        "Weather:",
        weather
    )

    print(
        "Model input:"
    )

    print(
        input_df
    )

    print("=" * 70)

    try:

        prediction_result = (
            model.predict(
                input_df
            )
        )

        prediction = float(
            prediction_result[0]
        )

    except Exception as e:

        print(
            "AI model prediction error:",
            e
        )

        return render_template(

            "ai_result.html",

            username=session[
                "username"
            ],

            prediction=None,

            estimated_production=0,

            latitude=latitude,

            longitude=longitude,

            weather=weather,

            historical={},

            ai_analysis="",

            explanation="",

            recommendation="",

            news=[],

            error=str(e),

            data={

                "location":
                    location,

                "state":
                    state,

                "district":
                    district,

                "crop":
                    crop,

                "area":
                    area

            }

        )

    prediction = max(
        0.0,
        prediction
    )

    estimated_production = (
        prediction * area
    )

    historical = get_historical_analysis(

        crop=crop,

        state=state,

        district=district

    )

    (
        ai_analysis,
        explanation,
        recommendation
    ) = generate_ai_analysis(

        crop=crop,

        location=location,

        prediction=prediction,

        historical=historical,

        weather=weather

    )

    news = get_agriculture_news(

        crop=crop,

        location=location

    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        INSERT INTO predictions
        (
            username,
            state,
            district,
            location,
            latitude,
            longitude,
            crop,
            season,
            year,
            month,
            area,
            rainfall_mm,
            temperature_c,
            humidity_percent,
            soil_moisture_percent,
            soil_ph,
            prediction,
            estimated_production,
            prediction_type
        )

        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,

        (

            session[
                "username"
            ],

            state,

            district,

            location,

            latitude,

            longitude,

            crop,

            season,

            year,

            month,

            area,

            rainfall,

            temperature,

            humidity,

            soil_moisture,

            0.0,

            prediction,

            estimated_production,

            "ai"

        )

    )

    conn.commit()

    conn.close()

    return render_template(

        "ai_result.html",

        username=session[
            "username"
        ],

        prediction=round(
            prediction,
            4
        ),

        estimated_production=round(
            estimated_production,
            4
        ),

        latitude=latitude,

        longitude=longitude,

        weather=weather,

        historical=historical,

        ai_analysis=ai_analysis,

        explanation=explanation,

        recommendation=recommendation,

        news=news,

        data={

            "location":
                location,

            "state":
                state,

            "district":
                district,

            "crop":
                crop,

            "area":
                area

        }

    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# ERROR HANDLER - 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "login.html"
    ), 404


# =========================================================
# ERROR HANDLER - 500
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    print(
        "Internal server error:",
        error
    )

    return (
        "Internal Server Error. "
        "Check the Flask terminal for details.",
        500
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "CROP YIELD AI"
    )

    print("=" * 70)

    print(
        "Login             : /login"
    )

    print(
        "Register          : /register"
    )

    print(
        "Admin Dashboard   : /admin"
    )

    print(
        "Farmer Dashboard  : /farmer"
    )

    print(
        "Solutions         : /solutions"
    )

    print(
        "History           : /history"
    )

    print(
        "Analytics         : /analytics"
    )

    print(
        "Normal Prediction : /predict"
    )

    print(
        "AI Prediction     : /ai-prediction"
    )

    print(
        "AI Processing     : /ai-predict"
    )

    print(
        "Map Search        : /map/search"
    )

    print(
        "Reverse Geocode   : /map/reverse"
    )

    print(
        "Dataset Status    : /api/dataset-status"
    )

    print(
        "Reload Dataset    : /api/reload-dataset"
    )

    print("=" * 70)

    app.run(
        debug=True
    )