import pandas as pd

from app.etl.loader import load_dataset

from app.etl.cleaner import (
    clean_basic_data,
    detect_category_inconsistencies,
    analyze_missing_values,
    validate_date_columns,
    standardize_date_columns,
    validate_numeric_columns,
    detect_outliers,
    validate_business_rules,
    impute_missing_values,
    reconstruct_business_values,
)


def run_etl_pipeline(file_path):
    """
    Run the complete ETL pipeline.

    Steps:
        1. Load dataset
        2. Basic cleaning
        3. Category analysis
        4. Missing value analysis
        5. Date validation
        6. Date standardization
        7. Numeric validation
        8. Outlier detection
        9. Business rule validation
        10. Missing value imputation
        11. Business value reconstruction
    """

    # ============================================================
    # 1. LOAD DATASET
    # ============================================================

    df = load_dataset(file_path)

    if df is None:
        raise ValueError("Dataset could not be loaded.")

    if df.empty:
        raise ValueError("Dataset is empty.")

    # ============================================================
    # 2. BASIC CLEANING
    # ============================================================

    df, cleaning_report = clean_basic_data(df)

    # ============================================================
    # 3. CATEGORY INCONSISTENCY ANALYSIS
    # ============================================================

    category_issues = detect_category_inconsistencies(df)

    # ============================================================
    # 4. MISSING VALUE ANALYSIS
    # ============================================================

    missing_values = analyze_missing_values(df)

    # ============================================================
    # 5. DATE VALIDATION
    # ============================================================

    date_issues = validate_date_columns(df)

    # ============================================================
    # 6. DATE STANDARDIZATION
    # ============================================================

    df, date_standardization_report = (
        standardize_date_columns(df)
    )

    # ============================================================
    # 7. NUMERIC VALIDATION
    # ============================================================

    numeric_issues = validate_numeric_columns(df)

    # ============================================================
    # 8. OUTLIER DETECTION
    # ============================================================

    outlier_issues = detect_outliers(df)

    # ============================================================
    # 9. BUSINESS RULE VALIDATION
    # ============================================================

    business_issues = validate_business_rules(df)

    # ============================================================
    # 10. MISSING VALUE IMPUTATION
    # ============================================================

    df, imputation_report = impute_missing_values(df)

    # ============================================================
    # 11. BUSINESS VALUE RECONSTRUCTION
    # ============================================================

    df, reconstruction_report = (
        reconstruct_business_values(df)
    )

    # ============================================================
    # 12. FINAL REPORT
    # ============================================================

    report = {
        "category_issues": category_issues,

        "missing_values": missing_values,

        "date_issues": date_issues,

        "date_standardization": (
            date_standardization_report
        ),

        "numeric_issues": numeric_issues,

        "outlier_issues": outlier_issues,

        "business_issues": business_issues,

        "imputation_report": imputation_report,

        "reconstruction_report": reconstruction_report,

        "cleaning_report": cleaning_report,

        "preview": (
            df.head(5)
            .astype(object)
            .where(
                pd.notnull(df.head(5)),
                None
            )
            .to_dict(orient="records")
        )
    }

    return df, report