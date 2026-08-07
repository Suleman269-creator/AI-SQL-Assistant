import pandas as pd


def profile_data(df: pd.DataFrame):

    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_details": []
    }

    for column in df.columns:

        missing = int(df[column].isna().sum())
        unique = int(df[column].nunique())

        profile["column_details"].append({
            "column": str(column),
            "data_type": str(df[column].dtype),
            "missing": missing,
            "missing_percentage": round(
                (missing / len(df)) * 100, 2
            ) if len(df) > 0 else 0,
            "unique_values": unique
        })

    profile["duplicate_rows"] = int(df.duplicated().sum())

    return profile