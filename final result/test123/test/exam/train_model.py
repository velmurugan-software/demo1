import os
import json
import joblib

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from xgboost import XGBRegressor


# =========================================================
# CONFIGURATION
# =========================================================

DATASET = "data/combined_crop_yield.csv"

MODEL_DIR = "models"

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "best_model.pkl"
)

MODEL_INFO_PATH = os.path.join(
    MODEL_DIR,
    "model_info.json"
)


os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# =========================================================
# LOAD DATASET
# =========================================================

if not os.path.exists(DATASET):

    raise FileNotFoundError(
        f"""
Dataset not found:

{DATASET}

Please place combined_crop_yield.csv inside:

data/
"""
    )


print("=" * 70)
print("LOADING CROP YIELD DATASET")
print("=" * 70)


df = pd.read_csv(
    DATASET
)


print(
    "Dataset shape:",
    df.shape
)


print(
    "\nDataset columns:"
)

print(
    df.columns.tolist()
)


# =========================================================
# CLEAN COLUMN NAMES
# =========================================================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)


print(
    "\nCleaned columns:"
)

print(
    df.columns.tolist()
)


# =========================================================
# TARGET
# =========================================================

TARGET = "yield"


if TARGET not in df.columns:

    raise ValueError(
        """
Yield column not found.

Expected column:

yield
"""
    )


# =========================================================
# REMOVE SOURCE COLUMN
# =========================================================

if "source_file" in df.columns:

    df = df.drop(
        columns=[
            "source_file"
        ]
    )


# =========================================================
# FEATURE DEFINITIONS
# =========================================================

preferred_categorical = [

    "state",

    "district",

    "crop",

    "season"
]


preferred_numeric = [

    "year",

    "month",

    "area",

    "rainfall_mm",

    "temperature_c",

    "humidity_percent",

    "soil_moisture_percent",

    "soil_ph"
]


# =========================================================
# FIND AVAILABLE FEATURES
# =========================================================

categorical_features = [

    column

    for column in preferred_categorical

    if column in df.columns
]


numeric_features = [

    column

    for column in preferred_numeric

    if column in df.columns
]


features = (

    categorical_features

    +

    numeric_features
)


# =========================================================
# PRINT FEATURES
# =========================================================

print(
    "\nCategorical features:"
)

print(
    categorical_features
)


print(
    "\nNumeric features:"
)

print(
    numeric_features
)


print(
    "\nFinal model features:"
)

print(
    features
)


# =========================================================
# CHECK IMPORTANT FEATURES
# =========================================================

important_features = [

    "state",

    "district",

    "crop",

    "year",

    "area",

    "rainfall_mm",

    "temperature_c",

    "humidity_percent",

    "soil_moisture_percent",

    "soil_ph"
]


missing_important = [

    column

    for column in important_features

    if column not in df.columns
]


if missing_important:

    print(
        "\nWARNING!"
    )

    print(
        "These columns are missing from the dataset:"
    )

    print(
        missing_important
    )

    print(
        """
The model cannot learn from these features
until they exist in the training dataset.
"""
    )


# =========================================================
# VALIDATE FEATURES
# =========================================================

if not features:

    raise ValueError(
        "No usable features found."
    )


# =========================================================
# CONVERT NUMERIC COLUMNS
# =========================================================

for column in numeric_features:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# =========================================================
# CONVERT TARGET
# =========================================================

df[TARGET] = pd.to_numeric(
    df[TARGET],
    errors="coerce"
)


# =========================================================
# REMOVE INVALID TARGET
# =========================================================

before_rows = len(df)


df = df.dropna(
    subset=[
        TARGET
    ]
)


after_rows = len(df)


print(
    "\nRemoved invalid target rows:",
    before_rows - after_rows
)


# =========================================================
# REMOVE NEGATIVE YIELD
# =========================================================

df = df[
    df[TARGET] >= 0
]


# =========================================================
# X / Y
# =========================================================

X = df[features].copy()

y = df[TARGET].copy()


print(
    "\nFinal training rows:",
    len(X)
)


# =========================================================
# TRAIN TEST SPLIT
# =========================================================

X_train, X_test, y_train, y_test = (

    train_test_split(

        X,

        y,

        test_size=0.20,

        random_state=42
    )
)


print(
    "\nTraining rows:",
    len(X_train)
)

print(
    "Testing rows:",
    len(X_test)
)


