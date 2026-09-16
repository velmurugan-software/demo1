import os
import numpy as np
import pandas as pd

# =========================================================
# SETTINGS
# =========================================================

OUTPUT_FOLDER = "datasets"
OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "crop_yield_india_2015_2026_20_crops.csv"
)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

np.random.seed(42)

# =========================================================
# 8 STATES + 77 DISTRICTS
# =========================================================

state_districts = {
    "Tamil Nadu": [
        "Ariyalur", "Coimbatore", "Cuddalore", "Dharmapuri",
        "Dindigul", "Erode", "Kanchipuram", "Karur",
        "Madurai", "Vellore"
    ],

    "Andhra Pradesh": [
        "Anantapur", "Chittoor", "East Godavari", "Guntur",
        "Kadapa", "Krishna", "Kurnool", "Nellore",
        "Prakasam", "Visakhapatnam"
    ],

    "Telangana": [
        "Adilabad", "Jagtial", "Karimnagar", "Khammam",
        "Mahbubnagar", "Medak", "Nalgonda", "Nizamabad",
        "Rangareddy", "Warangal"
    ],

    "Karnataka": [
        "Bagalkot", "Bangalore Rural", "Belagavi", "Bellary",
        "Chikkaballapur", "Chikkamagaluru", "Dharwad",
        "Hassan", "Mandya", "Mysuru"
    ],

    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Aurangabad",
        "Beed", "Bhandara", "Buldhana", "Chandrapur",
        "Dhule", "Jalgaon"
    ],

    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ayodhya", "Azamgarh",
        "Bareilly", "Farrukhabad", "Gorakhpur",
        "Kanpur Nagar", "Lucknow", "Varanasi"
    ],

    "Madhya Pradesh": [
        "Chhindwara", "Dewas", "Dhar", "Gwalior",
        "Indore", "Jabalpur", "Mandsaur", "Sagar",
        "Ujjain"
    ],

    "Punjab": [
        "Amritsar", "Bathinda", "Fazilka", "Firozpur",
        "Gurdaspur", "Hoshiarpur", "Jalandhar", "Ludhiana",
        "Patiala", "Sangrur"
    ]
}

# Check district count
district_count = sum(
    len(v) for v in state_districts.values()
)

print("Districts:", district_count)

# =========================================================
# 20 CROPS
# =========================================================

crops = [
    "Rice",
    "Wheat",
    "Maize",
    "Groundnut",
    "Cotton",
    "Sugarcane",
    "Soybean",
    "Chickpea",
    "Pigeon Pea",
    "Sorghum",
    "Pearl Millet",
    "Finger Millet",
    "Sunflower",
    "Mustard",
    "Potato",
    "Onion",
    "Tomato",
    "Banana",
    "Coconut",
    "Sesame"
]

# =========================================================
# CROP BASE YIELDS
# =========================================================

crop_yield = {
    "Rice": 3.2,
    "Wheat": 3.4,
    "Maize": 4.0,
    "Groundnut": 2.1,
    "Cotton": 1.8,
    "Sugarcane": 75.0,
    "Soybean": 1.6,
    "Chickpea": 1.3,
    "Pigeon Pea": 1.2,
    "Sorghum": 1.4,
    "Pearl Millet": 1.5,
    "Finger Millet": 1.7,
    "Sunflower": 1.4,
    "Mustard": 1.6,
    "Potato": 22.0,
    "Onion": 20.0,
    "Tomato": 25.0,
    "Banana": 35.0,
    "Coconut": 8.5,
    "Sesame": 0.8
}

# =========================================================
# STATE FACTORS
# =========================================================

state_factor = {
    "Tamil Nadu": 1.05,
    "Andhra Pradesh": 1.03,
    "Telangana": 1.00,
    "Karnataka": 0.98,
    "Maharashtra": 1.02,
    "Uttar Pradesh": 1.08,
    "Madhya Pradesh": 1.04,
    "Punjab": 1.12
}

# =========================================================
# GENERATE DATA
# =========================================================

rows = []

TARGET_ROWS = 20000

states = list(state_districts.keys())

