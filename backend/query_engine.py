"""
Natural-language -> SQL -> answer pipeline for AquaGen AI.

Rewritten for Phase 2: queries Supabase Postgres (ocean_data table) instead
of the old local SQLite file. Key differences from the original:

1. Uses the app's existing SQLAlchemy engine (app.db.session.engine) rather
   than sqlite3.connect() — this is the same connection your FastAPI routes
   already use, so it works identically locally and on Render.

2. The LLM prompt describes the REAL Postgres schema (latitude, longitude,
   profile_date, temperature_c, salinity_psu, pressure_dbar) instead of the
   old SQLite column names.

3. Result columns are renamed back to short, frontend-friendly names
   (lat, lon, date, depth, temperature, salinity) in Python, AFTER the query
   runs — not by relying on the LLM to alias correctly every time. This is
   what keeps App.jsx's map/chart rendering working without any frontend
   changes.

4. Generated SQL is validated before execution: only SELECT statements are
   allowed, and known-dangerous keywords are blocked. This closes an
   otherwise-open SQL injection surface (an LLM turning free text into SQL
   with no guardrails).

5. Every question is logged to query_log (success or failure), matching the
   schema built in Phase 1.
"""
import os
import re
import time

import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.models.query_log import QueryLog

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Schema description shown to the LLM ---
SCHEMA_DESCRIPTION = """
Table: ocean_data (PostgreSQL)
Columns:
- float_id (text): ARGO float platform number
- cycle_number (integer, nullable): profile cycle number
- profile_date (timestamptz): when the measurement was taken
- latitude (double precision): -30 to 30
- longitude (double precision): 50 to 100
- pressure_dbar (double precision, nullable): depth proxy in meters, 0 to 100
- temperature_c (double precision, nullable): ocean temperature in Celsius
- salinity_psu (double precision, nullable): salinity in PSU
- data_mode (text, nullable): 'R' (realtime), 'D' (delayed-mode), or 'legacy'
"""

# Maps real Postgres column names -> short names the frontend already expects.
# Applied to query results regardless of whether the LLM aliased them itself.
FRIENDLY_COLUMN_NAMES = {
    "latitude": "lat",
    "longitude": "lon",
    "profile_date": "date",
    "pressure_dbar": "depth",
    "temperature_c": "temperature",
    "salinity_psu": "salinity",
}

# --- SQL validation ---
FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "grant", "revoke", "exec", "execute", "call",
    "into outfile", "load_file", "pg_read_file", "pg_sleep",
]


class UnsafeSQLError(Exception):
    pass


def validate_sql(sql: str) -> None:
    """
    Raises UnsafeSQLError if the SQL isn't a single, plain SELECT statement.
    This is a defense-in-depth check, not a full SQL parser — it exists to
    stop an LLM-generated query from doing anything destructive, not to
    replace proper least-privilege database permissions.
    """
    cleaned = sql.strip().rstrip(";").strip()

    if not re.match(r"^\s*select\b", cleaned, re.IGNORECASE):
        raise UnsafeSQLError("Only SELECT statements are allowed.")

    # Reject stacked statements (a second statement after a semicolon).
    if ";" in cleaned:
        raise UnsafeSQLError("Multiple SQL statements are not allowed.")

    lowered = cleaned.lower()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            raise UnsafeSQLError(f"Query contains a disallowed keyword: '{keyword}'.")


def rename_to_friendly_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        col: FRIENDLY_COLUMN_NAMES[col] for col in df.columns if col in FRIENDLY_COLUMN_NAMES
    }
    return df.rename(columns=rename_map)


def query_database(sql: str) -> pd.DataFrame | str:
    """
    Validates and executes SQL against Supabase. Returns a DataFrame with
    frontend-friendly column names, or an error string on failure.
    """
    try:
        validate_sql(sql)
    except UnsafeSQLError as e:
        return f"Query rejected: {e}"

    try:
        df = pd.read_sql_query(text(sql), engine)
        return rename_to_friendly_columns(df)
    except Exception as e:
        return str(e)


