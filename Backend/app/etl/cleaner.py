import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOLERANCE = 1.0

DATE_KEYWORDS = [
    "date",
    "datetime",
    "timestamp",
    "created_at",
    "updated_at",
    "modified_at",
    "ordered_at",
    "order_date",
    "purchase_date",
    "transaction_date",
    "invoice_date",
    "shipment_date",
    "delivery_date",
    "dob",
    "birth_date",
]

PROTECTED_TEXT_KEYWORDS = [
    "email",
    "e_mail",
    "url",
    "website",
    "phone",
    "mobile",
    "telephone",
    "password",
    "username",
    "user_name",
    "customer_id",
    "client_id",
    "employee_id",
    "student_id",
    "product_id",
    "order_id",
    "transaction_id",
    "invoice_id",
    "id",
    "code",
    "sku",
    "zip",
    "postal",
]


# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(value: Any) -> Any:
    """
    Convert pandas/numpy values into JSON-safe Python values.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, (np.ndarray, list, tuple)):
        return [
            safe_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key): safe_value(val)
            for key, val in value.items()
        }

    return value


# ============================================================
# SAFE COLUMN NAME NORMALIZATION
# ============================================================

def normalize_column_name(column: Any) -> str:
    """
    Convert arbitrary column names into safe snake_case names.

    Examples:
        Order ID       -> order_id
        Customer Name  -> customer_name
        Total Sales ($) -> total_sales
    """

    column = str(column).strip().lower()

    column = re.sub(
        r"[^a-z0-9]+",
        "_",
        column
    )

    column = re.sub(
        r"_+",
        "_",
        column
    )

    column = column.strip("_")

    return column or "unnamed_column"


def make_unique_columns(
    columns
) -> List[str]:
    """
    Normalize column names and ensure uniqueness.
    """

    result = []
    counts = {}

    for column in columns:

        base = normalize_column_name(
            column
        )

        if base not in counts:

            counts[base] = 0
            result.append(base)

        else:

            counts[base] += 1

            result.append(
                f"{base}_{counts[base]}"
            )

    return result


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text_values(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean unnecessary whitespace from text columns.

    Capitalization is intentionally preserved.
    """

    df = df.copy()

    text_columns = df.select_dtypes(
        include=[
            "object",
            "string"
        ]
    ).columns

    for column in text_columns:

        df[column] = df[column].apply(
            lambda value:
                re.sub(
                    r"\s+",
                    " ",
                    value
                ).strip()
                if isinstance(
                    value,
                    str
                )
                else value
        )

    return df


# ============================================================
# BASIC DATA CLEANING
# ============================================================

