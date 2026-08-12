from fastapi import (
    FastAPI,
    Depends,
    UploadFile,
    File,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

import os
import shutil
import tempfile
import pandas as pd
import json
import uuid


# ============================================================
# DATABASE
# ============================================================

from app.database.database import (
    Base,
    engine,
    get_db
)


# ============================================================
# TABLE MANAGER
# ============================================================

from app.database.table_manager import (
    generate_table_name,
    create_dataset_table
)


# ============================================================
# MODELS
# ============================================================

from app.models.query_history import QueryHistory
from app.models.dataset import DatasetMetadata


# ============================================================
# SCHEMAS
# ============================================================
from app.schemas.queries import (
    QueryCreate,
    SQLResponse,
    AskRequest
)

# ============================================================
# DATASET SERVICE
# ============================================================

from app.services.dataset_service import (
    get_dataset_by_id,
    check_table_exists,
    get_table_row_count,
    get_table_columns,
    get_table_preview,
    get_dataset_schema_context
)


# ============================================================
# GEMINI SERVICE
# ============================================================

from app.services.gemini_service import (
    generate_response,
    generate_sql_from_question
)


# ============================================================
# SQL SERVICE
# ============================================================

from app.services.sql_service import (
    execute_sql
)


# ============================================================
# ETL PIPELINE
# ============================================================

from app.etl.pipeline import (
    run_etl_pipeline
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI SQL Assistant API",
    version="1.0.0"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "message":
            "Welcome to the AI SQL Assistant API!"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():

    return {
        "status":
            "healthy",

        "message":
            "The API is running smoothly."
    }


# ============================================================
# DATASET INFORMATION
# ============================================================

@app.get("/datasets/{dataset_id}")
async def get_dataset_info(
    dataset_id: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find dataset metadata
    # --------------------------------------------------------

    dataset = get_dataset_by_id(
        db,
        dataset_id
    )

    if not dataset:

        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # --------------------------------------------------------
    # Check actual SQL table
    # --------------------------------------------------------

    table_exists = check_table_exists(
        engine,
        dataset.table_name
    )

    if not table_exists:

        raise HTTPException(
            status_code=404,
            detail="Dataset SQL table does not exist."
        )

    # --------------------------------------------------------
    # Get actual row count
    # --------------------------------------------------------

    row_count = get_table_row_count(
        engine,
        dataset.table_name
    )

    # --------------------------------------------------------
    # Get actual columns
    # --------------------------------------------------------

    columns = get_table_columns(
        engine,
        dataset.table_name
    )

    # --------------------------------------------------------
    # Return dataset information
    # --------------------------------------------------------

    return {

        "success":
            True,

        "dataset_id":
            dataset.dataset_id,

        "filename":
            dataset.filename,

        "table_name":
            dataset.table_name,

        "row_count":
            row_count,

        "column_count":
            len(columns),

        "columns":
            columns,

        "table_exists":
            table_exists
    }


# ============================================================
# DATASET PREVIEW
# ============================================================

@app.get("/datasets/{dataset_id}/preview")
async def dataset_preview(
    dataset_id: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find dataset metadata
    # --------------------------------------------------------

    dataset = get_dataset_by_id(
        db,
        dataset_id
    )

    if not dataset:

        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # --------------------------------------------------------
    # Check actual SQL table
    # --------------------------------------------------------

    table_exists = check_table_exists(
        engine,
        dataset.table_name
    )

    if not table_exists:

        raise HTTPException(
            status_code=404,
            detail="Dataset SQL table does not exist."
        )

    # --------------------------------------------------------
    # Get preview
    # --------------------------------------------------------

    preview = get_table_preview(
        engine,
        dataset.table_name,
        limit=5
    )

    # --------------------------------------------------------
    # Return preview
    # --------------------------------------------------------

    return {

        "success":
            True,

        "dataset_id":
            dataset.dataset_id,

        "table_name":
            dataset.table_name,

        "row_count":
            dataset.row_count,

        "preview":
            preview
    }


# ============================================================
# CREATE QUERY HISTORY
# ============================================================

@app.post("/queries")
def create_query(
    query: QueryCreate,
    db: Session = Depends(get_db)
):

    new_query = QueryHistory(
        question=query.question,
        generated_sql=query.generated_sql
    )

    db.add(
        new_query
    )

    db.commit()

    db.refresh(
        new_query
    )

    return {

        "id":
            new_query.id,

        "question":
            new_query.question,

        "generated_sql":
            new_query.generated_sql
    }


# ============================================================
# TEST GEMINI
# ============================================================

@app.get("/test-gemini")
async def test_gemini():

    response = generate_response(
        "Explain SQL in one sentence."
    )

    return {
        "response":
            response
    }


# ============================================================
# GENERATE SQL
# ============================================================

@app.post("/generate-sql")
async def generate_sql_query(
    request: SQLResponse
):

    # --------------------------------------------------------
    # NOTE:
    # This endpoint is kept for basic SQL generation testing.
    #
    # The real dataset-aware AI pipeline is /ask.
    # --------------------------------------------------------

    raise HTTPException(
        status_code=501,
        detail=(
            "Use the /ask endpoint for "
            "dataset-aware SQL generation."
        )
    )


# ============================================================
# UPLOAD DATASET + RUN ETL PIPELINE
# ============================================================

@app.post("/upload-data")
async def upload_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    allowed_extensions = [
        ".csv",
        ".xlsx"
    ]

    file_extension = os.path.splitext(
        file.filename
    )[1].lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,

            detail=(
                "Only CSV and Excel "
                "files are supported."
            )
        )

    # --------------------------------------------------------
    # Create temporary file
    # --------------------------------------------------------

    temp_file = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp:

            temp_file = temp.name

            shutil.copyfileobj(
                file.file,
                temp
            )

        # ----------------------------------------------------
        # Run complete ETL pipeline
        # ----------------------------------------------------

        df, report = run_etl_pipeline(
            temp_file
        )

        print(
            "DEBUG ETL completed:",
            df.shape
        )

        # ----------------------------------------------------
        # Generate unique dataset ID
        # ----------------------------------------------------

        dataset_id = (
            f"ds_{uuid.uuid4().hex[:8]}"
        )

        # ----------------------------------------------------
        # Generate SQL table name
        # ----------------------------------------------------

        table_name = generate_table_name(
            dataset_id
        )

        print(
            "DEBUG dataset_id:",
            dataset_id
        )

        print(
            "DEBUG table_name:",
            table_name
        )

        print(
            "DEBUG dataframe shape:",
            df.shape
        )

        # ----------------------------------------------------
        # Create dynamic SQL table
        #
        # IMPORTANT:
        # create_dataset_table() already uses df.to_sql()
        # and therefore inserts the DataFrame into the table.
        # We do NOT need insert_dataset() separately.
        # ----------------------------------------------------

        create_dataset_table(
            df,
            table_name,
            engine
        )

        print(
            "DEBUG: Dataset table created successfully"
        )

        # ----------------------------------------------------
        # Store column metadata
        # ----------------------------------------------------

        column_metadata = []

        for column in df.columns:

            column_metadata.append({

                "name":
                    column,

                "data_type":
                    str(df[column].dtype)
            })

        # ----------------------------------------------------
        # Create DatasetMetadata record
        # ----------------------------------------------------

        dataset_metadata = DatasetMetadata(

            dataset_id=
                dataset_id,

            filename=
                file.filename,

            table_name=
                table_name,

            row_count=
                len(df),

            column_count=
                len(df.columns),

            columns=
                json.dumps(column_metadata)
        )

        db.add(
            dataset_metadata
        )

        db.commit()

        db.refresh(
            dataset_metadata
        )

        # ----------------------------------------------------
        # Create preview
        # ----------------------------------------------------

        preview_df = (
            df.head(5)
            .astype(object)
        )

        preview_df = preview_df.where(
            pd.notnull(preview_df),
            None
        )

        preview = (
            preview_df
            .to_dict(
                orient="records"
            )
        )

        # ----------------------------------------------------
        # Dataset information
        # ----------------------------------------------------

        dataset_info = {

            "filename":
                file.filename,

            "rows":
                len(df),

            "columns":
                len(df.columns),

            "column_names":
                df.columns.tolist()
        }

        # ----------------------------------------------------
        # Return response
        # ----------------------------------------------------

        return {

            "success":
                True,

            "message":
                (
                    "Dataset uploaded and "
                    "ETL pipeline completed "
                    "successfully."
                ),

            "dataset_id":
                dataset_id,

            "dataset":
                dataset_info,

            "table_name":
                table_name,

            "cleaning_report":
                report.get(
                    "cleaning_report",
                    {}
                ),

            "category_issues":
                report.get(
                    "category_issues",
                    {}
                ),

            "missing_values":
                report.get(
                    "missing_values",
                    {}
                ),

            "date_issues":
                report.get(
                    "date_issues",
                    {}
                ),

            "numeric_issues":
                report.get(
                    "numeric_issues",
                    {}
                ),

            "outlier_issues":
                report.get(
                    "outlier_issues",
                    {}
                ),

            "business_issues":
                report.get(
                    "business_issues",
                    {}
                ),

            "imputation_report":
                report.get(
                    "imputation_report",
                    {}
                ),

            "reconstruction_report":
                report.get(
                    "reconstruction_report",
                    {}
                ),

            "preview":
                preview
        }

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        print(
            "UPLOAD ERROR:",
            str(error)
        )

        raise HTTPException(
            status_code=500,

            detail={

                "message":
                    "ETL pipeline failed.",

                "error":
                    str(error)
            }
        )

    finally:

        # ----------------------------------------------------
        # Delete temporary file
        # ----------------------------------------------------

        if (
            temp_file
            and os.path.exists(temp_file)
        ):

            os.remove(
                temp_file
            )


# ============================================================
# CLEAN DATA
# ============================================================

@app.post("/clean-data")
async def clean_data(
    file: UploadFile = File(...)
):

    """
    Runs the ETL pipeline without
    creating a SQL dataset table.
    """

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    allowed_extensions = [
        ".csv",
        ".xlsx"
    ]

    file_extension = os.path.splitext(
        file.filename
    )[1].lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,

            detail=(
                "Only CSV and Excel "
                "files are supported."
            )
        )

    temp_file = None

    try:

        # ----------------------------------------------------
        # Save temporary uploaded file
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp:

            temp_file = temp.name

            shutil.copyfileobj(
                file.file,
                temp
            )

        # ----------------------------------------------------
        # Run ETL
        # ----------------------------------------------------

        df, report = run_etl_pipeline(
            temp_file
        )

        # ----------------------------------------------------
        # Preview cleaned dataset
        # ----------------------------------------------------

        preview_df = (
            df.head(5)
            .astype(object)
        )

        preview_df = preview_df.where(
            pd.notnull(preview_df),
            None
        )

        preview = (
            preview_df
            .to_dict(
                orient="records"
            )
        )

        # ----------------------------------------------------
        # Return cleaning result
        # ----------------------------------------------------

        return {

            "success":
                True,

            "filename":
                file.filename,

            "dataset_shape": {

                "rows":
                    len(df),

                "columns":
                    len(df.columns)
            },

            "columns":
                df.columns.tolist(),

            "cleaning_report":
                report.get(
                    "cleaning_report",
                    {}
                ),

            "category_issues":
                report.get(
                    "category_issues",
                    {}
                ),

            "missing_values":
                report.get(
                    "missing_values",
                    {}
                ),

            "date_issues":
                report.get(
                    "date_issues",
                    {}
                ),

            "numeric_issues":
                report.get(
                    "numeric_issues",
                    {}
                ),

            "outlier_issues":
                report.get(
                    "outlier_issues",
                    {}
                ),

            "business_issues":
                report.get(
                    "business_issues",
                    {}
                ),

            "imputation_report":
                report.get(
                    "imputation_report",
                    {}
                ),

            "reconstruction_report":
                report.get(
                    "reconstruction_report",
                    {}
                ),

            "preview":
                preview
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,

            detail={

                "message":
                    "Data cleaning failed.",

                "error":
                    str(error)
            }
        )

    finally:

        if (
            temp_file
            and os.path.exists(temp_file)
        ):

            os.remove(
                temp_file
            )


# ============================================================
# ASK AI SQL ASSISTANT
# ============================================================

@app.post("/ask")
async def ask_ai(
    request: AskRequest,
    db: Session = Depends(get_db)
):

    dataset_id = request.dataset_id
    question = request.question

    # --------------------------------------------------------
    # Validate dataset_id
    # --------------------------------------------------------

    if not dataset_id:
        raise HTTPException(
            status_code=400,
            detail="dataset_id is required."
        )

    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    if not question:
        raise HTTPException(
            status_code=400,
            detail="question is required."
        )

    # --------------------------------------------------------
    # Find dataset metadata
    # --------------------------------------------------------

    dataset = get_dataset_by_id(
        db,
        dataset_id
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # --------------------------------------------------------
    # Check actual SQL table
    # --------------------------------------------------------

    table_exists = check_table_exists(
        engine,
        dataset.table_name
    )

    if not table_exists:
        raise HTTPException(
            status_code=404,
            detail="Dataset SQL table does not exist."
        )

    # --------------------------------------------------------
    # Get dataset schema
    # --------------------------------------------------------

    schema_context = get_dataset_schema_context(
        engine,
        dataset.table_name
    )

    # --------------------------------------------------------
    # Generate SQL using Gemini
    # --------------------------------------------------------

    generated_sql = generate_sql_from_question(
        question,
        dataset.table_name,
        schema_context
    )

    print(
        "DEBUG generated SQL:",
        generated_sql
    )

    # --------------------------------------------------------
    # Execute SQL safely
    # --------------------------------------------------------

    result = execute_sql(
        engine,
        generated_sql
    )

    # --------------------------------------------------------
    # Check SQL execution
    # --------------------------------------------------------

    if not result["success"]:

        raise HTTPException(
            status_code=400,

            detail={
                "message":
                    "SQL execution failed.",

                "error":
                    result["error"]
            }
        )

    # --------------------------------------------------------
    # SAVE QUERY HISTORY
    # --------------------------------------------------------

    query_history = QueryHistory(

        dataset_id=dataset_id,

        user_question=question,

        generated_sql=generated_sql
    )

    db.add(
        query_history
    )

    db.commit()

    db.refresh(
        query_history
    )

    print(
        "DEBUG query history saved:",
        query_history.id
    )

    # --------------------------------------------------------
    # Return AI SQL result
    # --------------------------------------------------------

    return {

        "success":
            True,

        "dataset_id":
            dataset_id,

        "question":
            question,

        "sql":
            generated_sql,

        "result": {

            "columns":
                result["columns"],

            "rows":
                result["rows"],

            "row_count":
                result["row_count"]
        },

        "query_history_id":
            query_history.id
    }
    
    
# ============================================================
# QUERY HISTORY
# ============================================================

@app.get("/datasets/{dataset_id}/history")
async def get_query_history(
    dataset_id: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Validate dataset
    # --------------------------------------------------------

    dataset = get_dataset_by_id(
        db,
        dataset_id
    )

    if not dataset:

        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # --------------------------------------------------------
    # Get query history for this dataset
    # --------------------------------------------------------

    history = (
        db.query(QueryHistory)
        .filter(
            QueryHistory.dataset_id == dataset_id
        )
        .order_by(
            QueryHistory.created_at.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # Format history
    # --------------------------------------------------------

    history_data = []

    for item in history:

        history_data.append({

            "id":
                item.id,

            "question":
                item.user_question,

            "generated_sql":
                item.generated_sql,

            "created_at":
                item.created_at
        })

    # --------------------------------------------------------
    # Return history
    # --------------------------------------------------------

    return {

        "success":
            True,

        "dataset_id":
            dataset_id,

        "count":
            len(history_data),

        "history":
            history_data
    }