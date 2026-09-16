import os
import glob
import re
import pandas as pd

# =========================================================
# CONFIGURATION
# =========================================================

INPUT_FOLDER = "datasets"
OUTPUT_FOLDER = "data"

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "combined_crop_yield.csv"
)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================================================
# 1. CLEAN COLUMN NAMES
# =========================================================

def clean_column_name(col):
    col = str(col).strip().lower()

    col = re.sub(
        r"[^a-z0-9]+",
        "_",
        col
    )

    return col.strip("_")


# =========================================================
# 2. COLUMN ALIASES
# =========================================================

ALIASES = {

    "year": [
        "year",
        "crop_year",
        "cropyear",
        "agricultural_year"
    ],

    "month": [
        "month",
        "month_name"
    ],

    "state": [
        "state",
        "state_name"
    ],

    "district": [
        "district",
        "district_name"
    ],

    "crop": [
        "crop",
        "crop_name"
    ],

    "season": [
        "season",
        "crop_season"
    ],

    "area": [
        "area",
        "area_ha",
        "area_hectares",
        "area_in_hectares"
    ],

    "production": [
        "production",
        "production_tons",
        "production_tonnes",
        "production_mt",
        "production_in_tonnes"
    ],

    "yield": [
        "yield",
        "crop_yield",
        "yield_ha",
        "yield_ton_ha",
        "yield_tons_ha",
        "yield_per_hectare",
        "yield_tonnes_per_hectare"
    ],

    "rainfall_mm": [
        "rainfall_mm",
        "rainfall",
        "rainfall_millimeters"
    ],

    "temperature_c": [
        "temperature_c",
        "temperature",
        "temperature_celsius"
    ],

    "humidity_percent": [
        "humidity_percent",
        "humidity"
    ],

    "soil_moisture_percent": [
        "soil_moisture_percent",
        "soil_moisture"
    ],

    "soil_ph": [
        "soil_ph",
        "ph",
        "soil_ph_value"
    ]
}


# =========================================================
# 3. STANDARDIZE COLUMNS
# =========================================================

def standardize_columns(df):

    df.columns = [
        clean_column_name(c)
        for c in df.columns
    ]

    rename = {}

    for standard, names in ALIASES.items():

        for column in df.columns:

            if column in names:

                rename[column] = standard
                break

    df = df.rename(columns=rename)

    return df


# =========================================================
# 4. FILE HEADER
# =========================================================

def get_file_header(path):

    try:

        with open(
            path,
            "rb"
        ) as f:

            return f.read(1024)

    except Exception:

        return b""


# =========================================================
# 5. READ OLD XLS
# =========================================================

def read_real_xls(path):

    try:

        import xlrd

        book = xlrd.open_workbook(
            path,
            on_demand=True
        )

        sheet_names = book.sheet_names()

        print(
            "Excel sheets:",
            sheet_names
        )

        all_sheets = []

        for sheet_name in sheet_names:

            sheet = book.sheet_by_name(
                sheet_name
            )

            rows = []

            for row_index in range(
                sheet.nrows
            ):

                rows.append(
                    sheet.row_values(
                        row_index
                    )
                )

            if not rows:
                continue

            header = rows[0]
            data = rows[1:]

            df = pd.DataFrame(
                data,
                columns=header
            )

            all_sheets.append(df)

        if all_sheets:

            return pd.concat(
                all_sheets,
                ignore_index=True
            )

    except Exception as e:

        print(
            "Real XLS reader failed:",
            str(e)
        )

    return None


# =========================================================
# 6. READ XLSX
# =========================================================

def read_xlsx(path):

    try:

        return pd.read_excel(
            path,
            engine="openpyxl"
        )

    except Exception as e:

        print(
            "XLSX reader failed:",
            str(e)
        )

        return None


# =========================================================
# 7. READ HTML
# =========================================================

