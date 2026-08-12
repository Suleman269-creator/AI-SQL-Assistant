from app.database.database import engine

from app.services.dataset_service import (
    get_dataset_schema_context
)


DATASET_TABLE = "dataset_ds_2f2ea298"


print("================================")
print("DATASET SCHEMA TEST")
print("================================")


schema = get_dataset_schema_context(
    engine,
    DATASET_TABLE
)


print("\nGenerated schema context:\n")

print(schema)


print("\n================================")
print("DATASET SCHEMA TEST COMPLETE")
print("================================")