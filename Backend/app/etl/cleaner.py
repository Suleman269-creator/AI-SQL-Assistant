import pandas as pd


def safe_value(value):
    """Convert pandas/numpy values into JSON-safe Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    return value


# ============================================================
# 1. TEXT CLEANING
# ============================================================

def clean_text_values(df):
    df = df.copy()

    text_columns = df.select_dtypes(
        include="object"
    ).columns

    for column in text_columns:
        df[column] = df[column].apply(
            lambda value: " ".join(value.split())
            if isinstance(value, str)
            else value
        )

    return df


# ============================================================
# 2. BASIC DATA CLEANING
# ============================================================

def clean_basic_data(df):
    df = df.copy()

    # --------------------------------------------------
    # Clean column names
    # --------------------------------------------------

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    # --------------------------------------------------
    # Remove completely empty columns
    # --------------------------------------------------

    df = df.dropna(
        axis=1,
        how="all"
    )

    # --------------------------------------------------
    # Remove completely empty rows
    # --------------------------------------------------

    df = df.dropna(
        axis=0,
        how="all"
    )

    # --------------------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------------------

    duplicate_count = int(
        df.duplicated().sum()
    )

    df = df.drop_duplicates()

    # --------------------------------------------------
    # Clean text
    # --------------------------------------------------

    df = clean_text_values(df)

    return df, {
        "duplicate_rows_removed": duplicate_count,
        "rows_after_cleaning": len(df),
        "columns_after_cleaning": len(df.columns)
    }


# ============================================================
# 3. CATEGORY INCONSISTENCY DETECTION
# ============================================================

def detect_category_inconsistencies(
    df,
    max_unique_values=20
):
    issues = {}

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns

    for column in categorical_columns:

        values = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        if values.nunique() > max_unique_values:
            continue

        normalized = values.str.lower()

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
            key: sorted(list(variants))
            for key, variants in groups.items()
            if len(variants) > 1
        }

        if inconsistent:
            issues[column] = inconsistent

    return issues


# ============================================================
# 4. MISSING VALUE ANALYSIS
# ============================================================

def analyze_missing_values(df):

    missing_report = {}

    total_rows = len(df)

    for column in df.columns:

        missing_count = int(
            df[column].isna().sum()
        )

        missing_percentage = (
            round(
                (
                    missing_count
                    / total_rows
                ) * 100,
                2
            )
            if total_rows > 0
            else 0
        )

        if missing_count > 0:

            missing_report[column] = {
                "missing_count": missing_count,
                "missing_percentage": missing_percentage,
                "data_type": str(df[column].dtype)
            }

    return missing_report


# ============================================================
# 5. DATE VALIDATION
# ============================================================

def validate_date_columns(df):

    date_report = {}

    date_keywords = [
        "date",
        "time",
        "created_at",
        "updated_at"
    ]

    for column in df.columns:

        column_name = column.lower()

        if not any(
            keyword in column_name
            for keyword in date_keywords
        ):
            continue

        converted = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid_mask = (
            df[column].notna()
            & converted.isna()
        )

        invalid_count = int(
            invalid_mask.sum()
        )

        if invalid_count > 0:

            date_report[column] = {
                "invalid_count": invalid_count,
                "invalid_percentage": round(
                    (
                        invalid_count
                        / len(df)
                    ) * 100,
                    2
                ) if len(df) > 0 else 0
            }

    return date_report


# ============================================================
# 6. DATE STANDARDIZATION
# ============================================================

def standardize_date_columns(df):

    df = df.copy()

    report = {}

    date_keywords = [
        "date",
        "time",
        "created_at",
        "updated_at"
    ]

    for column in df.columns:

        column_name = column.lower()

        if not any(
            keyword in column_name
            for keyword in date_keywords
        ):
            continue

        original_non_null = int(
            df[column].notna().sum()
        )

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

        df[column] = converted.dt.strftime(
            "%Y-%m-%d"
        )

        df.loc[
            converted.isna(),
            column
        ] = None

        report[column] = {
            "valid_dates": valid_count,
            "invalid_dates": invalid_count,
            "standard_format": "YYYY-MM-DD"
        }

    return df, report


# ============================================================
# 7. NUMERIC VALIDATION
# ============================================================

def validate_numeric_columns(df):

    numeric_report = {}

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        negative_count = int(
            (values < 0).sum()
        )

        zero_count = int(
            (values == 0).sum()
        )

        missing_count = int(
            values.isna().sum()
        )

        numeric_report[column] = {
            "data_type": str(df[column].dtype),
            "minimum": (
                float(values.min())
                if not values.dropna().empty
                else None
            ),
            "maximum": (
                float(values.max())
                if not values.dropna().empty
                else None
            ),
            "negative_values": negative_count,
            "zero_values": zero_count,
            "missing_values": missing_count
        }

    return numeric_report


# ============================================================
# 8. OUTLIER DETECTION
# ============================================================

def detect_outliers(df):

    outlier_report = {}

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        values = df[column].dropna()

        if len(values) < 4:
            continue

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)

        iqr = q3 - q1

        lower_bound = (
            q1 - 1.5 * iqr
        )

        upper_bound = (
            q3 + 1.5 * iqr
        )

        outlier_mask = (
            (df[column] < lower_bound)
            | (df[column] > upper_bound)
        )

        outlier_count = int(
            outlier_mask.sum()
        )

        if outlier_count > 0:

            sample_outliers = (
                df.loc[
                    outlier_mask,
                    column
                ]
                .head(10)
                .tolist()
            )

            outlier_report[column] = {
                "outlier_count": outlier_count,
                "outlier_percentage": round(
                    (
                        outlier_count
                        / len(df)
                    ) * 100,
                    2
                ),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "sample_outliers": sample_outliers
            }

    return outlier_report


# ============================================================
# 9. BUSINESS RULE VALIDATION
# ============================================================

def validate_business_rules(df):

    issues = {}

    data = df.copy()

    # --------------------------------------------------
    # Helper: find column safely
    # --------------------------------------------------

    def find_column(possible_names):

        for name in possible_names:

            if name in data.columns:
                return name

        return None

    quantity_col = find_column([
        "quantity",
        "qty"
    ])

    unit_price_col = find_column([
        "unit_price",
        "unitprice",
        "price"
    ])

    discount_col = find_column([
        "discount",
        "discount_percent"
    ])

    sales_col = find_column([
        "sales",
        "revenue",
        "total_sales"
    ])

    cost_col = find_column([
        "cost_price",
        "cost",
        "total_cost"
    ])

    profit_col = find_column([
        "profit",
        "gross_profit"
    ])

    order_id_col = find_column([
        "order_id",
        "orderid",
        "id"
    ])

    # ==================================================
    # 1. SALES CONSISTENCY
    # ==================================================

    if (
        quantity_col
        and unit_price_col
        and discount_col
        and sales_col
    ):

        temp = data[
            [
                quantity_col,
                unit_price_col,
                discount_col,
                sales_col
            ]
        ].copy()

        temp = temp.apply(
            pd.to_numeric,
            errors="coerce"
        )

        valid = temp.notna().all(axis=1)

        expected_sales = (
            temp[quantity_col]
            * temp[unit_price_col]
            * (
                1
                - temp[discount_col] / 100
            )
        )

        actual_sales = temp[sales_col]

        difference = (
            actual_sales
            - expected_sales
        )

        # Small rounding differences are acceptable.
        tolerance = 1.0

        inconsistent_mask = (
            valid
            & (
                difference.abs()
                > tolerance
            )
        )

        inconsistent_count = int(
            inconsistent_mask.sum()
        )

        sample_records = []

        if inconsistent_count > 0:

            problem_indexes = (
                data.index[
                    inconsistent_mask
                ].tolist()
            )

            for index in problem_indexes[:10]:

                record = {
                    "quantity": safe_value(
                        temp.loc[
                            index,
                            quantity_col
                        ]
                    ),
                    "unit_price": safe_value(
                        temp.loc[
                            index,
                            unit_price_col
                        ]
                    ),
                    "discount": safe_value(
                        temp.loc[
                            index,
                            discount_col
                        ]
                    ),
                    "sales": safe_value(
                        temp.loc[
                            index,
                            sales_col
                        ]
                    ),
                    "expected_sales": safe_value(
                        round(
                            expected_sales.loc[index],
                            2
                        )
                    ),
                    "difference": safe_value(
                        round(
                            difference.loc[index],
                            2
                        )
                    )
                }

                if order_id_col:

                    record["order_id"] = safe_value(
                        data.loc[
                            index,
                            order_id_col
                        ]
                    )

                sample_records.append(record)

        issues["sales_consistency"] = {
            "inconsistent_count": inconsistent_count,
            "issue": (
                "Sales does not match "
                "quantity × unit_price × "
                "(1 - discount/100)"
            ),
            "tolerance": tolerance,
            "severity": (
                "medium"
                if inconsistent_count > 0
                else "none"
            ),
            "sample_records": sample_records
        }

    # ==================================================
    # 2. PROFIT CONSISTENCY
    #
    # Total Cost = Quantity × Cost Price
    # Profit = Sales - Total Cost
    # ==================================================

    if (
        sales_col
        and cost_col
        and quantity_col
        and profit_col
    ):

        sales = pd.to_numeric(
            data[sales_col],
            errors="coerce"
        )

        cost_price = pd.to_numeric(
            data[cost_col],
            errors="coerce"
        )

        quantity = pd.to_numeric(
            data[quantity_col],
            errors="coerce"
        )

        profit = pd.to_numeric(
            data[profit_col],
            errors="coerce"
        )

        expected_profit = (
            sales
            - (
                quantity
                * cost_price
            )
        )

        profit_difference = (
            profit
            - expected_profit
        )

        valid_profit = (
            sales.notna()
            & cost_price.notna()
            & quantity.notna()
            & profit.notna()
        )

        tolerance = 1.0

        inconsistent_mask = (
            valid_profit
            & (
                profit_difference.abs()
                > tolerance
            )
        )

        inconsistent_count = int(
            inconsistent_mask.sum()
        )

        sample_records = []

        if inconsistent_count > 0:

            sample_df = data.loc[
                inconsistent_mask
            ].copy()

            for index, row in sample_df.head(10).iterrows():

                record = {
                    "sales": safe_value(
                        row.get(sales_col)
                    ),
                    "quantity": safe_value(
                        row.get(quantity_col)
                    ),
                    "cost_price": safe_value(
                        row.get(cost_col)
                    ),
                    "profit": safe_value(
                        row.get(profit_col)
                    ),
                    "expected_profit": safe_value(
                        round(
                            expected_profit.loc[index],
                            2
                        )
                    ),
                    "difference": safe_value(
                        round(
                            profit_difference.loc[index],
                            2
                        )
                    )
                }

                if order_id_col:

                    record["order_id"] = safe_value(
                        row.get(order_id_col)
                    )

                sample_records.append(record)

        issues["profit_consistency"] = {
            "inconsistent_count": inconsistent_count,
            "issue": (
                "Profit does not match "
                "sales - (quantity × cost_price)"
            ),
            "formula": (
                "profit = sales - "
                "(quantity × cost_price)"
            ),
            "tolerance": tolerance,
            "severity": (
                "none"
                if inconsistent_count == 0
                else "medium"
            ),
            "sample_records": sample_records
        }

    # ==================================================
    # 3. NEGATIVE PROFIT
    # ==================================================

    if profit_col:

        profit_values = pd.to_numeric(
            data[profit_col],
            errors="coerce"
        )

        negative_mask = (
            profit_values < 0
        )

        negative_count = int(
            negative_mask.sum()
        )

        issues["negative_profit"] = {
            "count": negative_count,
            "issue": (
                "Negative profit indicates "
                "a potential business loss"
            ),
            "action": "flag_only",
            "severity": (
                "info"
                if negative_count > 0
                else "none"
            )
        }

    # ==================================================
    # 4. QUANTITY VALIDATION
    # ==================================================

    if quantity_col:

        quantity_values = pd.to_numeric(
            data[quantity_col],
            errors="coerce"
        )

        negative_quantity = int(
            (quantity_values < 0).sum()
        )

        zero_quantity = int(
            (quantity_values == 0).sum()
        )

        missing_quantity = int(
            quantity_values.isna().sum()
        )

        issues["quantity_validation"] = {
            "negative_count": negative_quantity,
            "zero_count": zero_quantity,
            "missing_count": missing_quantity,
            "severity": (
                "high"
                if negative_quantity > 0
                else "medium"
                if (
                    zero_quantity > 0
                    or missing_quantity > 0
                )
                else "none"
            )
        }

    # ==================================================
    # 5. DISCOUNT VALIDATION
    # ==================================================

    if discount_col:

        discount_values = pd.to_numeric(
            data[discount_col],
            errors="coerce"
        )

        negative_discount = int(
            (discount_values < 0).sum()
        )

        excessive_discount = int(
            (discount_values > 100).sum()
        )

        issues["discount_validation"] = {
            "negative_count": negative_discount,
            "above_100_percent": excessive_discount,
            "severity": (
                "high"
                if (
                    negative_discount > 0
                    or excessive_discount > 0
                )
                else "none"
            )
        }

    # ==================================================
    # 6. UNIT PRICE VALIDATION
    # ==================================================

    if unit_price_col:

        price_values = pd.to_numeric(
            data[unit_price_col],
            errors="coerce"
        )

        negative_price = int(
            (price_values < 0).sum()
        )

        zero_price = int(
            (price_values == 0).sum()
        )

        issues["unit_price_validation"] = {
            "negative_count": negative_price,
            "zero_count": zero_price,
            "severity": (
                "high"
                if negative_price > 0
                else "medium"
                if zero_price > 0
                else "none"
            )
        }

    return issues


# ============================================================
# 10. MISSING VALUE IMPUTATION
# ============================================================

def impute_missing_values(df):

    df = df.copy()

    report = {}

    for column in df.columns:

        missing_count = int(
            df[column].isna().sum()
        )

        if missing_count == 0:
            continue

        # --------------------------------------------------
        # Numeric columns → median
        # --------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            replacement = (
                df[column].median()
            )

            if pd.notna(replacement):

                df[column] = (
                    df[column]
                    .fillna(replacement)
                )

                report[column] = {
                    "method": "median",
                    "missing_values_filled":
                        missing_count,
                    "replacement_value":
                        safe_value(replacement)
                }

        # --------------------------------------------------
        # Text columns → mode
        # --------------------------------------------------

        else:

            mode_values = (
                df[column]
                .mode()
            )

            if not mode_values.empty:

                replacement = (
                    mode_values.iloc[0]
                )

                df[column] = (
                    df[column]
                    .fillna(replacement)
                )

                report[column] = {
                    "method": "mode",
                    "missing_values_filled":
                        missing_count,
                    "replacement_value":
                        safe_value(replacement)
                }

    return df, report


# ============================================================
# 11. BUSINESS-RULE RECONSTRUCTION
# ============================================================

def reconstruct_business_values(df):

    df = df.copy()

    report = {
        "reconstructed_values": {},
        "business_logic_issues": {}
    }

    # --------------------------------------------------
    # Helper
    # --------------------------------------------------

    def has_columns(*columns):

        return all(
            column in df.columns
            for column in columns
        )

    # ==================================================
    # 11.1 SALES RECONSTRUCTION & VALIDATION
    #
    # Sales =
    # Quantity × Unit Price × (1 - Discount/100)
    # ==================================================

    if has_columns(
        "sales",
        "quantity",
        "unit_price"
    ):

        quantity = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        )

        unit_price = pd.to_numeric(
            df["unit_price"],
            errors="coerce"
        )

        calculated_sales = (
            quantity
            * unit_price
        )

        if "discount" in df.columns:

            discount = pd.to_numeric(
                df["discount"],
                errors="coerce"
            )

            calculated_sales = (
                calculated_sales
                * (
                    1
                    - discount / 100
                )
            )

        # --------------------------------------------------
        # Reconstruct missing sales
        # --------------------------------------------------

        sales_missing = (
            df["sales"].isna()
            & quantity.notna()
            & unit_price.notna()
        )

        if "discount" in df.columns:

            sales_missing = (
                sales_missing
                & discount.notna()
            )

        sales_count = int(
            sales_missing.sum()
        )

        if sales_count > 0:

            df.loc[
                sales_missing,
                "sales"
            ] = calculated_sales[
                sales_missing
            ]

        report[
            "reconstructed_values"
        ]["sales"] = {
            "method": (
                "quantity × unit_price × "
                "(1 - discount/100)"
            ),
            "values_reconstructed":
                sales_count
        }

        # --------------------------------------------------
        # Validate existing sales
        # --------------------------------------------------

        valid_sales_mask = (
            df["sales"].notna()
            & quantity.notna()
            & unit_price.notna()
        )

        if "discount" in df.columns:

            valid_sales_mask = (
                valid_sales_mask
                & discount.notna()
            )

        sales_difference = (
            pd.to_numeric(
                df["sales"],
                errors="coerce"
            )
            - calculated_sales
        )

        tolerance = 1.0

        inconsistent_sales = (
            valid_sales_mask
            & (
                sales_difference.abs()
                > tolerance
            )
        )

        sales_issue_count = int(
            inconsistent_sales.sum()
        )

        sales_samples = []

        if sales_issue_count > 0:

            sample_columns = [
                column
                for column in [
                    "order_id",
                    "quantity",
                    "unit_price",
                    "discount",
                    "sales"
                ]
                if column in df.columns
            ]

            sales_samples_df = (
                df.loc[
                    inconsistent_sales,
                    sample_columns
                ]
                .copy()
            )

            sales_samples_df[
                "expected_sales"
            ] = calculated_sales[
                inconsistent_sales
            ]

            sales_samples_df[
                "difference"
            ] = sales_difference[
                inconsistent_sales
            ]

            sales_samples = (
                sales_samples_df
                .head(10)
                .astype(object)
                .where(
                    pd.notnull(
                        sales_samples_df.head(10)
                    ),
                    None
                )
                .to_dict(
                    orient="records"
                )
            )

        report[
            "business_logic_issues"
        ]["sales_consistency"] = {
            "inconsistent_count":
                sales_issue_count,
            "issue": (
                "Sales does not match "
                "quantity × unit_price × "
                "(1 - discount/100)"
            ),
            "tolerance": tolerance,
            "severity": (
                "medium"
                if sales_issue_count > 0
                else "none"
            ),
            "sample_records":
                sales_samples
        }

    # ==================================================
    # 11.2 PROFIT RECONSTRUCTION & VALIDATION
    #
    # Total Cost =
    # Quantity × Cost Price
    #
    # Profit =
    # Sales - Total Cost
    # ==================================================

    if has_columns(
        "sales",
        "quantity",
        "cost_price",
        "profit"
    ):

        sales = pd.to_numeric(
            df["sales"],
            errors="coerce"
        )

        quantity = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        )

        cost_price = pd.to_numeric(
            df["cost_price"],
            errors="coerce"
        )

        calculated_profit = (
            sales
            - (
                quantity
                * cost_price
            )
        )

        profit_missing = (
            df["profit"].isna()
            & sales.notna()
            & quantity.notna()
            & cost_price.notna()
        )

        profit_count = int(
            profit_missing.sum()
        )

        if profit_count > 0:

            df.loc[
                profit_missing,
                "profit"
            ] = calculated_profit[
                profit_missing
            ]

        report[
            "reconstructed_values"
        ]["profit"] = {
            "method": (
                "sales - "
                "(quantity × cost_price)"
            ),
            "values_reconstructed":
                profit_count
        }

        # --------------------------------------------------
        # Validate profit
        # --------------------------------------------------

        valid_profit_mask = (
            df["profit"].notna()
            & sales.notna()
            & quantity.notna()
            & cost_price.notna()
        )

        profit_difference = (
            pd.to_numeric(
                df["profit"],
                errors="coerce"
            )
            - calculated_profit
        )

        tolerance = 1.0

        inconsistent_profit = (
            valid_profit_mask
            & (
                profit_difference.abs()
                > tolerance
            )
        )

        profit_issue_count = int(
            inconsistent_profit.sum()
        )

        profit_samples = []

        if profit_issue_count > 0:

            sample_columns = [
                column
                for column in [
                    "order_id",
                    "sales",
                    "quantity",
                    "cost_price",
                    "profit"
                ]
                if column in df.columns
            ]

            profit_samples_df = (
                df.loc[
                    inconsistent_profit,
                    sample_columns
                ]
                .copy()
            )

            profit_samples_df[
                "expected_profit"
            ] = calculated_profit[
                inconsistent_profit
            ]

            profit_samples_df[
                "difference"
            ] = profit_difference[
                inconsistent_profit
            ]

            profit_samples = (
                profit_samples_df
                .head(10)
                .astype(object)
                .where(
                    pd.notnull(
                        profit_samples_df.head(10)
                    ),
                    None
                )
                .to_dict(
                    orient="records"
                )
            )

        report[
            "business_logic_issues"
        ]["profit_consistency"] = {
            "inconsistent_count":
                profit_issue_count,
            "issue": (
                "Profit does not equal "
                "sales - "
                "(quantity × cost_price)"
            ),
            "formula": (
                "profit = sales - "
                "(quantity × cost_price)"
            ),
            "tolerance": tolerance,
            "severity": (
                "medium"
                if profit_issue_count > 0
                else "none"
            ),
            "sample_records":
                profit_samples
        }

    # ==================================================
    # 11.3 QUANTITY RECONSTRUCTION
    # ==================================================

    if has_columns(
        "quantity",
        "sales",
        "unit_price"
    ):

        quantity_mask = (
            df["quantity"].isna()
            & df["sales"].notna()
            & df["unit_price"].notna()
            & (
                pd.to_numeric(
                    df["unit_price"],
                    errors="coerce"
                ) > 0
            )
        )

        unit_price = pd.to_numeric(
            df["unit_price"],
            errors="coerce"
        )

        if "discount" in df.columns:

            discount = pd.to_numeric(
                df["discount"],
                errors="coerce"
            )

            quantity_mask = (
                quantity_mask
                & discount.notna()
            )

            discounted_price = (
                unit_price
                * (
                    1
                    - discount / 100
                )
            )

        else:

            discounted_price = unit_price

        calculated_quantity = (
            pd.to_numeric(
                df["sales"],
                errors="coerce"
            )
            / discounted_price
        )

        valid_quantity = (
            discounted_price.gt(0)
            & calculated_quantity.gt(0)
            & (
                (
                    calculated_quantity
                    - calculated_quantity.round()
                ).abs()
                < 0.000001
            )
        )

        reconstruct_quantity = (
            quantity_mask
            & valid_quantity
        )

        quantity_count = int(
            reconstruct_quantity.sum()
        )

        if quantity_count > 0:

            df.loc[
                reconstruct_quantity,
                "quantity"
            ] = (
                calculated_quantity[
                    reconstruct_quantity
                ].round()
            )

        report[
            "reconstructed_values"
        ]["quantity"] = {
            "method":
                "sales / discounted_unit_price",
            "values_reconstructed":
                quantity_count
        }

    # ==================================================
    # 11.4 NEGATIVE PROFIT
    # ==================================================

    if "profit" in df.columns:

        profit_values = pd.to_numeric(
            df["profit"],
            errors="coerce"
        )

        negative_profit_mask = (
            profit_values.notna()
            & profit_values.lt(0)
        )

        loss_count = int(
            negative_profit_mask.sum()
        )

        report[
            "business_logic_issues"
        ]["negative_profit"] = {
            "count": loss_count,
            "issue": (
                "Negative profit indicates "
                "a potential business loss"
            ),
            "action": "flag_only",
            "severity": (
                "info"
                if loss_count > 0
                else "none"
            )
        }

    # ==================================================
    # 11.5 QUANTITY VALIDATION
    # ==================================================

    if "quantity" in df.columns:

        quantity_values = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        )

        invalid_quantity = (
            quantity_values.notna()
            & quantity_values.le(0)
        )

        quantity_issue_count = int(
            invalid_quantity.sum()
        )

        report[
            "business_logic_issues"
        ]["invalid_quantity"] = {
            "count": quantity_issue_count,
            "issue": (
                "Quantity should be "
                "greater than zero"
            ),
            "action": "flag_only",
            "severity": (
                "high"
                if quantity_issue_count > 0
                else "none"
            )
        }

    # ==================================================
    # 11.6 UNIT PRICE VALIDATION
    # ==================================================

    if "unit_price" in df.columns:

        unit_price_values = pd.to_numeric(
            df["unit_price"],
            errors="coerce"
        )

        invalid_price = (
            unit_price_values.notna()
            & unit_price_values.le(0)
        )

        price_issue_count = int(
            invalid_price.sum()
        )

        report[
            "business_logic_issues"
        ]["invalid_unit_price"] = {
            "count": price_issue_count,
            "issue": (
                "Unit price should "
                "be greater than zero"
            ),
            "action": "flag_only",
            "severity": (
                "high"
                if price_issue_count > 0
                else "none"
            )
        }

    # ==================================================
    # 11.7 DISCOUNT VALIDATION
    # ==================================================

    if "discount" in df.columns:

        discount_values = pd.to_numeric(
            df["discount"],
            errors="coerce"
        )

        invalid_discount = (
            discount_values.notna()
            & (
                discount_values.lt(0)
                | discount_values.gt(100)
            )
        )

        discount_issue_count = int(
            invalid_discount.sum()
        )

        report[
            "business_logic_issues"
        ]["invalid_discount"] = {
            "count": discount_issue_count,
            "issue": (
                "Discount must be "
                "between 0 and 100"
            ),
            "action": "flag_only",
            "severity": (
                "high"
                if discount_issue_count > 0
                else "none"
            )
        }

    # ==================================================
    # 11.8 COMPLETED / DELIVERED ORDERS
    # ==================================================

    status_column = None

    for column in [
        "order_status",
        "delivery_status",
        "shipment_status"
    ]:

        if column in df.columns:

            status_column = column
            break

    if status_column:

        status = (
            df[status_column]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        completed_mask = status.isin([
            "completed",
            "delivered",
            "shipped"
        ])

        critical_columns = [
            column
            for column in [
                "quantity",
                "sales",
                "profit"
            ]
            if column in df.columns
        ]

        completed_issues = {}

        for column in critical_columns:

            missing_mask = (
                completed_mask
                & df[column].isna()
            )

            count = int(
                missing_mask.sum()
            )

            if count > 0:

                completed_issues[column] = {
                    "missing_count": count,
                    "issue": (
                        f"{column} is missing "
                        "for completed/"
                        "delivered orders"
                    ),
                    "action": "review",
                    "severity": "high"
                }

        if completed_issues:

            report[
                "business_logic_issues"
            ]["completed_orders"] = (
                completed_issues
            )

    # ==================================================
    # 11.9 RETURNED ORDERS
    # ==================================================

    if "return_status" in df.columns:

        return_status = (
            df["return_status"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        returned_mask = return_status.isin([
            "yes",
            "returned"
        ])

        return_issues = {}

        for column in [
            "sales",
            "profit"
        ]:

            if column not in df.columns:
                continue

            missing_mask = (
                returned_mask
                & df[column].isna()
            )

            count = int(
                missing_mask.sum()
            )

            if count > 0:

                return_issues[column] = {
                    "missing_count": count,
                    "issue": (
                        f"{column} is missing "
                        "for returned orders"
                    ),
                    "action": "review",
                    "severity": "high"
                }

        if return_issues:

            report[
                "business_logic_issues"
            ]["returned_orders"] = (
                return_issues
            )

    return df, report