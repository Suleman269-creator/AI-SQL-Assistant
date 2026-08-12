from app.database.database import engine

from app.services.dataset_service import (
    get_dataset_schema_context
)

from app.services.gemini_service import (
    generate_sql_from_question
)

from app.services.sql_validator import (
    clean_generated_sql
)

from app.services.sql_service import (
    execute_sql
)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_TABLE = "dataset_ds_2f2ea298"

QUESTION = "What are the total sales?"


print("================================")
print("FULL AI SQL PIPELINE TEST")
print("================================")


# ============================================================
# 1. GET DATASET SCHEMA
# ============================================================

schema_context = get_dataset_schema_context(
    engine,
    DATASET_TABLE
)

print("\n[1] Dataset schema loaded")


# ============================================================
# 2. GENERATE SQL USING GEMINI
# ============================================================

generated_sql = generate_sql_from_question(
    QUESTION,
    DATASET_TABLE,
    schema_context
)

print("\n[2] Gemini generated SQL:")
print(generated_sql)


# ============================================================
# 3. CLEAN GENERATED SQL
# ============================================================

cleaned_sql = clean_generated_sql(
    generated_sql
)

print("\n[3] Cleaned SQL:")
print(cleaned_sql)


# ============================================================
# 4. VALIDATE + EXECUTE SQL
# ============================================================

result = execute_sql(
    engine,
    cleaned_sql
)

print("\n[4] SQL execution result:")
print(result)


# ============================================================
# 5. FINAL RESULT
# ============================================================

if result["success"]:

    print("\n================================")
    print("AI SQL PIPELINE SUCCESSFUL")
    print("================================")

    print("\nQuestion:")
    print(QUESTION)

    print("\nGenerated SQL:")
    print(cleaned_sql)

    print("\nDatabase Result:")
    print(result["rows"])

else:

    print("\n================================")
    print("AI SQL PIPELINE FAILED")
    print("================================")

    print("\nError:")
    print(result["error"])