def clean_basic_data(
    df: pd.DataFrame
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any]
]:
    """
    Perform safe dataset-independent cleaning.

    Operations:
        1. Validate DataFrame
        2. Normalize column names
        3. Remove completely empty columns
        4. Remove completely empty rows
        5. Remove exact duplicate rows
        6. Clean whitespace
    """

    if df is None:
        raise ValueError(
            "Input dataframe cannot be None."
        )

    if not isinstance(
        df,
        pd.DataFrame
    ):
        raise TypeError(
            "clean_basic_data() expects "
            "a pandas DataFrame."
        )

    df = df.copy()

    original_rows = len(df)
    original_columns = len(
        df.columns
    )

    original_column_names = list(
        df.columns
    )

    normalized_columns = (
        make_unique_columns(
            original_column_names
        )
    )

    df.columns = normalized_columns

    # --------------------------------------------------------
    # Empty columns
    # --------------------------------------------------------

    empty_columns = [
        column
        for column in df.columns
        if df[column].isna().all()
    ]

    if empty_columns:

        df = df.drop(
            columns=empty_columns
        )

    # --------------------------------------------------------
    # Empty rows
    # --------------------------------------------------------

    empty_rows_before = int(
        df.isna()
        .all(axis=1)
        .sum()
    )

    df = df.dropna(
        axis=0,
        how="all"
    )

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    duplicate_count = int(
        df.duplicated().sum()
    )

    df = (
        df.drop_duplicates(
            keep="first"
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Text cleaning
    # --------------------------------------------------------

    df = clean_text_values(df)

    return df, {
        "original_rows": original_rows,
        "original_columns": original_columns,
        "empty_columns_removed": len(
            empty_columns
        ),
        "empty_column_names": (
            empty_columns
        ),
        "empty_rows_removed": (
            empty_rows_before
        ),
        "duplicate_rows_removed": (
            duplicate_count
        ),
        "rows_after_cleaning": len(df),
        "columns_after_cleaning": len(
            df.columns
        ),
        "column_mapping": {
            str(old): new
            for old, new in zip(
                original_column_names,
                normalized_columns
            )
        }
    }


# ============================================================
# IDENTIFIER DETECTION
# ============================================================

def is_identifier_column(
    column: str
) -> bool:
    """
    Detect columns that should generally not be
    treated as ordinary numeric/category fields.
    """

    column = str(column).lower().strip()

    exact_identifiers = {
        "id",
        "code",
        "sku",
        "zip",
        "postal",
        "phone",
        "mobile"
    }

    if column in exact_identifiers:
        return True

    identifier_keywords = [
        "_id",
        "id_",
        "code",
        "sku",
        "zip",
        "postal",
        "phone",
        "mobile",
        "account_number",
        "reference",
        "ref"
    ]

    return any(
        keyword in column
        for keyword in identifier_keywords
    )


# ============================================================
# DATE COLUMN DETECTION
# ============================================================

def looks_like_date_column(
    column: str
) -> bool:

    column = str(
        column
    ).lower()

    return any(
        keyword in column
        for keyword in DATE_KEYWORDS
    )


# ============================================================
# COLUMN TYPE DETECTION
# ============================================================

def detect_column_types(
    df: pd.DataFrame,
    numeric_threshold: float = 0.90,
    date_threshold: float = 0.80
) -> Dict[str, str]:
    """
    Detect likely semantic data types.

    Possible values:
        numeric
        datetime
        categorical
        text
        boolean
        empty
    """

    result = {}

    for column in df.columns:

        series = df[column]

        if series.dropna().empty:

            result[column] = "empty"
            continue

        # Boolean
        if pd.api.types.is_bool_dtype(
            series
        ):

            result[column] = "boolean"
            continue

        # Existing numeric
        if pd.api.types.is_numeric_dtype(
            series
        ):

            result[column] = "numeric"
            continue

        # Existing datetime
        if pd.api.types.is_datetime64_any_dtype(
            series
        ):

            result[column] = "datetime"
            continue

        non_null = series.dropna()

        # ----------------------------------------------------
        # Numeric strings
        # ----------------------------------------------------

        numeric_converted = pd.to_numeric(
            non_null,
            errors="coerce"
        )

        if (
            len(non_null) > 0
            and
            numeric_converted.notna().mean()
            >= numeric_threshold
            and
            not is_identifier_column(column)
        ):

            result[column] = "numeric"
            continue

        # ----------------------------------------------------
        # Dates
        # ----------------------------------------------------

        date_converted = pd.to_datetime(
            non_null,
            errors="coerce",
            format="mixed"
        )

        if (
            len(non_null) > 0
            and
            date_converted.notna().mean()
            >= date_threshold
            and
            looks_like_date_column(column)
        ):

            result[column] = "datetime"
            continue

        # ----------------------------------------------------
        # Categorical / text
        # ----------------------------------------------------

        unique_ratio = (
            non_null.nunique()
            / len(non_null)
            if len(non_null) > 0
            else 1
        )

        if (
            non_null.nunique() <= 50
            or unique_ratio <= 0.05
        ):

            result[column] = "categorical"

        else:

            result[column] = "text"

    return result


# ============================================================
# CATEGORY INCONSISTENCY DETECTION
# ============================================================

def detect_category_inconsistencies(
    df: pd.DataFrame,
    max_unique_values: int = 50
) -> Dict[str, Any]:
    """
    Detect values that differ only by case or whitespace.

    Example:

        Karachi
        karachi
        KARACHI

    are detected as one inconsistent group.
    """

    issues = {}

    categorical_columns = (
        df.select_dtypes(
            include=[
                "object",
                "string",
                "category"
            ]
        ).columns
    )

    for column in categorical_columns:

        if is_identifier_column(column):
            continue

        values = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        if values.empty:
            continue

        if values.nunique() > max_unique_values:
            continue

        normalized = (
            values
            .str.casefold()
            .str.replace(
                r"\s+",
                " ",
                regex=True
            )
        )

        groups = {}

        for original, normalized_value in zip(
            values,
            normalized
        ):

            groups.setdefault(
                normalized_value,
                set()
            ).add(original)

        inconsistent = {
            key: sorted(
                list(variants)
            )
            for key, variants
            in groups.items()
            if len(variants) > 1
        }

        if inconsistent:

            issues[column] = (
                inconsistent
            )

    return issues


# ============================================================
# CATEGORY STANDARDIZATION
# ============================================================

def standardize_category_values(
    df: pd.DataFrame
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any]
]:
    """
    Standardize categorical/text values using the
    most frequent representation as canonical value.

    Does not blindly title-case values.
    """

    df = df.copy()

    report = {}

    categorical_columns = (
        df.select_dtypes(
            include=[
                "object",
                "category",
                "string"
            ]
        ).columns
    )

    for column in categorical_columns:

        if is_identifier_column(column):
            continue

        cleaned = (
            df[column]
            .astype("string")
            .str.strip()
            .str.replace(
                r"\s+",
                " ",
                regex=True
            )
        )

        normalization_key = (
            cleaned.str.casefold()
        )

        temp = pd.DataFrame({
            "cleaned": cleaned,
            "key": normalization_key
        })

        temp = temp.dropna(
            subset=["key"]
        )

        canonical_map = {}

        for key, group in temp.groupby(
            "key",
            sort=False
        ):

            value_counts = (
                group["cleaned"]
                .value_counts()
            )

            if value_counts.empty:
                continue

            canonical_map[key] = (
                value_counts.index[0]
            )

        standardized = (
            normalization_key
            .map(canonical_map)
            .astype("string")
        )

        changed_mask = (
            cleaned.fillna("__NULL__")
            != standardized.fillna(
                "__NULL__"
            )
        )

        changed_count = int(
            changed_mask.sum()
        )

        variants = {}

        for key, group in temp.groupby(
            "key",
            sort=False
        ):

            unique_values = (
                group["cleaned"]
                .dropna()
                .unique()
                .tolist()
            )

            if len(unique_values) > 1:

                variants[key] = {
                    "original_variants": (
                        unique_values
                    ),
                    "standardized_value": (
                        canonical_map.get(key)
                    )
                }

        df[column] = standardized

        if changed_count > 0:

            report[column] = {
                "values_standardized": (
                    changed_count
                ),
                "category_groups_merged": (
                    len(variants)
                ),
                "variants": variants,
                "method": (
                    "Whitespace normalization + "
                    "case-insensitive canonicalization "
                    "using most frequent representation"
                )
            }

    return df, report


# ============================================================
# GENDER STANDARDIZATION
# ============================================================

def standardize_gender_values(
    df: pd.DataFrame
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any]
]:
    """
    Standardize obvious gender/sex columns.
    """

    df = df.copy()

    report = {}

    gender_columns = [
        column
        for column in df.columns
        if column.lower()
        in {
            "gender",
            "sex"
        }
    ]

    gender_mapping = {

        "f": "Female",
        "female": "Female",
        "woman": "Female",
        "women": "Female",

        "m": "Male",
        "male": "Male",
        "man": "Male",
        "men": "Male",

        "non-binary": "Non-binary",
        "nonbinary": "Non-binary",
        "non binary": "Non-binary",
        "nb": "Non-binary",

        "other": "Other",
        "unknown": "Unknown",
        "prefer not to say":
            "Prefer not to say"
    }

    for column in gender_columns:

        original = df[column].copy()

        cleaned = (
            df[column]
            .astype("string")
            .str.strip()
            .str.casefold()
        )

        standardized = cleaned.map(
            gender_mapping
        )

        standardized = (
            standardized.fillna(
                df[column]
                .astype("string")
                .str.strip()
            )
        )

        changed_mask = (
            original
            .astype("string")
            .fillna("__NULL__")
            !=
            standardized
            .fillna("__NULL__")
        )

        changed_count = int(
            changed_mask.sum()
        )

        if changed_count > 0:

            changes = {}

            for index in df.index[
                changed_mask
            ]:

                old_value = safe_value(
                    original.loc[index]
                )

                new_value = safe_value(
                    standardized.loc[index]
                )

                key = str(old_value)

                if key not in changes:

                    changes[key] = {
                        "standardized_value":
                            new_value,
                        "count": 0
                    }

                changes[key]["count"] += 1

            report[column] = {
                "values_standardized":
                    changed_count,
                "changes": changes,
                "method":
                    "semantic gender normalization"
            }

        df[column] = standardized

    return df, report


