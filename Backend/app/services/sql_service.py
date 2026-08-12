from sqlalchemy import text

from app.services.sql_validator import (
    validate_sql,
    clean_generated_sql
)


def execute_sql(
    engine,
    sql: str
):
    """
    Safely validate and execute a read-only SQL query.
    """

    # ========================================================
    # Clean AI-generated SQL
    # ========================================================

    sql = clean_generated_sql(sql)

    # ========================================================
    # Validate SQL
    # ========================================================

    validation = validate_sql(sql)

    if not validation["valid"]:

        return {
            "success": False,
            "error": validation["message"],
            "columns": [],
            "rows": []
        }

    # Use the cleaned SQL returned by validator
    safe_sql = validation["sql"]

    # ========================================================
    # 2. Execute SQL
    # ========================================================

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text(safe_sql)
            )

            rows = result.fetchall()

            columns = result.keys()

            # =================================================
            # Convert result to JSON-friendly structure
            # =================================================

            return {
                "success": True,

                "columns":
                    list(columns),

                "rows": [
                    dict(zip(columns, row))
                    for row in rows
                ],

                "row_count":
                    len(rows)
            }

    except Exception as error:

        return {
            "success": False,

            "error":
                str(error),

            "columns": [],

            "rows": []
        }