def read_html(path):

    try:

        tables = pd.read_html(
            path
        )

        if not tables:
            return None

        print(
            "HTML tables found:",
            len(tables)
        )

        table = max(
            tables,
            key=lambda x:
            x.shape[0] * x.shape[1]
        )

        return table

    except Exception as e:

        print(
            "HTML reader failed:",
            str(e)
        )

        return None


# =========================================================
# 8. READ CSV / TEXT
# =========================================================

def read_text_file(path):

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin1"
    ]

    for encoding in encodings:

        try:

            df = pd.read_csv(
                path,
                sep=None,
                engine="python",
                encoding=encoding
            )

            if len(df.columns) > 1:

                return df

        except Exception:

            pass

    return None


# =========================================================
# 9. AUTOMATIC FILE READER
# =========================================================

def read_dataset(path):

    print()
    print(
        "Reading:",
        os.path.basename(path)
    )

    header = get_file_header(
        path
    )

    # -----------------------------------------------------
    # XLSX / ZIP
    # -----------------------------------------------------

    if header.startswith(
        b"PK"
    ):

        print(
            "Detected: XLSX/ZIP format"
        )

        df = read_xlsx(
            path
        )

        if df is not None:
            return df

    # -----------------------------------------------------
    # OLD XLS
    # -----------------------------------------------------

    if header.startswith(
        b"\xD0\xCF\x11\xE0"
    ):

        print(
            "Detected: OLD XLS format"
        )

        df = read_real_xls(
            path
        )

        if df is not None:
            return df

    # -----------------------------------------------------
    # HTML
    # -----------------------------------------------------

    header_lower = header.lower()

    if (
        b"<html" in header_lower
        or
        b"<table" in header_lower
        or
        b"<!doctype" in header_lower
    ):

        print(
            "Detected: HTML table"
        )

        df = read_html(
            path
        )

        if df is not None:
            return df

    # -----------------------------------------------------
    # TRY XLS
    # -----------------------------------------------------

    print(
        "Trying XLS reader..."
    )

    df = read_real_xls(
        path
    )

    if df is not None:
        return df

    # -----------------------------------------------------
    # TRY HTML
    # -----------------------------------------------------

    print(
        "Trying HTML reader..."
    )

    df = read_html(
        path
    )

    if df is not None:
        return df

    # -----------------------------------------------------
    # TRY TEXT / CSV
    # -----------------------------------------------------

    print(
        "Trying text reader..."
    )

    df = read_text_file(
        path
    )

    if df is not None:
        return df

    return None


# =========================================================
# 10. FIND ALL DATASET FILES
# =========================================================

patterns = [
    "*.xls",
    "*.xlsx",
    "*.csv"
]

files = []

for pattern in patterns:

    files.extend(
        glob.glob(
            os.path.join(
                INPUT_FOLDER,
                pattern
            )
        )
    )


files = sorted(
    list(set(files))
)


print()
print(
    "========================================"
)

print(
    "FOUND DATASET FILES:",
    len(files)
)

print(
    "========================================"
)


if not files:

    raise FileNotFoundError(
        "No datasets found inside datasets folder."
    )


# =========================================================
# 11. LOAD DATASETS
# =========================================================

datasets = []


for path in files:

    filename = os.path.basename(
        path
    )

    try:

        df = read_dataset(
            path
        )

        if df is None:

            print(
                "FAILED:",
                filename
            )

            continue

        if df.empty:

            print(
                "EMPTY:",
                filename
            )

            continue

        print(
            "Rows:",
            len(df)
        )

        print(
            "Original columns:"
        )

        print(
            list(df.columns)
        )

        # -------------------------------------------------
        # STANDARDIZE
        # -------------------------------------------------

        df = standardize_columns(
            df
        )

        print(
            "Standard columns:"
        )

        print(
            list(df.columns)
        )

        # -------------------------------------------------
        # SOURCE FILE
        # -------------------------------------------------

        df["source_file"] = filename

        datasets.append(
            df
        )

        print(
            "SUCCESS:",
            filename
        )

    except Exception as e:

        print(
            "ERROR:",
            filename
        )

        print(
            str(e)
        )