# ============================================================
# MISSING VALUE ANALYSIS
# ============================================================

def analyze_missing_values(
    df: pd.DataFrame
) -> Dict[str, Any]:

    missing_report = {}

    total_rows = len(df)

    if total_rows == 0:
        return missing_report

    for column in df.columns:

        missing_count = int(
            df[column].isna().sum()
        )

        if missing_count == 0:
            continue

        missing_percentage = round(
            (
                missing_count
                / total_rows
            ) * 100,
            2
        )

        missing_report[column] = {
            "missing_count":
                missing_count,
            "missing_percentage":
                missing_percentage,
            "data_type":
                str(df[column].dtype)
        }

    return missing_report


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_date_columns(
    df: pd.DataFrame
) -> Dict[str, Any]:

    date_report = {}

    for column in df.columns:

        if not looks_like_date_column(
            column
        ):
            continue

        non_null = df[column].notna()

        if not non_null.any():
            continue

        converted = pd.to_datetime(
            df[column],
            errors="coerce",
            format="mixed"
        )

        invalid_mask = (
            non_null
            & converted.isna()
        )

        invalid_count = int(
            invalid_mask.sum()
        )

        date_report[column] = {
            "invalid_count":
                invalid_count,
            "invalid_percentage":
                round(
                    (
                        invalid_count
                        / len(df)
                    ) * 100,
                    2
                )
                if len(df) > 0
                else 0,
            "valid_count":
                int(
                    converted.notna().sum()
                )
        }

    return date_report


# ============================================================
# DATE STANDARDIZATION
# ============================================================

def standardize_date_columns(
    df: pd.DataFrame
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any]
]:

    df = df.copy()

    report = {}

    for column in df.columns:

        if not looks_like_date_column(
            column
        ):
            continue

        original_non_null = int(
            df[column].notna().sum()
        )

        if original_non_null == 0:
            continue

        converted = pd.to_datetime(
            df[column],
            errors="coerce",
            format="mixed"
        )

        valid_count = int(
            converted.notna().sum()
        )

        invalid_count = (
            original_non_null
            - valid_count
        )

        validity_ratio = (
            valid_count
            / original_non_null
        )

        if validity_ratio >= 0.80:

            df[column] = (
                converted
                .dt.strftime("%Y-%m-%d")
            )

            df.loc[
                converted.isna(),
                column
            ] = None

            report[column] = {
                "valid_dates":
                    valid_count,
                "invalid_dates":
                    invalid_count,
                "standard_format":
                    "YYYY-MM-DD"
            }

        else:

            report[column] = {
                "valid_dates":
                    valid_count,
                "invalid_dates":
                    invalid_count,
                "standard_format":
                    "not_changed",
                "reason":
                    "Too many invalid values "
                    "to safely standardize"
            }

    return df, report


# ============================================================
# NUMERIC COLUMN DETECTION
# ============================================================

def get_numeric_columns(
    df: pd.DataFrame
) -> List[str]:

    columns = []

    for column in df.columns:

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            if not is_identifier_column(
                column
            ):
                columns.append(column)

            continue

        if is_identifier_column(
            column
        ):
            continue

        values = df[column].dropna()

        if values.empty:
            continue

        converted = pd.to_numeric(
            values,
            errors="coerce"
        )

        if (
            converted.notna().mean()
            >= 0.90
        ):

            columns.append(column)

    return columns


# ============================================================
# NUMERIC VALIDATION
# ============================================================

def validate_numeric_columns(
    df: pd.DataFrame
) -> Dict[str, Any]:

    numeric_report = {}

    numeric_columns = (
        get_numeric_columns(df)
    )

    for column in numeric_columns:

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        valid_values = values.dropna()

        numeric_report[column] = {
            "data_type":
                str(df[column].dtype),

            "minimum":
                safe_value(
                    valid_values.min()
                )
                if not valid_values.empty
                else None,

            "maximum":
                safe_value(
                    valid_values.max()
                )
                if not valid_values.empty
                else None,

            "mean":
                safe_value(
                    valid_values.mean()
                )
                if not valid_values.empty
                else None,

            "negative_values":
                int(
                    (values < 0).sum()
                ),

            "zero_values":
                int(
                    (values == 0).sum()
                ),

            "missing_values":
                int(
                    values.isna().sum()
                )
        }

    return numeric_report


