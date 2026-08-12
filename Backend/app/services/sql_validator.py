import re


# ============================================================
# ALLOWED SQL
# ============================================================

ALLOWED_STATEMENTS = (
    "SELECT",
    "WITH"
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
    "PRAGMA"
]


# ============================================================
# VALIDATE SQL
# ============================================================

def validate_sql(sql: str) -> dict:
    """
    Validate SQL before execution.

    The AI SQL Assistant currently allows
    read-only SQL queries only.
    """

    if not sql:

        return {
            "valid": False,
            "message": "SQL query is empty."
        }

    # --------------------------------------------------------
    # Clean SQL
    # --------------------------------------------------------

    cleaned_sql = sql.strip()

    # Remove trailing semicolon
    cleaned_sql = cleaned_sql.rstrip(";").strip()

    # --------------------------------------------------------
    # Check first SQL statement
    # --------------------------------------------------------

    first_word_match = re.match(
        r"^\s*([A-Za-z]+)",
        cleaned_sql
    )

    if not first_word_match:

        return {
            "valid": False,
            "message": "Unable to determine SQL statement type."
        }

    first_word = (
        first_word_match.group(1)
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
                "is not allowed. Only SELECT queries "
                "are permitted."
            )
        }

    # --------------------------------------------------------
    # Check blocked keywords
    # --------------------------------------------------------

    upper_sql = cleaned_sql.upper()

    for keyword in BLOCKED_KEYWORDS:

        pattern = rf"\b{keyword}\b"

        if re.search(
            pattern,
            upper_sql
        ):

            return {
                "valid": False,
                "message": (
                    f"Blocked SQL keyword detected: "
                    f"{keyword}"
                )
            }

    # --------------------------------------------------------
    # Check multiple statements
    # --------------------------------------------------------

    if ";" in cleaned_sql:

        return {
            "valid": False,
            "message": (
                "Multiple SQL statements are not allowed."
            )
        }

    # --------------------------------------------------------
    # SQL is valid
    # --------------------------------------------------------

    return {
        "valid": True,
        "message": "SQL query is valid.",
        "sql": cleaned_sql
    }
    
def clean_generated_sql(sql: str) -> str:
    """
    Clean SQL returned by the AI model.
    """

    if not sql:
        return ""

    sql = sql.strip()

    # Remove Markdown SQL code fences
    if sql.startswith("```sql"):
        sql = sql[6:]

    elif sql.startswith("```SQL"):
        sql = sql[6:]

    elif sql.startswith("```"):
        sql = sql[3:]

    if sql.endswith("```"):
        sql = sql[:-3]

    # Remove unnecessary whitespace
    sql = sql.strip()

    # Remove trailing semicolon
    sql = sql.rstrip(";").strip()

    return sql