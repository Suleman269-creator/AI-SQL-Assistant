from sqlalchemy import text

from app.services.sql_validator import (
    validate_sql,
    clean_generated_sql
)


def execute_sql(
    engine,
    sql: str,
    allowed_table: str = None
):
    """
    Safely validate and execute a read-only SQL query.
    """

    # ========================================================
    # CLEAN AI SQL
    # ========================================================

    sql = clean_generated_sql(sql)

    # ========================================================
    # VALIDATE SQL
    # ========================================================

    validation = validate_sql(
        sql,
        allowed_table=allowed_table
    )

    if not validation["valid"]:

        return {

            "success":
                False,

            "error":
                validation["message"],

            "columns":
                [],

            "rows":
                [],

            "row_count":
                0
        }

    safe_sql = validation["sql"]

    # ========================================================
    # EXECUTE
    # ========================================================

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text(safe_sql)
            )

            rows = result.fetchall()

            columns = list(
                result.keys()
            )

            # =================================================
            # JSON FRIENDLY RESULT
            # =================================================

            formatted_rows = []

            for row in rows:

                record = {}

                for index, column in enumerate(columns):

                    value = row[index]

                    # Convert common SQLite/Python values
                    # into JSON-friendly values.

                    if hasattr(value, "isoformat"):

                        try:
                            value = value.isoformat()
                        except Exception:
                            pass

                    record[column] = value

                formatted_rows.append(
                    record
                )

            return {

                "success":
                    True,

                "columns":
                    columns,

                "rows":
                    formatted_rows,

                "row_count":
                    len(formatted_rows)
            }

    except Exception as error:

        return {

            "success":
                False,

            "error":
                str(error),

            "columns":
                [],

            "rows":
                [],

            "row_count":
                0
        }