# ============================================================
# OUTLIER DETECTION
# ============================================================

def detect_outliers(
    df: pd.DataFrame,
    minimum_values: int = 4
) -> Dict[str, Any]:

    outlier_report = {}

    numeric_columns = (
        get_numeric_columns(df)
    )

    for column in numeric_columns:

        values = (
            pd.to_numeric(
                df[column],
                errors="coerce"
            )
            .dropna()
        )

        if len(values) < minimum_values:
            continue

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = (
            q1 - 1.5 * iqr
        )

        upper_bound = (
            q3 + 1.5 * iqr
        )

        numeric_series = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        outlier_mask = (
            numeric_series.lt(
                lower_bound
            )
            |
            numeric_series.gt(
                upper_bound
            )
        )

        outlier_count = int(
            outlier_mask.sum()
        )

        if outlier_count == 0:
            continue

        sample_outliers = (
            df.loc[
                outlier_mask,
                column
            ]
            .head(10)
            .apply(safe_value)
            .tolist()
        )

        outlier_report[column] = {
            "outlier_count":
                outlier_count,

            "outlier_percentage":
                round(
                    (
                        outlier_count
                        / len(df)
                    ) * 100,
                    2
                ),

            "q1":
                safe_value(q1),

            "q3":
                safe_value(q3),

            "iqr":
                safe_value(iqr),

            "lower_bound":
                safe_value(
                    lower_bound
                ),

            "upper_bound":
                safe_value(
                    upper_bound
                ),

            "sample_outliers":
                sample_outliers
        }

    return outlier_report


# ============================================================
# COLUMN RESOLUTION
# ============================================================

def find_column(
    df: pd.DataFrame,
    aliases: List[str]
) -> Optional[str]:

    columns = {
        str(column).lower():
            column
        for column in df.columns
    }

    for alias in aliases:

        alias_lower = (
            alias.lower()
        )

        if alias_lower in columns:

            return columns[
                alias_lower
            ]

    return None


def find_numeric_column(
    df: pd.DataFrame,
    aliases: List[str]
) -> Optional[str]:

    column = find_column(
        df,
        aliases
    )

    if column is None:
        return None

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    if values.notna().sum() == 0:
        return None

    return column


# ============================================================
# BUSINESS COLUMN RESOLUTION
# ============================================================

def resolve_business_columns(
    df: pd.DataFrame
) -> Dict[str, Optional[str]]:

    return {

        "order_id":
            find_column(
                df,
                [
                    "order_id",
                    "orderid",
                    "order_number"
                ]
            ),

        "quantity":
            find_numeric_column(
                df,
                [
                    "quantity",
                    "qty",
                    "units",
                    "units_sold"
                ]
            ),

        "unit_price":
            find_numeric_column(
                df,
                [
                    "unit_price",
                    "unitprice",
                    "selling_price",
                    "sale_price"
                ]
            ),

        "discount_percent":
            find_numeric_column(
                df,
                [
                    "discount_percent",
                    "discount_pct",
                    "discount_percentage"
                ]
            ),

        "discount":
            find_numeric_column(
                df,
                [
                    "discount"
                ]
            ),

        "sales":
            find_numeric_column(
                df,
                [
                    "sales",
                    "revenue",
                    "total_sales",
                    "total_revenue",
                    "net_sales"
                ]
            ),

        "unit_cost":
            find_numeric_column(
                df,
                [
                    "unit_cost",
                    "unit_cost_price",
                    "cost_per_unit"
                ]
            ),

        "total_cost":
            find_numeric_column(
                df,
                [
                    "total_cost",
                    "cost",
                    "total_expense",
                    "total_cogs"
                ]
            ),

        "profit":
            find_numeric_column(
                df,
                [
                    "profit",
                    "gross_profit",
                    "net_profit"
                ]
            ),

        "status":
            find_column(
                df,
                [
                    "order_status",
                    "delivery_status",
                    "shipment_status",
                    "status"
                ]
            ),

        "return_status":
            find_column(
                df,
                [
                    "return_status",
                    "returned",
                    "is_returned"
                ]
            )
    }


# ============================================================
# DISCOUNT RESOLUTION
# ============================================================

def get_discount_percentage(
    df: pd.DataFrame,
    columns: Dict[str, Optional[str]]
) -> Optional[pd.Series]:

    discount_percent_col = (
        columns.get(
            "discount_percent"
        )
    )

    if discount_percent_col:

        return pd.to_numeric(
            df[discount_percent_col],
            errors="coerce"
        )

    discount_col = (
        columns.get("discount")
    )

    if discount_col:

        values = pd.to_numeric(
            df[discount_col],
            errors="coerce"
        )

        valid = values.dropna()

        if (
            not valid.empty
            and valid.between(
                0,
                100
            ).all()
        ):

            return values

    return None


# ============================================================
# BUSINESS RULE VALIDATION
# ============================================================

