from fastapi import FastAPI, Depends, UploadFile, File
import pandas as pd
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app.services.gemini_service import (generate_response, generate_sql)

from app.database.database import Base, engine, get_db
from app.models.query_history import QueryHistory
from app.models.dataset import DatasetMetadata
from app.schemas.queries import QueryCreate, SQLResponse
from app.services.gemini_service import generate_response
from app.etl.profiler import profile_data
from app.etl.cleaner import (
    clean_basic_data,
    detect_category_inconsistencies,
    analyze_missing_values,
    validate_date_columns,
    validate_numeric_columns,
    detect_outliers,
    validate_business_rules,
    impute_missing_values,
    standardize_date_columns,
    reconstruct_business_values
)

app = FastAPI(
    title="AI SQL Assistant API",
    version="1.0.0",
)


# Create database tables
Base.metadata.create_all(bind=engine)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI SQL Assistant API!"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "The API is running smoothly."
    }
    
@app.post("/queries")
def create_query(
    query: QueryCreate,
    db: Session = Depends(get_db)
):
    new_query = QueryHistory(
        question=query.question,
        generated_sql=query.generated_sql
    )

    db.add(new_query)
    db.commit()
    db.refresh(new_query)

    return {
        "id": new_query.id,
        "question": new_query.question,
        "generated_sql": new_query.generated_sql
    }
    
    
@app.get("/test-gemini")
async def test_gemini():
    response = generate_response("Explain SQL in one sentence.")
    
    return {
        "response": response
    }
    
@app.post("/generate-sql")
async def generate_sql_query(request: SQLResponse):
    sql = generate_sql(request.question)

    return {
        "question": request.question,
        "sql": sql
    }
    
@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):

    if file.filename.endswith(".csv"):
        df = pd.read_csv(file.file)

    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(file.file)

    else:
        return {
            "error": "Only CSV and Excel files are supported."
        }

    profile = profile_data(df)

    preview_df = df.head(5).copy()

    preview_df = preview_df.astype(object).where(
        pd.notnull(preview_df),
        None
    )

    preview = preview_df.to_dict(orient="records")

    return {
        "filename": file.filename,
        "profile": profile,
        "preview": preview
    }
    

@app.post("/clean-data")
async def clean_data(file: UploadFile = File(...)):

    # --------------------------------------------------
    # 0. Read uploaded file
    # --------------------------------------------------

    if file.filename.endswith(".csv"):
        df = pd.read_csv(file.file)

    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(file.file)

    else:
        return {
            "error": "Only CSV and Excel files are supported."
        }

    # --------------------------------------------------
    # 1. Basic cleaning
    # --------------------------------------------------

    cleaned_df, cleaning_report = clean_basic_data(df)

    # --------------------------------------------------
    # 2. Standardize date columns - 4.6.10
    # --------------------------------------------------

    standardized_df, date_standardization_report = (
        standardize_date_columns(cleaned_df)
    )

    # --------------------------------------------------
    # 3. Detect categorical inconsistencies
    # --------------------------------------------------

    category_issues = detect_category_inconsistencies(
        standardized_df
    )

    # --------------------------------------------------
    # 4. Analyze missing values
    # --------------------------------------------------

    missing_values = analyze_missing_values(
        standardized_df
    )

    # --------------------------------------------------
    # 5. Validate date columns
    # --------------------------------------------------

    date_issues = validate_date_columns(
        standardized_df
    )

    # --------------------------------------------------
    # 6. Validate ALL numeric columns
    # --------------------------------------------------

    numeric_issues = validate_numeric_columns(
        standardized_df
    )

    # --------------------------------------------------
    # 7. Detect outliers
    # --------------------------------------------------

    outlier_issues = detect_outliers(
        standardized_df
    )

    # --------------------------------------------------
    # 8. Validate business rules
    # --------------------------------------------------

    business_issues = validate_business_rules(
        standardized_df
    )

    # --------------------------------------------------
    # 9. Impute missing values
    # --------------------------------------------------

    imputed_df, imputation_report = (
        impute_missing_values(standardized_df)
    )
    
    # --------------------------------------------------
    # 10. Business-rule reconstruction - 4.6.11
    # --------------------------------------------------

    reconstructed_df, reconstruction_report = (
    reconstruct_business_values(imputed_df))

    # --------------------------------------------------
    # 10. Create preview
    # --------------------------------------------------

    preview_df = (
    imputed_df
    .head(5)
    .astype(object)
)

    preview_df = preview_df.where(
    pd.notnull(preview_df),
    None
)

    preview = preview_df.to_dict(
    orient="records"
)

    # --------------------------------------------------
    # 11. Return ETL quality report
    # --------------------------------------------------

    return {
    "filename": file.filename,

    "category_issues": category_issues,

    "missing_values": missing_values,

    "date_issues": date_issues,

    "numeric_issues": numeric_issues,

    "outlier_issues": outlier_issues,

    "business_issues": business_issues,

    "imputation_report": imputation_report,

    "cleaning_report": cleaning_report,

    "preview": preview
}