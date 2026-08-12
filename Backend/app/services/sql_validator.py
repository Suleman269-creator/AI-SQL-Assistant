import re


# ============================================================
# ALLOWED SQL
# ============================================================

ALLOWED_STATEMENTS = (
    "SELECT",
    "WITH",
)


# ============================================================
# BLOCKED SQL KEYWORDS
# ============================================================

BLOCKED_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
]


# ============================================================
# CLEAN GENERATED SQL
# ============================================================

def clean_generated_sql(sql: str) -> str:
    """
    Clean SQL returned by the AI model.
    """

    if not sql:
        return ""

    sql = sql.strip()

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    sql = re.sub(
        r"^```(?:sql|SQL)?\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = re.sub(
        r"\s*```$",
        "",
        sql,
    )

    # --------------------------------------------------------
    # Remove trailing semicolon
    # --------------------------------------------------------

    sql = sql.rstrip(";").strip()

    return sql


# ============================================================
# REMOVE SQL COMMENTS
# ============================================================

def remove_sql_comments(sql: str) -> str:
    """
    Remove SQL comments before validation.

    Supports:
        -- comment
        /* comment */
    """

    # Remove -- comments
    sql = re.sub(
        r"--[^\n\r]*",
        "",
        sql,
    )

    # Remove /* ... */ comments
    sql = re.sub(
        r"/\*.*?\*/",
        "",
        sql,
        flags=re.DOTALL,
    )

    return sql.strip()


# ============================================================
# VALIDATE SQL
# ============================================================

def validate_sql(
    sql: str,
    allowed_table: str = None
) -> dict:
    """
    Validate AI-generated SQL before execution.

    Only read-only SELECT / WITH queries are allowed.
    """

    # --------------------------------------------------------
    # Empty SQL
    # --------------------------------------------------------

    if not sql:

        return {
            "valid": False,
            "message": "SQL query is empty.",
        }

    # --------------------------------------------------------
    # Clean SQL
    # --------------------------------------------------------

    cleaned_sql = clean_generated_sql(sql)

    if not cleaned_sql:

        return {
            "valid": False,
            "message": "SQL query is empty after cleaning.",
        }

    # --------------------------------------------------------
    # Remove comments for security validation
    # --------------------------------------------------------

    validation_sql = remove_sql_comments(
        cleaned_sql
    )

    if not validation_sql:

        return {
            "valid": False,
            "message": "SQL query contains no executable SQL.",
        }

    # --------------------------------------------------------
    # Multiple statements
    # --------------------------------------------------------

    if ";" in validation_sql:

        return {
            "valid": False,
            "message": (
                "Multiple SQL statements are not allowed."
            ),
        }

    # --------------------------------------------------------
    # Check first SQL keyword
    # --------------------------------------------------------

    first_word_match = re.match(
        r"^\s*([A-Za-z]+)",
        validation_sql,
    )

    if not first_word_match:

        return {
            "valid": False,
            "message": (
                "Unable to determine SQL statement type."
            ),
        }

    first_word = (
        first_word_match
        .group(1)
        .upper()
    )

    # --------------------------------------------------------
    # Only SELECT / WITH allowed
    # --------------------------------------------------------

    if first_word not in ALLOWED_STATEMENTS:

        return {
            "valid": False,
            "message": (
                f"SQL statement '{first_word}' "
                "is not allowed. Only SELECT "
                "and WITH queries are permitted."
            ),
        }

    # --------------------------------------------------------
    # Check blocked keywords
    # --------------------------------------------------------

    upper_sql = validation_sql.upper()

    for keyword in BLOCKED_KEYWORDS:

        pattern = rf"\b{keyword}\b"

        if re.search(
            pattern,
            upper_sql,
        ):

            return {
                "valid": False,
                "message": (
                    f"Blocked SQL keyword detected: "
                    f"{keyword}"
                ),
            }
            
            
        # --------------------------------------------------------
        # Check referenced tables
        # --------------------------------------------------------

        if allowed_table: referenced_tables = re.findall(
            r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)",
            cleaned_sql,
            flags=re.IGNORECASE
        )

        for referenced_table in referenced_tables:

            if referenced_table.lower() != allowed_table.lower():

                return {
                    "valid": False,
                    "message": (
                        "Unauthorized table detected: "
                        f"{referenced_table}"
                    )
                }

    # --------------------------------------------------------
    # Protect against SQLite dangerous functions
    # --------------------------------------------------------

    blocked_functions = [
        "LOAD_EXTENSION",
    ]

    for function in blocked_functions:

        pattern = rf"\b{function}\s*\("

        if re.search(
            pattern,
            upper_sql,
        ):

            return {
                "valid": False,
                "message": (
                    f"Blocked SQL function detected: "
                    f"{function}"
                ),
            }

    # --------------------------------------------------------
    # Verify requested dataset table
    # --------------------------------------------------------

    if allowed_table:

        table_pattern = rf"\b{re.escape(allowed_table)}\b"

        if not re.search(
            table_pattern,
            validation_sql,
            flags=re.IGNORECASE,
        ):

            return {
                "valid": False,
                "message": (
                    "Generated SQL does not reference "
                    "the active dataset table."
                ),
            }

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    return {
        "valid": True,
        "message": "SQL query is valid.",
        "sql": cleaned_sql,
    }