def log_query(
    user_query: str,
    generated_sql: str | None,
    execution_time_ms: int,
    success: bool,
    error_message: str | None,
    result_row_count: int | None,
) -> None:
    """Best-effort logging — a logging failure should never break the user's response."""
    db = SessionLocal()
    try:
        db.add(
            QueryLog(
                user_query=user_query,
                generated_sql=generated_sql,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message,
                result_row_count=result_row_count,
            )
        )
        db.commit()
    except Exception as log_err:
        print(f"Warning: failed to write query_log entry: {log_err}")
        db.rollback()
    finally:
        db.close()


def ask_aquagen(user_question: str) -> dict:
    start_time = time.monotonic()
    sql_query = None

    try:
        # Step 1: Ask LLM to convert question to SQL
        sql_prompt = f"""
        You are an ocean data expert. Convert the user's question into a valid PostgreSQL query.
        Only return the SQL query, nothing else. No explanation, no markdown, just raw SQL.

        Database schema:
        {SCHEMA_DESCRIPTION}

        User question: {user_question}

        Important rules:
        - This is PostgreSQL, not SQLite. Use PostgreSQL syntax (e.g. to_char() for date formatting, not strftime()).
        - For questions asking for maximum, minimum, average, or count values, use MAX(), MIN(), AVG(), COUNT() — do NOT use ORDER BY with LIMIT.
        - Only add LIMIT 50 for questions asking to "show", "list", or "display" multiple records.
        - For "what is the highest/maximum X" questions, always use SELECT MAX(X) FROM ocean_data.
        - For map or location questions asking for lat/lon, use:
          SELECT DISTINCT latitude, longitude, AVG(temperature_c) AS temperature FROM ocean_data GROUP BY latitude, longitude LIMIT 50
        - For month-based aggregation, use:
          SELECT to_char(profile_date, 'YYYY-MM') AS month, AVG(temperature_c) AS temperature FROM ocean_data GROUP BY month ORDER BY month
        - Only generate a single SELECT statement. Never use INSERT, UPDATE, DELETE, DROP, or any other data-modifying statement.

        SQL query:
        """

        sql_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": sql_prompt}],
            max_tokens=300,
        )

        sql_query = sql_response.choices[0].message.content.strip()
        # Strip markdown code fences if the model adds them despite instructions
        sql_query = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql_query, flags=re.IGNORECASE).strip()
        print(f"\nGenerated SQL: {sql_query}")

        # Step 2: Execute the SQL
        result = query_database(sql_query)

        if isinstance(result, str):
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            log_query(user_question, sql_query, execution_time_ms, False, result, None)
            return {
                "error": result,
                "sql": sql_query,
                "explanation": "Sorry, I couldn't process that query. Please try rephrasing your question.",
            }

        # Step 3: Ask LLM to explain the result
        explain_prompt = f"""
        The user asked: "{user_question}"
        The SQL query returned this data (showing first 20 rows):
        {result.head(20).to_string()}

        Give a clear, friendly 2-3 sentence explanation of what this data means.
        """

        explain_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": explain_prompt}],
            max_tokens=200,
        )

        explanation = explain_response.choices[0].message.content.strip()

        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        log_query(user_question, sql_query, execution_time_ms, True, None, len(result))

        return {
            "question": user_question,
            "sql": sql_query,
            "data": result.to_dict(orient="records"),
            "explanation": explanation,
        }

    except Exception as e:
        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        log_query(user_question, sql_query, execution_time_ms, False, str(e), None)
        return {
            "error": str(e),
            "sql": sql_query,
            "explanation": "Something went wrong while processing your question. Please try again.",
        }


# Test it
if __name__ == "__main__":
    test_question = "What is the average temperature in the Indian Ocean?"
    print(f"Question: {test_question}")
    result = ask_aquagen(test_question)
    print(f"\nExplanation: {result.get('explanation')}")
    print(f"\nData: {result.get('data', [])[:3]}")
