from app.database.database import engine

from app.services.sql_service import execute_sql


print("================================")
print("SQL SERVICE TEST")
print("================================")


# ============================================================
# TEST 1 — Total Sales
# ============================================================

sql_1 = """
SELECT SUM(sales) AS total_sales
FROM dataset_ds_2f2ea298
"""

result_1 = execute_sql(
    engine,
    sql_1
)

print("\nTEST 1 — TOTAL SALES")

print(result_1)


# ============================================================
# TEST 2 — Sales by Region
# ============================================================

sql_2 = """
SELECT
    region,
    SUM(sales) AS total_sales
FROM dataset_ds_2f2ea298
GROUP BY region
ORDER BY total_sales DESC
"""

result_2 = execute_sql(
    engine,
    sql_2
)

print("\nTEST 2 — SALES BY REGION")

print(result_2)


# ============================================================
# TEST 3 — Unsafe Query
# ============================================================

sql_3 = """
DROP TABLE dataset_ds_2f2ea298
"""

result_3 = execute_sql(
    engine,
    sql_3
)

print("\nTEST 3 — UNSAFE QUERY")

print(result_3)


print("\n================================")
print("SQL SERVICE TEST COMPLETE")
print("================================")