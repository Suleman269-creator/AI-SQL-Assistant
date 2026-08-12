import os
import re
import json

from google import genai
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# GENERIC GEMINI RESPONSE
# ============================================================

def generate_response(prompt: str):
    """
    Generate a general-purpose Gemini response.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()


# ============================================================
# BASIC SQL GENERATION
# ============================================================

def generate_sql(question: str):
    """
    Generate SQL for the legacy/static sales example.
    """

    prompt = f"""
You are an expert SQL developer.

Convert the user's natural-language question into SQL.

Database:
SQLite

Table:
sales

Columns:
- id INTEGER
- customer_name TEXT
- product_name TEXT
- quantity INTEGER
- revenue REAL
- sale_date DATE

RULES:

1. Return ONLY SQL.
2. Use SQLite-compatible SQL.
3. Only generate SELECT statements.
4. WITH queries are allowed.
5. Do not generate INSERT, UPDATE, DELETE, DROP,
   ALTER, CREATE, TRUNCATE, REPLACE, ATTACH,
   DETACH, or PRAGMA.
6. Do not invent tables.
7. Do not invent columns.
8. Use appropriate aggregation functions.
9. Use GROUP BY for grouped analysis.
10. Use ORDER BY for ranking.
11. Use LIMIT for "top N" or "bottom N" questions.
12. Use clear aliases for calculated columns.
13. Do not use Markdown.
14. Do not explain the query.

USER QUESTION:
{question}

SQL:
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return clean_sql(response.text)


# ============================================================
# CLEAN SQL
# ============================================================

def clean_sql(sql: str) -> str:
    """
    Clean Gemini-generated SQL.

    Removes:
    - Markdown code fences
    - Leading/trailing whitespace
    - Unnecessary SQL labels
    """

    if not sql:
        return ""

    sql = sql.strip()

    # Remove ```sql
    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # Remove closing ```
    sql = re.sub(
        r"\s*```$",
        "",
        sql
    )

    # Remove accidental SQL: prefix
    sql = re.sub(
        r"^SQL\s*:\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    return sql.strip()


# ============================================================
# VALIDATE SQL
# ============================================================

def validate_generated_sql(
    sql: str,
    table_name: str,
    schema_context: str
):
    """
    Perform basic safety validation on
    Gemini-generated SQL.

    This is an additional backend safety layer.
    """

    if not sql:
        raise ValueError(
            "Gemini returned an empty SQL query."
        )

    cleaned_sql = clean_sql(sql)

    # --------------------------------------------------------
    # Remove trailing semicolon
    # --------------------------------------------------------

    cleaned_sql = cleaned_sql.rstrip(";").strip()

    # --------------------------------------------------------
    # Must start with SELECT or WITH
    # --------------------------------------------------------

    if not re.match(
        r"^(SELECT|WITH)\b",
        cleaned_sql,
        flags=re.IGNORECASE
    ):
        raise ValueError(
            "Generated SQL is not a read-only query."
        )

    # --------------------------------------------------------
    # Block dangerous SQL statements
    # --------------------------------------------------------

    forbidden = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "REPLACE",
        "ATTACH",
        "DETACH",
        "PRAGMA"
    ]

    for keyword in forbidden:

        if re.search(
            rf"\b{keyword}\b",
            cleaned_sql,
            flags=re.IGNORECASE
        ):
            raise ValueError(
                f"Unsafe SQL keyword detected: {keyword}"
            )

    # --------------------------------------------------------
    # Only allow the current dataset table
    # --------------------------------------------------------

    referenced_tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)",
        cleaned_sql,
        flags=re.IGNORECASE
    )

    for referenced_table in referenced_tables:

        if referenced_table != table_name:

            raise ValueError(
                "Generated SQL references an unauthorized table: "
                f"{referenced_table}"
            )

    return cleaned_sql


# ============================================================
# DATASET-AWARE SQL GENERATION
# ============================================================

