from app.etl.pipeline import run_etl_pipeline


# ============================================================
# TEST DATASET
# ============================================================

file_path = r"C:\Users\Glow Computers\Downloads\MSN_TechWare_Raw_Sales_Data.xlsx"


# ============================================================
# RUN ETL PIPELINE
# ============================================================

df, report = run_etl_pipeline(file_path)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n================================")
print("ETL PIPELINE SUCCESSFUL")
print("================================")


print("\nDataset shape:")
print(df.shape)


print("\nColumns:")
print(df.columns.tolist())


print("\nCleaning report:")
print(report["cleaning_report"])


print("\nBusiness issues:")
print(report["business_issues"])


print("\nFirst 5 rows:")
print(df.head())