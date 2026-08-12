from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


def get_dataset_by_id(
    db: Session,
    dataset_id: str
):
    """
    Get dataset metadata using dataset_id.
    """

    from app.models.dataset import DatasetMetadata

    return (
        db.query(DatasetMetadata)
        .filter(
            DatasetMetadata.dataset_id == dataset_id
        )
        .first()
    )


def check_table_exists(
    engine,
    table_name: str
) -> bool:
    """
    Check whether the dynamic dataset table exists.
    """

    inspector = inspect(engine)

    return table_name in inspector.get_table_names()


def get_table_row_count(
    engine,
    table_name: str
) -> int:
    """
    Get number of rows in a dataset table.
    """

    with engine.connect() as connection:

        result = connection.execute(
            text(
                f'SELECT COUNT(*) FROM "{table_name}"'
            )
        )

        return result.scalar()


def get_table_columns(
    engine,
    table_name: str
):
    """
    Get columns from a dynamic dataset table.
    """

    inspector = inspect(engine)

    columns = inspector.get_columns(
        table_name
    )

    return [
        {
            "name": column["name"],
            "type": str(column["type"])
        }
        for column in columns
    ]
    
    
def get_table_preview(
    engine,
    table_name: str,
    limit: int = 5
):
    """
    Get preview rows from a dynamic dataset table.
    """

    with engine.connect() as connection:

        result = connection.execute(
            text(
                f'SELECT * FROM "{table_name}" LIMIT :limit'
            ),
            {
                "limit": limit
            }
        )

        rows = result.fetchall()

        columns = result.keys()

        return [
            dict(zip(columns, row))
            for row in rows
        ]
        
def get_dataset_schema_context(
    engine,
    table_name: str
):
    """
    Build a schema description that can be
    provided to the AI model.
    """

    columns = get_table_columns(
        engine,
        table_name
    )

    schema_lines = []

    for column in columns:

        schema_lines.append(
            f"- {column['name']}: {column['type']}"
        )

    return "\n".join(schema_lines)