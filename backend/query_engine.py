import sqlite3
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def query_database(sql):
    conn = sqlite3.connect("ocean_data.db")
    try:
        df = __import__("pandas").read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception as e:
        conn.close()
        return str(e)

def ask_aquagen(user_question):
    # Step 1: Ask LLM to convert question to SQL
    schema = """
    Table: ocean_data
    Columns:
    - date (text): datetime string e.g. '2023-01-01T03:23:36Z'
    - lat (real): latitude (-30 to 30)
    - lon (real): longitude (50 to 100)
    - depth (real): depth in meters (0 to 100)
    - temperature (real): ocean temperature in Celsius
    - salinity (real): salinity in PSU
    """

    sql_prompt = f"""
    You are an ocean data expert. Convert the user's question into a valid SQLite SQL query.
    Only return the SQL query, nothing else. No explanation, no markdown, just raw SQL.

    Database schema:
    {schema}

    User question: {user_question}

    Important rules:
    - For questions asking for maximum, minimum, average, or count values, use MAX(), MIN(), AVG(), COUNT() - do NOT use ORDER BY with LIMIT
    - Only add LIMIT 50 for questions asking to "show", "list", or "display" multiple records
    - For "what is the highest/maximum X" questions, always use SELECT MAX(X) FROM ocean_data
    - For map or location questions asking for lat and lon, use SELECT DISTINCT lat, lon, AVG(temperature) as temperature FROM ocean_data GROUP BY lat, lon LIMIT 50

    SQL query:
    """

    sql_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": sql_prompt}],
        max_tokens=300
    )

    sql_query = sql_response.choices[0].message.content.strip()
    print(f"\nGenerated SQL: {sql_query}")

    # Step 2: Execute the SQL
    result = query_database(sql_query)

    if isinstance(result, str):
        return {"error": result, "sql": sql_query}

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
        max_tokens=200
    )

    explanation = explain_response.choices[0].message.content.strip()

    return {
        "question": user_question,
        "sql": sql_query,
        "data": result.to_dict(orient="records"),
        "explanation": explanation
    }

# Test it
if __name__ == "__main__":
    test_question = "What is the average temperature in the Indian Ocean?"
    print(f"Question: {test_question}")
    result = ask_aquagen(test_question)
    print(f"\nExplanation: {result['explanation']}")
    print(f"\nData: {result['data'][:3]}")