def generate_sql_from_question(
    question: str,
    table_name: str,
    schema_context: str
):
    """
    Generate a read-only SQL query from a
    natural-language question.

    The query is generated specifically
    for the uploaded dataset.
    """

    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    if not table_name:
        raise ValueError(
            "Table name is required."
        )

    if not schema_context:
        raise ValueError(
            "Dataset schema is required."
        )

    prompt = f"""
You are an expert SQL analyst and data analyst.

You convert natural-language questions into
accurate SQLite SQL queries.

The user has uploaded ONE dataset.

============================================================
DATABASE
============================================================

Database:
SQLite

Allowed table:
{table_name}

============================================================
TABLE SCHEMA
============================================================

{schema_context}

============================================================
USER QUESTION
============================================================

{question}

============================================================
SQL GENERATION RULES
============================================================

1. Return ONLY the SQL query.

2. Do NOT return Markdown.

3. Do NOT use ```sql or ```.

4. Do NOT explain the query.

5. Generate ONLY a read-only SELECT query.

6. WITH queries are allowed when useful.

7. Use ONLY the provided table:
   {table_name}

8. Use ONLY columns present in the schema.

9. Never invent a column.

10. Never invent another table.

11. Never use:
    INSERT
    UPDATE
    DELETE
    DROP
    ALTER
    CREATE
    TRUNCATE
    REPLACE
    ATTACH
    DETACH
    PRAGMA

============================================================
ANALYTICAL RULES
============================================================

For total/sum questions:
    SUM(column)

For average questions:
    AVG(column)

For minimum questions:
    MIN(column)

For maximum questions:
    MAX(column)

For counting records:
    COUNT(*)

For counting unique values:
    COUNT(DISTINCT column)

For grouped questions:
    GROUP BY column

For ranking questions:
    ORDER BY calculated_value DESC

For lowest/bottom questions:
    ORDER BY calculated_value ASC

For "top N":
    ORDER BY value DESC
    LIMIT N

For "bottom N":
    ORDER BY value ASC
    LIMIT N

For calculated aggregations:
    ALWAYS use a meaningful alias.

Example:

SELECT
    city,
    SUM(sales) AS total_sales
FROM {table_name}
GROUP BY city
ORDER BY total_sales DESC;

For date-based questions:
    Use SQLite-compatible date functions.

For percentage calculations:
    Protect against division by zero.

For NULL values:
    Handle them appropriately when necessary.

For ranking:
    Make sure the ordering matches the user's request.

============================================================
IMPORTANT
============================================================

Understand the user's intent before generating SQL.

Examples:

Question:
"Which are the top 3 cities with the highest sales?"

Expected pattern:

SELECT
    city,
    SUM(sales) AS total_sales
FROM {table_name}
GROUP BY city
ORDER BY total_sales DESC
LIMIT 3;

Question:
"What city has the lowest sales?"

Expected pattern:

SELECT
    city,
    SUM(sales) AS total_sales
FROM {table_name}
GROUP BY city
ORDER BY total_sales ASC
LIMIT 1;

Question:
"What are total sales by city?"

Expected pattern:

SELECT
    city,
    SUM(sales) AS total_sales
FROM {table_name}
GROUP BY city
ORDER BY total_sales DESC;

============================================================
FINAL REQUIREMENT
============================================================

Return ONLY the final SQLite SQL query.

SQL:
"""

    response = generate_response(prompt)

    sql = clean_sql(response)

    sql = validate_generated_sql(
        sql,
        table_name,
        schema_context
    )

    return sql

# ============================================================
# AI RESULT INSIGHT
# ============================================================

def generate_result_insight(
    question: str,
    generated_sql: str,
    result: dict
):
    """
    Generate a concise natural-language explanation
    from the actual SQL result.
    """

    if not question:
        return "No question provided."

    if not result:
        return "No result was returned."

    columns = result.get("columns", [])
    rows = result.get("rows", [])

    try:
        result_json = json.dumps(
            rows,
            indent=2,
            default=str
        )
    except Exception:
        result_json = str(rows)

    prompt = f"""
You are a professional data analyst.

The user asked:

{question}

The SQL query was:

{generated_sql}

The SQL query returned these columns:

{columns}

The actual data returned was:

{result_json}

Give the user a short, clear business insight based ONLY
on the actual result.

Rules:
- Do not invent information.
- Do not change any numbers.
- Do not explain the SQL.
- Do not mention Gemini.
- Do not use Markdown.
- Keep the answer to 1 or 2 sentences.
- If there is one numeric result, clearly state it.
- Format large numbers with commas.

Example:

Question:
Total Sales

Result:
[
  {{
    "total_sales": 173169905
  }}
]

Answer:
Total sales are 173,169,905.
"""

    print("\n==============================")
    print("INSIGHT PROMPT")
    print(prompt)
    print("==============================\n")

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        print(
            "RAW INSIGHT RESPONSE:",
            response
        )

        insight = response.text

        if not insight:
            return "No insight was generated."

        return insight.strip()

    except Exception as error:

        print(
            "INSIGHT GENERATION ERROR:",
            repr(error)
        )

        return f"Insight generation failed: {str(error)}"