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