def validate_business_rules(
    df: pd.DataFrame
) -> Dict[str, Any]:

    issues = {}

    if df.empty:
        return issues

    columns = (
        resolve_business_columns(df)
    )

    quantity_col = columns[
        "quantity"
    ]

    unit_price_col = columns[
        "unit_price"
    ]

    sales_col = columns[
        "sales"
    ]

    unit_cost_col = columns[
        "unit_cost"
    ]

    total_cost_col = columns[
        "total_cost"
    ]

    profit_col = columns[
        "profit"
    ]

    # ========================================================
    # SALES CONSISTENCY
    # ========================================================

    if (
        quantity_col
        and unit_price_col
        and sales_col
    ):

        quantity = pd.to_numeric(
            df[quantity_col],
            errors="coerce"
        )

        unit_price = pd.to_numeric(
            df[unit_price_col],
            errors="coerce"
        )

        sales = pd.to_numeric(
            df[sales_col],
            errors="coerce"
        )

        discount = (
            get_discount_percentage(
                df,
                columns
            )
        )

        expected_sales = (
            quantity
            * unit_price
        )

        if discount is not None:

            expected_sales = (
                expected_sales
                * (
                    1
                    - discount / 100
                )
            )

        valid = (
            quantity.notna()
            & unit_price.notna()
            & sales.notna()
        )

        if discount is not None:

            valid = (
                valid
                & discount.notna()
            )

        difference = (
            sales
            - expected_sales
        )

        inconsistent = (
            valid
            & difference.abs().gt(
                DEFAULT_TOLERANCE
            )
        )

        count = int(
            inconsistent.sum()
        )

        samples = []

        for index in df.index[
            inconsistent
        ][:10]:

            record = {
                "quantity":
                    safe_value(
                        quantity.loc[index]
                    ),

                "unit_price":
                    safe_value(
                        unit_price.loc[index]
                    ),

                "sales":
                    safe_value(
                        sales.loc[index]
                    ),

                "expected_sales":
                    safe_value(
                        round(
                            expected_sales.loc[
                                index
                            ],
                            2
                        )
                    ),

                "difference":
                    safe_value(
                        round(
                            difference.loc[
                                index
                            ],
                            2
                        )
                    )
            }

            order_id_col = (
                columns["order_id"]
            )

            if order_id_col:

                record["order_id"] = (
                    safe_value(
                        df.loc[
                            index,
                            order_id_col
                        ]
                    )
                )

            if discount is not None:

                record[
                    "discount_percent"
                ] = safe_value(
                    discount.loc[index]
                )

            samples.append(record)

        issues[
            "sales_consistency"
        ] = {

            "checked": True,

            "inconsistent_count":
                count,

            "formula":
                "sales = quantity × "
                "unit_price × "
                "(1 - discount_percent / 100)",

            "tolerance":
                DEFAULT_TOLERANCE,

            "severity":
                "medium"
                if count > 0
                else "none",

            "sample_records":
                samples
        }

    # ========================================================
    # PROFIT CONSISTENCY
    # ========================================================

    if (
        sales_col
        and profit_col
        and (
            unit_cost_col
            or total_cost_col
        )
    ):

        sales = pd.to_numeric(
            df[sales_col],
            errors="coerce"
        )

        profit = pd.to_numeric(
            df[profit_col],
            errors="coerce"
        )

        if (
            unit_cost_col
            and quantity_col
        ):

            quantity = pd.to_numeric(
                df[quantity_col],
                errors="coerce"
            )

            unit_cost = pd.to_numeric(
                df[unit_cost_col],
                errors="coerce"
            )

            expected_cost = (
                quantity
                * unit_cost
            )

            cost_interpretation = (
                "quantity × unit_cost"
            )

        else:

            expected_cost = pd.to_numeric(
                df[total_cost_col],
                errors="coerce"
            )

            cost_interpretation = (
                "total_cost"
            )

        expected_profit = (
            sales
            - expected_cost
        )

        difference = (
            profit
            - expected_profit
        )

        valid = (
            sales.notna()
            & profit.notna()
            & expected_cost.notna()
        )

        inconsistent = (
            valid
            & difference.abs().gt(
                DEFAULT_TOLERANCE
            )
        )

        count = int(
            inconsistent.sum()
        )

        issues[
            "profit_consistency"
        ] = {

            "checked": True,

            "inconsistent_count":
                count,

            "formula":
                "profit = sales - cost",

            "cost_interpretation":
                cost_interpretation,

            "tolerance":
                DEFAULT_TOLERANCE,

            "severity":
                "medium"
                if count > 0
                else "none"
        }

    # ========================================================
    # NEGATIVE PROFIT
    # ========================================================

    if profit_col:

        profit = pd.to_numeric(
            df[profit_col],
            errors="coerce"
        )

        negative_count = int(
            profit.lt(0).sum()
        )

        issues[
            "negative_profit"
        ] = {

            "count":
                negative_count,

            "issue":
                "Negative profit indicates "
                "a potential business loss.",

            "action":
                "flag_only",

            "severity":
                "info"
                if negative_count > 0
                else "none"
        }

    # ========================================================
    # QUANTITY VALIDATION
    # ========================================================

    if quantity_col:

        quantity = pd.to_numeric(
            df[quantity_col],
            errors="coerce"
        )

        negative_count = int(
            quantity.lt(0).sum()
        )

        zero_count = int(
            quantity.eq(0).sum()
        )

        missing_count = int(
            quantity.isna().sum()
        )

        issues[
            "quantity_validation"
        ] = {

            "negative_count":
                negative_count,

            "zero_count":
                zero_count,

            "missing_count":
                missing_count,

            "severity":
                "high"
                if negative_count > 0
                else
                "medium"
                if (
                    zero_count > 0
                    or missing_count > 0
                )
                else "none"
        }

    # ========================================================
    # UNIT PRICE VALIDATION
    # ========================================================

    if unit_price_col:

        price = pd.to_numeric(
            df[unit_price_col],
            errors="coerce"
        )

        negative_count = int(
            price.lt(0).sum()
        )

        zero_count = int(
            price.eq(0).sum()
        )

        issues[
            "unit_price_validation"
        ] = {

            "negative_count":
                negative_count,

            "zero_count":
                zero_count,

            "severity":
                "high"
                if negative_count > 0
                else
                "medium"
                if zero_count > 0
                else "none"
        }

    # ========================================================
    # DISCOUNT VALIDATION
    # ========================================================

    discount = (
        get_discount_percentage(
            df,
            columns
        )
    )

    if discount is not None:

        negative_count = int(
            discount.lt(0).sum()
        )

        excessive_count = int(
            discount.gt(100).sum()
        )

        issues[
            "discount_validation"
        ] = {

            "negative_count":
                negative_count,

            "above_100_percent":
                excessive_count,

            "severity":
                "high"
                if (
                    negative_count > 0
                    or excessive_count > 0
                )
                else "none"
        }

    # ========================================================
    # STATUS VALIDATION
    # ========================================================

    status_col = columns[
        "status"
    ]

    if status_col:

        status = (
            df[status_col]
            .astype("string")
            .str.strip()
            .str.casefold()
        )

        completed_mask = status.isin([
            "completed",
            "complete",
            "delivered",
            "shipped",
            "fulfilled"
        ])

        critical_columns = [
            column
            for column in [
                quantity_col,
                sales_col,
                profit_col
            ]
            if column
        ]

        completed_issues = {}

        for column in critical_columns:

            missing_count = int(
                (
                    completed_mask
                    & df[column].isna()
                ).sum()
            )

            if missing_count > 0:

                completed_issues[
                    column
                ] = {

                    "missing_count":
                        missing_count,

                    "severity":
                        "high"
                }

        if completed_issues:

            issues[
                "completed_orders"
            ] = completed_issues

    # ========================================================
    # RETURN VALIDATION
    # ========================================================

    return_status_col = (
        columns["return_status"]
    )

    if return_status_col:

        return_status = (
            df[return_status_col]
            .astype("string")
            .str.strip()
            .str.casefold()
        )

        returned_mask = (
            return_status.isin([
                "yes",
                "returned",
                "true",
                "1"
            ])
        )

        return_issues = {}

        for column in [
            sales_col,
            profit_col
        ]:

            if not column:
                continue

            missing_count = int(
                (
                    returned_mask
                    & df[column].isna()
                ).sum()
            )

            if missing_count > 0:

                return_issues[
                    column
                ] = {

                    "missing_count":
                        missing_count,

                    "severity":
                        "high"
                }

        if return_issues:

            issues[
                "returned_orders"
            ] = return_issues

    return issues


