from dotenv import load_dotenv
import os
import google.generativeai as genai
import streamlit as st
import pandas as pd
import mysql.connector

# ✅ Load environment variables
load_dotenv()

# ✅ Configure Gemini with your API key from environment variables
api_key = os.getenv("Google_API_KEY")
if not api_key:
    st.error("Google API Key not found in environment variables!")
else:
    genai.configure(api_key=api_key)

# ✅ Correct model name (avoid NotFound error)
MODEL_NAME = "models/gemini-2.0-flash-lite"

# ✅ Gemini prompt with fully qualified table name
prompt = """
You are a SQL expert. Convert the user's natural language request into a valid SQL query.
Assume the database is MySQL and there is a table called 'sales_data_db.sales_data' with the following columns:
sale_date, Channel, Product_Name, City, Quantity, Sales.
Only return the SQL query. Do not include explanations or extra text.
...
(keep the rest of your examples as-is)
"""

# ✅ Function to get SQL query from Gemini
def get_gemini_response(question, prompt):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content([prompt, question])
        sql_query = response.text.strip()
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        return sql_query
    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return None

# ✅ Function to execute SQL query on MySQL
def read_mysql_query(sql, db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        conn.close()
        return rows, col_names
    except mysql.connector.Error as e:
        st.error(f"MySQL Error: {str(e)}")
        return [], []
    except Exception as e:
        st.error(f"General Error: {str(e)}")
        return [], []

# ✅ Function to list all tables
def list_tables(db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SHOW TABLES;")
        tables = [table[0] for table in cur.fetchall()]
        conn.close()
        return tables
    except mysql.connector.Error as e:
        st.error(f"MySQL Error while listing tables: {str(e)}")
        return []
    except Exception as e:
        st.error(f"General Error while listing tables: {str(e)}")
        return []

# ✅ Streamlit UI
st.set_page_config(page_title="SQL Assistant")
st.header("🤖 Gemini SQL Query Generator")

question = st.text_input("🔍 Ask your data question (in plain English):", key="input")
submit = st.button("Get SQL & Run")

# ✅ MySQL connection config (no Unix socket, no SSL for Windows)
db_config = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "Sonali1@2",
    "database": "sales_data_db"
}

if submit and question:
    with st.spinner("Generating SQL and fetching data..."):
        sql_query = get_gemini_response(question, prompt)

        if sql_query:
            st.subheader("🧠 Generated SQL Query:")
            st.code(sql_query, language="sql")

            # ✅ Proper table check (avoid tuple issue)
            tables = list_tables(db_config)
            if "sales_data" in tables:
                data, columns = read_mysql_query(sql_query, db_config)

                st.subheader("📊 Query Results:")
                if data:
                    df = pd.DataFrame(data, columns=columns)
                    st.dataframe(df)
                else:
                    st.warning("No data returned.")
            else:
                st.error("Table 'sales_data_db.sales_data' does not exist in the database.")
