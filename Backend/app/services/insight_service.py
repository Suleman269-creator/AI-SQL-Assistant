import re


def format_number(value):
    """
    Format numeric values for human-readable output.
    """

    if value is None:
        return "—"

    if isinstance(value, float):

        if value.is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def generate_insight(question: str, result: dict):
    """
    Generate a simple deterministic insight from
    the actual SQL result.

    No external AI/API call is required.
    """

    if not result:
        return "No result was returned."

    rows = result.get("rows", [])
    columns = result.get("columns", [])

    if not rows:
        return "No matching data was found."

    question_lower = question.lower()

    # ========================================================
    # SINGLE VALUE RESULT
    # ========================================================

    if len(rows) == 1 and len(columns) == 1:

        column = columns[0]
        value = rows[0].get(column)

        formatted_value = format_number(value)

        # Total / Sum
        if (
            "total" in question_lower
            or "sum" in question_lower
        ):
            return (
                f"Total {column.replace('_', ' ')} "
                f"is {formatted_value}."
            )

        # Average
        if (
            "average" in question_lower
            or "avg" in question_lower
        ):
            return (
                f"The average {column.replace('_', ' ')} "
                f"is {formatted_value}."
            )

        # Maximum
        if (
            "maximum" in question_lower
            or "highest" in question_lower
            or "max" in question_lower
        ):
            return (
                f"The highest {column.replace('_', ' ')} "
                f"is {formatted_value}."
            )

        # Minimum
        if (
            "minimum" in question_lower
            or "lowest" in question_lower
            or "min" in question_lower
        ):
            return (
                f"The lowest {column.replace('_', ' ')} "
                f"is {formatted_value}."
            )

        return (
            f"The result for {column.replace('_', ' ')} "
            f"is {formatted_value}."
        )

    # ========================================================
    # RANKING / GROUPED RESULT
    # ========================================================

    if len(rows) >= 2 and len(columns) >= 2:

        category_column = columns[0]
        value_column = columns[1]

        first_row = rows[0]

        category = first_row.get(category_column)
        value = first_row.get(value_column)

        insight = (
            f"{category} has the highest "
            f"{value_column.replace('_', ' ')} "
            f"at {format_number(value)}."
        )

        # ----------------------------------------------------
        # Top 3 results
        # ----------------------------------------------------

        if len(rows) >= 3:

            top_items = []

            for row in rows[:3]:

                item = row.get(category_column)
                amount = row.get(value_column)

                top_items.append(
                    f"{item} ({format_number(amount)})"
                )

            insight += (
                " The top results are "
                + ", ".join(top_items)
                + "."
            )

        return insight

    # ========================================================
    # MULTIPLE ROWS
    # ========================================================

    return (
        f"The query returned {len(rows):,} results."
    )