# =========================================================
# NUMERIC PIPELINE
# =========================================================

numeric_pipeline = Pipeline(

    steps=[

        (
            "imputer",

            SimpleImputer(
                strategy="median"
            )
        )
    ]
)


# =========================================================
# CATEGORICAL PIPELINE
# =========================================================

categorical_pipeline = Pipeline(

    steps=[

        (
            "imputer",

            SimpleImputer(
                strategy="most_frequent"
            )
        ),

        (
            "encoder",

            OneHotEncoder(
                handle_unknown="ignore"
            )
        )
    ]
)


# =========================================================
# PREPROCESSOR
# =========================================================

transformers = []


if numeric_features:

    transformers.append(

        (
            "numeric",

            numeric_pipeline,

            numeric_features
        )
    )


if categorical_features:

    transformers.append(

        (
            "categorical",

            categorical_pipeline,

            categorical_features
        )
    )


preprocessor = ColumnTransformer(

    transformers=transformers
)


# =========================================================
# MODELS
# =========================================================

models = {

    "Random Forest":

        RandomForestRegressor(

            n_estimators=300,

            random_state=42,

            n_jobs=-1
        ),


    "Gradient Boosting":

        GradientBoostingRegressor(

            n_estimators=200,

            learning_rate=0.05,

            max_depth=3,

            random_state=42
        ),


    "XGBoost":

        XGBRegressor(

            n_estimators=300,

            learning_rate=0.05,

            max_depth=6,

            subsample=0.8,

            colsample_bytree=0.8,

            objective="reg:squarederror",

            random_state=42,

            n_jobs=-1
        )
}


# =========================================================
# TRAIN MODELS
# =========================================================

results = {}


best_pipeline = None

best_model_name = None

best_r2 = -float("inf")


for name, model in models.items():

    print("\n" + "=" * 70)

    print(
        "TRAINING:",
        name
    )

    print("=" * 70)


    pipeline = Pipeline(

        steps=[

            (
                "preprocessor",

                preprocessor
            ),

            (
                "model",

                model
            )
        ]
    )


    # -----------------------------------------------------
    # FIT
    # -----------------------------------------------------

    pipeline.fit(

        X_train,

        y_train
    )


    # -----------------------------------------------------
    # PREDICT
    # -----------------------------------------------------

    predictions = pipeline.predict(

        X_test
    )


    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    mae = mean_absolute_error(

        y_test,

        predictions
    )


    rmse = np.sqrt(

        mean_squared_error(

            y_test,

            predictions
        )
    )


    r2 = r2_score(

        y_test,

        predictions
    )


    results[name] = {

        "MAE": float(mae),

        "RMSE": float(rmse),

        "R2": float(r2)
    }


    print(
        "MAE :",
        round(mae, 4)
    )


    print(
        "RMSE:",
        round(rmse, 4)
    )


    print(
        "R2  :",
        round(r2, 4)
    )


    # -----------------------------------------------------
    # BEST MODEL
    # -----------------------------------------------------

    if r2 > best_r2:

        best_r2 = r2

        best_pipeline = pipeline

        best_model_name = name


# =========================================================
# SAVE BEST MODEL
# =========================================================

print("\n" + "=" * 70)

print(
    "BEST MODEL:",
    best_model_name
)

print(
    "BEST R2:",
    round(best_r2, 4)
)

print("=" * 70)


joblib.dump(

    best_pipeline,

    MODEL_PATH
)


# =========================================================
# MODEL INFORMATION
# =========================================================

model_info = {

    "target": TARGET,

    "best_model":
        best_model_name,

    "features":
        features,

    "categorical_features":
        categorical_features,

    "numeric_features":
        numeric_features,

    "results":
        results,

    "units":
        "ton/ha"
}


with open(

    MODEL_INFO_PATH,

    "w",

    encoding="utf-8"

) as file:

    json.dump(

        model_info,

        file,

        indent=4
    )


# =========================================================
# COMPLETED
# =========================================================

print("\n")

print("=" * 70)

print(
    "TRAINING COMPLETED SUCCESSFULLY"
)

print("=" * 70)

print(
    "Best model:",
    best_model_name
)

print(
    "R2:",
    round(best_r2, 4)
)

print(
    "Model:",
    MODEL_PATH
)

print(
    "Model info:",
    MODEL_INFO_PATH
)

print("=" * 70)