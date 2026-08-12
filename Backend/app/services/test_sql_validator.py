from app.services.sql_validator import validate_sql


print("================================")
print("SQL VALIDATOR TEST")
print("================================")


# ============================================================
# TEST 1 — Valid SELECT
# ============================================================

sql_1 = """
SELECT SUM(sales)
FROM dataset_ds_2f2ea298
"""

result_1 = validate_sql(sql_1)

print("\nTEST 1 — SELECT")
print(result_1)


# ============================================================
# TEST 2 — Valid SELECT with WHERE
# ============================================================

sql_2 = """
SELECT region, SUM(sales)
FROM dataset_ds_2f2ea298
GROUP BY region
"""

result_2 = validate_sql(sql_2)

print("\nTEST 2 — GROUP BY")
print(result_2)


# ============================================================
# TEST 3 — DROP should fail
# ============================================================

sql_3 = """
DROP TABLE dataset_ds_2f2ea298
"""

result_3 = validate_sql(sql_3)

print("\nTEST 3 — DROP")
print(result_3)


# ============================================================
# TEST 4 — DELETE should fail
# ============================================================

sql_4 = """
DELETE FROM dataset_ds_2f2ea298
"""

result_4 = validate_sql(sql_4)

print("\nTEST 4 — DELETE")
print(result_4)


# ============================================================
# TEST 5 — UPDATE should fail
# ============================================================

sql_5 = """
UPDATE dataset_ds_2f2ea298
SET sales = 0
"""

result_5 = validate_sql(sql_5)

print("\nTEST 5 — UPDATE")
print(result_5)


print("\n================================")
print("SQL VALIDATOR TEST COMPLETE")
print("================================")