# ============================================================
# MISSING VALUE IMPUTATION
# ============================================================

def impute_missing_values(
    df: pd.DataFrame,
    numeric_method: str = "median",
    categorical_method: str = "mode",
    max_categorical_missing_percentage:
        float = 50.0
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any]
]:

    df = df.copy()

    report = {}

    for column in df.columns:

        missing_count = int(
            df[column].isna().sum()
        )

        if missing_count == 0:
            continue

        missing_percentage = (
            missing_count
            / len(df)
            * 100
            if len(df) > 0
            else 0
        )

        # ----------------------------------------------------
        # Identifier
        # ----------------------------------------------------

        if is_identifier_column(
            column
        ):

            report[column] = {

                "method":
                    "not_imputed",

                "missing_values":
                    missing_count,

                "reason":
                    "Identifier column"
            }

            continue

        # ----------------------------------------------------
        # Numeric
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            if numeric_method == "mean":

                replacement = (
                    df[column].mean()
                )

            else:

                replacement = (
                    df[column].median()
                )

            if pd.notna(
                replacement
            ):

                df[column] = (
                    df[column]
                    .fillna(
                        replacement
                    )
                )

                report[column] = {

                    "method":
                        numeric_method,

                    "missing_values_filled":
                        missing_count,

                    "replacement_value":
                        safe_value(
                            replacement
                        )
                }

            continue

        # ----------------------------------------------------
        # Categorical/text
        # ----------------------------------------------------

        if (
            missing_percentage
            > max_categorical_missing_percentage
        ):

            report[column] = {

                "method":
                    "not_imputed",

                "missing_values":
                    missing_count,

                "reason":
                    "Too many missing "
                    "categorical values"
            }

            continue

        mode_values = (
            df[column]
            .mode(dropna=True)
        )

        if mode_values.empty:

            report[column] = {

                "method":
                    "not_imputed",

                "missing_values":
                    missing_count,

                "reason":
                    "No valid mode available"
            }

            continue

        replacement = (
            mode_values.iloc[0]
        )

        df[column] = (
            df[column]
            .fillna(replacement)
        )

        report[column] = {

            "method":
                categorical_method,

            "missing_values_filled":
                missing_count,

            "replacement_value":
                safe_value(
                    replacement
                )
        }

    return df, report


# ============================================================
# BUSINESS VALUE RECONSTRUCTION
# ============================================================