# =========================================================
# 12. CHECK DATASETS
# =========================================================

print()
print(
    "========================================"
)

print(
    "SUCCESSFULLY READ:",
    len(datasets)
)

print(
    "========================================"
)


if not datasets:

    raise ValueError(
        """
No datasets could be read.

Check the files inside the datasets folder.
"""
    )


# =========================================================
# 13. COMBINE DATASETS
# =========================================================

combined = pd.concat(
    datasets,
    ignore_index=True,
    sort=False
)


print()
print(
    "Combined shape:",
    combined.shape
)


# =========================================================
# 14. REMOVE COMPLETELY EMPTY ROWS
# =========================================================

combined = combined.dropna(
    how="all"
)


# =========================================================
# 15. CLEAN STRING DATA
# =========================================================

for column in combined.columns:

    if combined[column].dtype == "object":

        combined[column] = (
            combined[column]
            .astype(str)
            .str.strip()
        )


# =========================================================
# 16. CONVERT YEAR
# =========================================================

if "year" in combined.columns:

    combined["year"] = (
        combined["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0]
    )

    combined["year"] = pd.to_numeric(
        combined["year"],
        errors="coerce"
    )


# =========================================================
# 17. CONVERT MONTH
# =========================================================

if "month" in combined.columns:

    # Keep month as text if it contains names
    combined["month"] = (
        combined["month"]
        .astype(str)
        .str.strip()
    )


# =========================================================
# 18. CONVERT NUMERIC COLUMNS
# =========================================================

numeric_columns = [

    "area",
    "production",
    "yield",
    "rainfall_mm",
    "temperature_c",
    "humidity_percent",
    "soil_moisture_percent",
    "soil_ph"
]


for column in numeric_columns:

    if column in combined.columns:

        combined[column] = (
            combined[column]
            .astype(str)
            .str.replace(
                ",",
                "",
                regex=False
            )
            .str.replace(
                "NA",
                "",
                regex=False
            )
            .str.replace(
                "N/A",
                "",
                regex=False
            )
        )

        combined[column] = pd.to_numeric(
            combined[column],
            errors="coerce"
        )


# =========================================================
# 19. CHECK REQUIRED COLUMNS
# =========================================================

required_columns = [
    "year",
    "state",
    "district",
    "crop",
    "yield"
]


missing_columns = [
    column
    for column in required_columns
    if column not in combined.columns
]


if missing_columns:

    print()
    print(
        "========================================"
    )

    print(
        "MISSING REQUIRED COLUMNS"
    )

    print(
        "========================================"
    )

    print(
        "Missing:",
        missing_columns
    )

    print(
        "Available columns:"
    )

    print(
        combined.columns.tolist()
    )

    combined.to_csv(
        OUTPUT_FILE,
        index=False
    )

    raise ValueError(
        "Required columns are missing: "
        + str(missing_columns)
    )


# =========================================================
# 20. YIELD CHECK
# =========================================================

print()
print(
    "========================================"
)

print(
    "YIELD COLUMN FOUND"
)

print(
    "========================================"
)

print(
    "Using column: yield"
)


print(
    "Yield missing values:",
    combined["yield"].isna().sum()
)


# =========================================================
# 21. REMOVE INVALID YIELD
# =========================================================

before_yield = len(
    combined
)


combined = combined[
    combined["yield"].notna()
]


combined = combined[
    combined["yield"] >= 0
]


after_yield = len(
    combined
)


print(
    "Rows removed due to invalid yield:",
    before_yield - after_yield
)


# =========================================================
# 22. REMOVE INVALID YEAR
# =========================================================

if "year" in combined.columns:

    combined = combined[
        combined["year"].notna()
    ]

    combined = combined[
        (combined["year"] >= 2015)
        &
        (combined["year"] <= 2026)
    ]


# =========================================================
# 23. CLEAN CATEGORY COLUMNS
# =========================================================

category_columns = [
    "state",
    "district",
    "crop",
    "season"
]


for column in category_columns:

    if column in combined.columns:

        combined[column] = (
            combined[column]
            .astype(str)
            .str.strip()
        )

        combined[column] = (
            combined[column]
            .replace(
                ["nan", "None", ""],
                pd.NA
            )
        )


# =========================================================
# 24. REMOVE DUPLICATES
# =========================================================

key_columns = [

    column

    for column in [
        "year",
        "month",
        "state",
        "district",
        "crop",
        "season"
    ]

    if column in combined.columns
]


if key_columns:

    before_duplicates = len(
        combined
    )

    combined = combined.drop_duplicates(
        subset=key_columns
    )

    after_duplicates = len(
        combined
    )

    print(
        "Duplicate rows removed:",
        before_duplicates - after_duplicates
    )

else:

    combined = combined.drop_duplicates()


# =========================================================
# 25. SORT DATA
# =========================================================

sort_columns = [

    column

    for column in [
        "year",
        "month",
        "state",
        "district",
        "crop"
    ]

    if column in combined.columns
]


if sort_columns:

    combined = combined.sort_values(
        sort_columns
    )


# =========================================================
# 26. RESET INDEX
# =========================================================

combined = combined.reset_index(
    drop=True
)


# =========================================================
# 27. SAVE DATASET
# =========================================================

combined.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 28. FINAL REPORT
# =========================================================

print()
print(
    "========================================"
)

print(
    "DATASET PREPARATION COMPLETE"
)

print(
    "========================================"
)

print(
    "Final rows:",
    len(combined)
)

print(
    "Final columns:",
    len(combined.columns)
)

print()
print(
    "Columns:"
)

print(
    combined.columns.tolist()
)

print()
print(
    "Saved file:"
)

print(
    OUTPUT_FILE
)


# =========================================================
# 29. YEARS
# =========================================================

if "year" in combined.columns:

    years = sorted(
        combined["year"]
        .dropna()
        .unique()
        .tolist()
    )

    print()
    print(
        "Available years:"
    )

    print(
        years
    )


# =========================================================
# 30. MONTHS
# =========================================================

if "month" in combined.columns:

    months = sorted(
        combined["month"]
        .dropna()
        .unique()
        .tolist()
    )

    print()
    print(
        "Number of months:",
        len(months)
    )


# =========================================================
# 31. STATES
# =========================================================

if "state" in combined.columns:

    print()
    print(
        "Number of states:",
        combined["state"].nunique()
    )

    print(
        "States:"
    )

    print(
        sorted(
            combined["state"]
            .dropna()
            .unique()
            .tolist()
        )
    )


# =========================================================
# 32. DISTRICTS
# =========================================================

if "district" in combined.columns:

    print()
    print(
        "Number of districts:",
        combined["district"].nunique()
    )


# =========================================================
# 33. CROPS
# =========================================================

if "crop" in combined.columns:

    print()
    print(
        "Number of crops:",
        combined["crop"].nunique()
    )


# =========================================================
# 34. SEASONS
# =========================================================

if "season" in combined.columns:

    print()
    print(
        "Number of seasons:",
        combined["season"].nunique()
    )


# =========================================================
# 35. DATA TYPES
# =========================================================

print()
print(
    "========================================"
)

print(
    "DATA TYPES"
)

print(
    "========================================"
)

print(
    combined.dtypes
)


# =========================================================
# 36. FIRST 10 ROWS
# =========================================================

print()
print(
    "========================================"
)

print(
    "FIRST 10 ROWS"
)

print(
    "========================================"
)

print(
    combined.head(10).to_string()
)


print()
print(
    "========================================"
)

print(
    "READY FOR MODEL TRAINING"
)

print(
    "========================================"
)