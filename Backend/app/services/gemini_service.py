import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_response(prompt: str):
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text

def generate_sql(question: str):
    prompt = f"""
You are an expert SQL developer.

Convert the user's natural language question into SQL.

Database:
SQLite

Table: sales

Columns:
- id INTEGER
- customer_name TEXT
- product_name TEXT
- quantity INTEGER
- revenue REAL
- sale_date DATE

Rules:
- Return only the SQL query.
- Do not use markdown.
- Do not explain the query.
- Use SQLite-compatible SQL.

User question:
{question}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text.strip()

def generate_sql_from_question(
    question: str,
    table_name: str,
    schema_context: str
):
    """
    Generate a read-only SQL query from a user's
    natural-language question.
    """

    prompt = f"""
You are an expert SQL analyst.

You are working with a SQLite database.

Your job is to convert the user's natural-language
question into a SQL query.

DATABASE TABLE:
{table_name}

TABLE SCHEMA:
{schema_context}

USER QUESTION:
{question}

RULES:

1. Generate ONLY a SQL SELECT query.
2. WITH queries are also allowed when necessary.
3. Do NOT generate INSERT, UPDATE, DELETE, DROP,
   ALTER, CREATE, TRUNCATE, REPLACE, ATTACH,
   DETACH, or PRAGMA statements.
4. Use ONLY the table and columns provided above.
5. Do not invent columns.
6. Do not invent tables.
7. Use SQLite-compatible SQL.
8. For aggregations, use appropriate functions such as
   SUM, AVG, COUNT, MIN, and MAX.
9. For grouping questions, use GROUP BY.
10. For ranking questions, use ORDER BY.
11. Return ONLY the SQL query.
12. Do not use Markdown code fences.
13. Do not provide explanations.

SQL QUERY:
"""

    response = generate_response(prompt)

    return response.strip()