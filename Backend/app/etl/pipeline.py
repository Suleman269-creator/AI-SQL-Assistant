import pandas as pd

from app.etl.loader import load_dataset

from app.etl.cleaner import (
    clean_basic_data,
    detect_category_inconsistencies,
    standardize_category_values,
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

    Pipeline:
        1. Load dataset
        2. Basic cleaning
        3. Category inconsistency detection
        4. Category standardization
        5. Missing value analysis
        6. Date validation
        7. Date standardization
        8. Numeric validation
        9. Outlier detection
        10. Business rule validation
        11. Missing value imputation
        12. Business value reconstruction
        13. Final validation
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
    # 3. CATEGORY INCONSISTENCY DETECTION
    # ============================================================

    category_issues_before = (
        detect_category_inconsistencies(df)
    )

    # ============================================================
    # 4. CATEGORY STANDARDIZATION
    # ============================================================

    df, category_standardization_report = (
        standardize_category_values(df)
    )

    # ============================================================
    # 5. CATEGORY INCONSISTENCY DETECTION AFTER CLEANING
    # ============================================================

    category_issues_after = (
        detect_category_inconsistencies(df)
    )

    # ============================================================
    # 6. MISSING VALUE ANALYSIS
    # ============================================================

    missing_values = analyze_missing_values(df)

    # ============================================================
    # 7. DATE VALIDATION
    # ============================================================

    date_issues = validate_date_columns(df)

    # ============================================================
    # 8. DATE STANDARDIZATION
    # ============================================================

    df, date_standardization_report = (
        standardize_date_columns(df)
    )

    # ============================================================
    # 9. NUMERIC VALIDATION
    # ============================================================

    numeric_issues = validate_numeric_columns(df)

    # ============================================================
    # 10. OUTLIER DETECTION
    # ============================================================

    outlier_issues = detect_outliers(df)

    # ============================================================
    # 11. BUSINESS RULE VALIDATION
    # ============================================================

    business_issues = validate_business_rules(df)

    # ============================================================
    # 12. MISSING VALUE IMPUTATION
    # ============================================================

    df, imputation_report = (
        impute_missing_values(df)
    )

    # ============================================================
    # 13. BUSINESS VALUE RECONSTRUCTION
    # ============================================================

    df, reconstruction_report = (
        reconstruct_business_values(df)
    )

    # ============================================================
    # 14. FINAL REPORT
    # ============================================================

    preview_df = df.head(5)

    report = {

        "category_issues_before": (
            category_issues_before
        ),

        "category_standardization": (
            category_standardization_report
        ),

        "category_issues_after": (
            category_issues_after
        ),

        "missing_values": (
            missing_values
        ),

        "date_issues": (
            date_issues
        ),

        "date_standardization": (
            date_standardization_report
        ),

        "numeric_issues": (
            numeric_issues
        ),

        "outlier_issues": (
            outlier_issues
        ),

        "business_issues": (
            business_issues
        ),

        "imputation_report": (
            imputation_report
        ),

        "reconstruction_report": (
            reconstruction_report
        ),

        "cleaning_report": (
            cleaning_report
        ),

        "preview": (
            preview_df
            .astype(object)
            .where(
                pd.notnull(preview_df),
                None
            )
            .to_dict(
                orient="records"
            )
        )
    }

    return df, report