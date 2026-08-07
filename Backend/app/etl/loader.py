import pandas as pd
from pathlib import Path


def load_dataset(file_path: str) -> pd.DataFrame:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    if extension == ".csv":

        df = pd.read_csv(file_path)

    elif extension in [".xlsx", ".xls"]:

        df = pd.read_excel(file_path)

    else:

        raise ValueError(
            "Unsupported file type. "
            "Only CSV and Excel files are supported."
        )

    if df.empty:

        raise ValueError(
            "The uploaded dataset is empty."
        )

    return df