def reconstruct_business_values(
    df: pd.DataFrame
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any]
]:

    """
    Reconstruct missing business values only when
    a valid formula can be established.
    """

    df = df.copy()

    report = {
        "reconstructed_values": {},
        "business_logic_issues": {}
    }

    columns = (
        resolve_business_columns(df)
    )

    quantity_col = columns[
        "quantity"
    ]

    unit_price_col = columns[
        "unit_price"
    ]

    sales_col = columns[
        "sales"
    ]

    unit_cost_col = columns[
        "unit_cost"
    ]

    total_cost_col = columns[
        "total_cost"
    ]

    profit_col = columns[
        "profit"
    ]

    # ========================================================
    # SALES
    # ========================================================

    if (
        sales_col
        and quantity_col
        and unit_price_col
    ):

        quantity = pd.to_numeric(
            df[quantity_col],
            errors="coerce"
        )

        unit_price = pd.to_numeric(
            df[unit_price_col],
            errors="coerce"
        )

        sales = pd.to_numeric(
            df[sales_col],
            errors="coerce"
        )

        discount = (
            get_discount_percentage(
                df,
                columns
            )
        )

        calculated_sales = (
            quantity
            * unit_price
        )

        formula = (
            "quantity × unit_price"
        )

        if discount is not None:

            calculated_sales = (
                calculated_sales
                * (
                    1
                    - discount / 100
                )
            )

            formula = (
                "quantity × unit_price × "
                "(1 - discount_percent / 100)"
            )

        sales_missing = (
            sales.isna()
            & quantity.notna()
            & unit_price.notna()
        )

        if discount is not None:

            sales_missing = (
                sales_missing
                & discount.notna()
            )

        count = int(
            sales_missing.sum()
        )

        if count > 0:

            df.loc[
                sales_missing,
                sales_col
            ] = (
                calculated_sales[
                    sales_missing
                ]
            )

        report[
            "reconstructed_values"
        ]["sales"] = {

            "column":
                sales_col,

            "values_reconstructed":
                count,

            "method":
                formula
        }

        # Validate
        current_sales = pd.to_numeric(
            df[sales_col],
            errors="coerce"
        )

        valid = (
            current_sales.notna()
            & quantity.notna()
            & unit_price.notna()
        )

        if discount is not None:

            valid = (
                valid
                & discount.notna()
            )

        difference = (
            current_sales
            - calculated_sales
        )

        inconsistent = (
            valid
            & difference.abs().gt(
                DEFAULT_TOLERANCE
            )
        )

        issue_count = int(
            inconsistent.sum()
        )

        report[
            "business_logic_issues"
        ]["sales_consistency"] = {

            "inconsistent_count":
                issue_count,

            "tolerance":
                DEFAULT_TOLERANCE,

            "severity":
                "medium"
                if issue_count > 0
                else "none"
        }

    # ========================================================
    # PROFIT
    # ========================================================

    if (
        sales_col
        and profit_col
        and (
            unit_cost_col
            or total_cost_col
        )
    ):

        sales = pd.to_numeric(
            df[sales_col],
            errors="coerce"
        )

        profit = pd.to_numeric(
            df[profit_col],
            errors="coerce"
        )

        if (
            unit_cost_col
            and quantity_col
        ):

            quantity = pd.to_numeric(
                df[quantity_col],
                errors="coerce"
            )

            unit_cost = pd.to_numeric(
                df[unit_cost_col],
                errors="coerce"
            )

            calculated_cost = (
                quantity
                * unit_cost
            )

            cost_method = (
                "quantity × unit_cost"
            )

        elif total_cost_col:

            calculated_cost = pd.to_numeric(
                df[total_cost_col],
                errors="coerce"
            )

            cost_method = "total_cost"

        else:

            calculated_cost = None
            cost_method = None

        if calculated_cost is not None:

            calculated_profit = (
                sales
                - calculated_cost
            )

            profit_missing = (
                profit.isna()
                & sales.notna()
                & calculated_cost.notna()
            )

            count = int(
                profit_missing.sum()
            )

            if count > 0:

                df.loc[
                    profit_missing,
                    profit_col
                ] = (
                    calculated_profit[
                        profit_missing
                    ]
                )

            report[
                "reconstructed_values"
            ]["profit"] = {

                "column":
                    profit_col,

                "values_reconstructed":
                    count,

                "method":
                    "sales - "
                    f"({cost_method})"
            }

            current_profit = pd.to_numeric(
                df[profit_col],
                errors="coerce"
            )

            valid = (
                current_profit.notna()
                & sales.notna()
                & calculated_cost.notna()
            )

            difference = (
                current_profit
                - calculated_profit
            )

            inconsistent = (
                valid
                & difference.abs().gt(
                    DEFAULT_TOLERANCE
                )
            )

            issue_count = int(
                inconsistent.sum()
            )

            report[
                "business_logic_issues"
            ]["profit_consistency"] = {

                "inconsistent_count":
                    issue_count,

                "tolerance":
                    DEFAULT_TOLERANCE,

                "severity":
                    "medium"
                    if issue_count > 0
                    else "none"
            }

    # ========================================================
    # QUANTITY
    # ========================================================

    if quantity_col:

        quantity = pd.to_numeric(
            df[quantity_col],
            errors="coerce"
        )

        invalid = (
            quantity.notna()
            & quantity.le(0)
        )

        count = int(
            invalid.sum()
        )

        report[
            "business_logic_issues"
        ]["invalid_quantity"] = {

            "count":
                count,

            "issue":
                "Quantity should be greater "
                "than zero.",

            "action":
                "flag_only",

            "severity":
                "high"
                if count > 0
                else "none"
        }

    # ========================================================
    # UNIT PRICE
    # ========================================================

    if unit_price_col:

        price = pd.to_numeric(
            df[unit_price_col],
            errors="coerce"
        )

        invalid = (
            price.notna()
            & price.le(0)
        )

        count = int(
            invalid.sum()
        )

        report[
            "business_logic_issues"
        ]["invalid_unit_price"] = {

            "count":
                count,

            "issue":
                "Unit price should be greater "
                "than zero.",

            "action":
                "flag_only",

            "severity":
                "high"
                if count > 0
                else "none"
        }

    # ========================================================
    # DISCOUNT
    # ========================================================

    discount = (
        get_discount_percentage(
            df,
            columns
        )
    )

    if discount is not None:

        invalid = (
            discount.notna()
            & (
                discount.lt(0)
                | discount.gt(100)
            )
        )

        count = int(
            invalid.sum()
        )

        report[
            "business_logic_issues"
        ]["invalid_discount"] = {

            "count":
                count,

            "issue":
                "Discount must be between "
                "0 and 100.",

            "action":
                "flag_only",

            "severity":
                "high"
                if count > 0
                else "none"
        }

    # ========================================================
    # COMPLETED ORDERS
    # ========================================================

    status_col = columns[
        "status"
    ]

    if status_col:

        status = (
            df[status_col]
            .astype("string")
            .str.strip()
            .str.casefold()
        )

        completed = status.isin([
            "completed",
            "complete",
            "delivered",
            "shipped",
            "fulfilled"
        ])

        critical_columns = [
            column
            for column in [
                quantity_col,
                sales_col,
                profit_col
            ]
            if column
        ]

        completed_issues = {}

        for column in critical_columns:

            count = int(
                (
                    completed
                    & df[column].isna()
                ).sum()
            )

            if count > 0:

                completed_issues[
                    column
                ] = {

                    "missing_count":
                        count,

                    "action":
                        "review",

                    "severity":
                        "high"
                }

        if completed_issues:

            report[
                "business_logic_issues"
            ]["completed_orders"] = (
                completed_issues
            )

    # ========================================================
    # RETURNED ORDERS
    # ========================================================

    return_status_col = (
        columns["return_status"]
    )

    if return_status_col:

        return_status = (
            df[return_status_col]
            .astype("string")
            .str.strip()
            .str.casefold()
        )

        returned = return_status.isin([
            "yes",
            "returned",
            "true",
            "1"
        ])

        return_issues = {}

        for column in [
            sales_col,
            profit_col
        ]:

            if not column:
                continue

            count = int(
                (
                    returned
                    & df[column].isna()
                ).sum()
            )

            if count > 0:

                return_issues[
                    column
                ] = {

                    "missing_count":
                        count,

                    "action":
                        "review",

                    "severity":
                        "high"
                }

        if return_issues:

            report[
                "business_logic_issues"
            ]["returned_orders"] = (
                return_issues
            )

    return df, report


