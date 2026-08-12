import pandas as pd

from app.database.database import engine
from app.database.table_manager import (
    generate_table_name,
    create_dataset_table,
    table_exists,
    insert_dataset
)


# Test dataset
df = pd.DataFrame({
    "name": ["Ali", "Sara", "Ahmed"],
    "sales": [1000, 2000, 1500],
    "profit": [200, 500, 300]
})


dataset_id = "ds_test123"

table_name = generate_table_name(dataset_id)

print("\nTable name:")
print(table_name)


# Create table
create_dataset_table(
    df,
    table_name,
    engine
)

print("\nTable created:")
print(table_exists(engine, table_name))


# Insert additional rows
new_df = pd.DataFrame({
    "name": ["Hamza"],
    "sales": [3000],
    "profit": [800]
})


inserted = insert_dataset(
    new_df,
    table_name,
    engine
)

print("\nRows inserted:")
print(inserted)


print("\nTable Manager test successful!")