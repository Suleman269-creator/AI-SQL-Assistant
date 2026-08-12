from app.database.database import engine

from app.services.dataset_service import (
    get_dataset_schema_context
)

from app.services.gemini_service import (
    generate_sql_from_question
)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_TABLE = "dataset_ds_2f2ea298"


# ============================================================
# GET DATASET SCHEMA
# ============================================================

schema_context = get_dataset_schema_context(
    engine,
    DATASET_TABLE
)


# ============================================================
# TEST QUESTION
# ============================================================

question = "What are the total sales?"


# ============================================================
# GENERATE SQL
# ============================================================

sql = generate_sql_from_question(
    question,
    DATASET_TABLE,
    schema_context
)


# ============================================================
# DISPLAY RESULT
# ============================================================

print("================================")
print("GEMINI SQL GENERATION TEST")
print("================================")

print("\nQuestion:")
print(question)

print("\nGenerated SQL:")
print(sql)

print("\n================================")
print("TEST COMPLETE")
print("================================")