# ============================================================
# DATASET PROFILING
# ============================================================

def profile_dataset(
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Generic dataset profiler.

    Useful for AI SQL Assistant because
    the profile can be passed to an LLM
    before SQL generation.
    """

    return {

        "rows":
            len(df),

        "columns":
            len(df.columns),

        "column_names":
            list(df.columns),

        "column_types":
            detect_column_types(df),

        "missing_values":
            analyze_missing_values(df),

        "numeric_summary":
            validate_numeric_columns(df),

        "date_validation":
            validate_date_columns(df),

        "category_inconsistencies":
            detect_category_inconsistencies(df)
    }


# ============================================================
# MASTER CLEANING FUNCTION
# ============================================================

def clean_dataset(
    df: pd.DataFrame,
    standardize_categories: bool = True,
    standardize_dates: bool = True,
    impute_missing: bool = False,
    reconstruct_business: bool = True
) -> Tuple[
    pd.DataFrame,
    Dict[str, Any]
]:
    """
    Main entry point for the cleaning layer.

    Designed for heterogeneous datasets.

    Missing-value imputation is OFF by default because
    automatically filling arbitrary datasets can change
    business meaning.
    """

    # ========================================================
    # 1. BASIC CLEANING
    # ========================================================

    cleaned_df, basic_report = (
        clean_basic_data(df)
    )

    # ========================================================
    # 2. INITIAL PROFILE
    # ========================================================

    initial_profile = (
        profile_dataset(
            cleaned_df
        )
    )

    # ========================================================
    # 3. CATEGORY STANDARDIZATION
    # ========================================================

    category_report = {}

    if standardize_categories:

        cleaned_df, category_report = (
            standardize_category_values(
                cleaned_df
            )
        )

    # ========================================================
    # 4. GENDER STANDARDIZATION
    # ========================================================

    cleaned_df, gender_report = (
        standardize_gender_values(
            cleaned_df
        )
    )

    # ========================================================
    # 5. DATE STANDARDIZATION
    # ========================================================

    date_report = {}

    if standardize_dates:

        cleaned_df, date_report = (
            standardize_date_columns(
                cleaned_df
            )
        )

    # ========================================================
    # 6. BUSINESS RECONSTRUCTION
    # ========================================================

    reconstruction_report = {}

    if reconstruct_business:

        cleaned_df, reconstruction_report = (
            reconstruct_business_values(
                cleaned_df
            )
        )

    # ========================================================
    # 7. OPTIONAL IMPUTATION
    # ========================================================

    imputation_report = {}

    if impute_missing:

        cleaned_df, imputation_report = (
            impute_missing_values(
                cleaned_df
            )
        )

    # ========================================================
    # 8. FINAL PROFILE
    # ========================================================

    final_profile = (
        profile_dataset(
            cleaned_df
        )
    )

    # ========================================================
    # 9. OUTLIERS
    # ========================================================

    outlier_report = (
        detect_outliers(
            cleaned_df
        )
    )

    # ========================================================
    # 10. BUSINESS VALIDATION
    # ========================================================

    business_report = (
        validate_business_rules(
            cleaned_df
        )
    )

    # ========================================================
    # 11. FINAL REPORT
    # ========================================================

    report = {

        "status":
            "success",

        "basic_cleaning":
            basic_report,

        "initial_profile":
            initial_profile,

        "category_standardization":
            category_report,

        "gender_standardization":
            gender_report,

        "date_standardization":
            date_report,

        "reconstruction":
            reconstruction_report,

        "imputation":
            imputation_report,

        "outliers":
            outlier_report,

        "business_rules":
            business_report,

        "final_profile":
            final_profile,

        "final_shape": {

            "rows":
                len(cleaned_df),

            "columns":
                len(cleaned_df.columns)
        }
    }

    return cleaned_df, report