for i in range(TARGET_ROWS):

    state = np.random.choice(states)

    district = np.random.choice(
        state_districts[state]
    )

    crop = np.random.choice(crops)

    year = np.random.randint(
        2015,
        2027
    )

    month = np.random.randint(
        1,
        13
    )

    # -----------------------------------------------------
    # SEASON
    # -----------------------------------------------------

    if month in [6, 7, 8, 9, 10]:
        season = "Kharif"

    elif month in [11, 12, 1, 2]:
        season = "Rabi"

    else:
        season = "Zaid"

    # -----------------------------------------------------
    # WEATHER
    # -----------------------------------------------------

    temperature_base = {
        "Tamil Nadu": 28,
        "Andhra Pradesh": 29,
        "Telangana": 28,
        "Karnataka": 26,
        "Maharashtra": 27,
        "Uttar Pradesh": 24,
        "Madhya Pradesh": 25,
        "Punjab": 23
    }

    rainfall_base = {
        "Tamil Nadu": 950,
        "Andhra Pradesh": 900,
        "Telangana": 850,
        "Karnataka": 800,
        "Maharashtra": 850,
        "Uttar Pradesh": 750,
        "Madhya Pradesh": 800,
        "Punjab": 650
    }

    temperature = (
        temperature_base[state]
        + np.random.normal(0, 2)
    )

    rainfall = (
        rainfall_base[state]
        + np.random.normal(0, 150)
    )

    rainfall = max(
        200,
        rainfall
    )

    humidity = np.random.uniform(
        45,
        90
    )

    soil_moisture = np.random.uniform(
        20,
        75
    )

    soil_ph = np.random.uniform(
        5.5,
        8.0
    )

    # -----------------------------------------------------
    # AREA
    # -----------------------------------------------------

    area = np.random.uniform(
        5,
        500
    )

    # -----------------------------------------------------
    # YIELD
    # -----------------------------------------------------

    base = crop_yield[crop]

    weather_factor = (
        1
        + (rainfall - rainfall_base[state])
        / rainfall_base[state]
        * 0.10
    )

    temperature_factor = (
        1
        - abs(temperature - 26)
        * 0.01
    )

    soil_factor = (
        1
        - abs(soil_ph - 6.8)
        * 0.02
    )

    yield_value = (
        base
        * state_factor[state]
        * weather_factor
        * temperature_factor
        * soil_factor
        * np.random.uniform(
            0.90,
            1.10
        )
    )

    yield_value = max(
        0.1,
        yield_value
    )

    # -----------------------------------------------------
    # PRODUCTION
    # -----------------------------------------------------

    production = (
        area * yield_value
    )

    rows.append([
        year,
        month,
        state,
        district,
        crop,
        season,
        round(area, 2),
        round(production, 2),
        round(yield_value, 3),
        round(rainfall, 2),
        round(temperature, 2),
        round(humidity, 2),
        round(soil_moisture, 2),
        round(soil_ph, 2)
    ])

# =========================================================
# DATAFRAME
# =========================================================

columns = [
    "Year",
    "Month",
    "State",
    "District",
    "Crop",
    "Season",
    "Area_ha",
    "Production_tons",
    "Yield_ton_ha",
    "Rainfall_mm",
    "Temperature_C",
    "Humidity_percent",
    "Soil_Moisture_percent",
    "Soil_pH"
]

df = pd.DataFrame(
    rows,
    columns=columns
)

# =========================================================
# REMOVE DUPLICATES
# =========================================================

df = df.drop_duplicates()

# =========================================================
# SAVE
# =========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# =========================================================
# REPORT
# =========================================================

print()
print("=" * 50)
print("DATASET CREATED SUCCESSFULLY")
print("=" * 50)

print(
    "Rows:",
    len(df)
)

print(
    "States:",
    df["State"].nunique()
)

print(
    "Districts:",
    df["District"].nunique()
)

print(
    "Crops:",
    df["Crop"].nunique()
)

print(
    "Years:",
    df["Year"].min(),
    "-",
    df["Year"].max()
)

print()
print("Crops:")
print(
    sorted(
        df["Crop"].unique()
    )
)

print()
print("Saved:")
print(OUTPUT_FILE)

print("=" * 50)