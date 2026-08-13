from pathlib import Path

import pandas as pd

from .cleaner import clean_dataset


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load and clean a CSV or Excel dataset.

    Flow:
        File
        ↓
        Pandas DataFrame
        ↓
        cleaner.py
        ↓
        Cleaned DataFrame

    The returned DataFrame is always the cleaned dataset.
    """

    path = Path(file_path)

    # --------------------------------------------------------
    # Check file exists
    # --------------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )

    # --------------------------------------------------------
    # Check extension
    # --------------------------------------------------------

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: "
            f"{', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------

    if extension == ".csv":

        df = pd.read_csv(path)

    # --------------------------------------------------------
    # Load Excel
    # --------------------------------------------------------

    elif extension in {".xlsx", ".xls"}:

        df = pd.read_excel(path)

    else:
        raise ValueError(
            f"Unable to load file type: {extension}"
        )

    # --------------------------------------------------------
    # Validate DataFrame
    # --------------------------------------------------------

    if df.empty:
        raise ValueError(
            "The uploaded dataset is empty."
        )

    # --------------------------------------------------------
    # CLEAN DATASET
    # --------------------------------------------------------
    #
    # Use the cleaner.py pipeline.
    #
    # This handles:
    # - column normalization
    # - whitespace cleaning
    # - category standardization
    # - date standardization
    # - business-rule reconstruction
    # - duplicate removal
    # - empty rows/columns
    #
    # --------------------------------------------------------

    cleaned_df, cleaning_report = clean_dataset(
        df,
        standardize_categories=True,
        standardize_dates=True,
        impute_missing=False,
        reconstruct_business=True
    )

    # --------------------------------------------------------
    # Validate cleaned dataset
    # --------------------------------------------------------

    if cleaned_df.empty:
        raise ValueError(
            "Dataset became empty after cleaning."
        )

    return cleaned_df


# ============================================================
# LOAD DATASET WITH CLEANING REPORT
# ============================================================

def load_dataset_with_report(
    file_path: str
):
    """
    Load and clean a dataset while also returning
    the complete cleaning report.

    Returns:
        cleaned_df, cleaning_report
    """

    path = Path(file_path)

    # --------------------------------------------------------
    # Check file
    # --------------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )

    # --------------------------------------------------------
    # Check extension
    # --------------------------------------------------------

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: "
            f"{', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    if extension == ".csv":

        df = pd.read_csv(path)

    elif extension in {".xlsx", ".xls"}:

        df = pd.read_excel(path)

    else:

        raise ValueError(
            f"Unable to load file type: {extension}"
        )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if df.empty:
        raise ValueError(
            "The uploaded dataset is empty."
        )

    # --------------------------------------------------------
    # Clean
    # --------------------------------------------------------

    cleaned_df, cleaning_report = clean_dataset(
        df,
        standardize_categories=True,
        standardize_dates=True,
        impute_missing=False,
        reconstruct_business=True
    )

    # --------------------------------------------------------
    # Validate after cleaning
    # --------------------------------------------------------

    if cleaned_df.empty:
        raise ValueError(
            "Dataset became empty after cleaning."
        )

    return cleaned_df, cleaning_report


# ============================================================
# DATASET INFORMATION
# ============================================================

def get_dataset_metadata(
    df: pd.DataFrame
) -> dict:
    """
    Generate metadata for a loaded/cleaned dataset.
    """

    columns = []

    for column in df.columns:

        columns.append({
            "name": str(column),
            "data_type": str(
                df[column].dtype
            ),
            "missing_values": int(
                df[column].isna().sum()
            ),
            "unique_values": int(
                df[column].nunique()
            )
        })

    return {
        "row_count": int(
            len(df)
        ),
        "column_count": int(
            len(df.columns)
        ),
        "columns": columns
    }