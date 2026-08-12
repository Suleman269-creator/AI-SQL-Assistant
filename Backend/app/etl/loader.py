from pathlib import Path

import pandas as pd


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
    Load a CSV or Excel dataset into a pandas DataFrame.

    The function does not assume any specific columns.
    Therefore, different datasets can be uploaded safely.
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
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
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
        # This should never happen because of the
        # extension validation above.
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

    return df


# ============================================================
# DATASET INFORMATION
# ============================================================

def get_dataset_metadata(df: pd.DataFrame) -> dict:
    """
    Generate metadata for any loaded dataset.

    This function does not require specific columns such as
    sales, quantity, profit, etc.
    """

    columns = []

    for column in df.columns:

        columns.append({
            "name": str(column),
            "data_type": str(df[column].dtype),
            "missing_values": int(
                df[column].isna().sum()
            ),
            "unique_values": int(
                df[column].nunique()
            )
        })

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": columns
    }
    
