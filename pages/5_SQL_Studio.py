import streamlit as st
import pandas as pd
import snowflake.connector
import time
import socket

st.title("🧠 Enterprise SQL Studio")

# ---------------------------------------------------
# SAFETY CHECK (ADMIN ONLY)
# ---------------------------------------------------
user_info = st.session_state.get("user_info", {})

if not user_info.get("CAN_EDIT_USERS"):
    st.error("Access Denied.")
    st.stop()

# ---------------------------------------------------
# SNOWFLAKE CONNECTION (USING YOUR SECRETS FORMAT)
# ---------------------------------------------------
def get_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"]
    )

# ---------------------------------------------------
# SQL EDITOR UI
# ---------------------------------------------------
query = st.text_area("SQL Editor", height=250)

col1, col2 = st.columns(2)

with col1:
    execute = st.button("▶ Execute")

with col2:
    clear = st.button("🧹 Clear")

if clear:
    st.rerun()

# ---------------------------------------------------
# EXECUTION LOGIC
# ---------------------------------------------------
if execute:

    if not query.strip():
        st.warning("Please enter a SQL query.")
        st.stop()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        start_time = time.time()
        cursor.execute(query)
        execution_time = round(time.time() - start_time, 3)

        # SELECT queries
        if query.strip().lower().startswith("select"):
            rows = cursor.fetchmany(5000)
            columns = [col[0] for col in cursor.description]

            df = pd.DataFrame(rows, columns=columns)

            st.success(f"Query executed in {execution_time} seconds")
            st.dataframe(df, use_container_width=True)

        # Other queries (INSERT / UPDATE / DELETE / CREATE)
        else:
            conn.commit()
            st.success("Query executed successfully.")

        # ---------------------------------------------------
        # AUDIT LOGGING
        # ---------------------------------------------------
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)

        cursor.execute("""
            INSERT INTO AUDIT_LOGS 
            (ACTION_TYPE, ACTION_DETAILS, CHANGED_BY, HOST_IP, HOST_NAME)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            "SQL_EXECUTION",
            query,
            user_info.get("EMAIL"),
            host_ip,
            host_name
        ))

        conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Error: {e}")
