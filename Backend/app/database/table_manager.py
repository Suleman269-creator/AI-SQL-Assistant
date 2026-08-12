import re
import pandas as pd

from sqlalchemy import inspect


def generate_table_name(dataset_id: str) -> str:
    """
    Generate a safe SQL table name from dataset_id.
    """

    safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", dataset_id)

    return f"dataset_{safe_id}"


def table_exists(engine, table_name: str) -> bool:
    """
    Check whether a table already exists.
    """

    inspector = inspect(engine)

    return table_name in inspector.get_table_names()


def create_dataset_table(
    df: pd.DataFrame,
    table_name: str,
    engine
):
    """
    Create a SQL table dynamically from the DataFrame.
    """

    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False
    )

    return table_name


def insert_dataset(
    df: pd.DataFrame,
    table_name: str,
    engine
):
    """
    Insert dataset rows into an existing table.
    """

    df.to_sql(
        table_name,
        con=engine,
        if_exists="append",
        index=False
    )

    return len(df)