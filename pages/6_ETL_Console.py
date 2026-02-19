import streamlit as st
import snowflake.connector
import pandas as pd
import pyodbc
import mysql.connector
import time
import socket

st.title("🔄 Enterprise Multi-Source ETL Console")

# ==========================================================
# SESSION CHECK
# ==========================================================
if "user_info" not in st.session_state:
    st.error("Session expired.")
    st.stop()

user_info = st.session_state["user_info"]

if not user_info.get("CAN_EDIT_USERS"):
    st.error("Access Denied.")
    st.stop()

# ==========================================================
# SNOWFLAKE CONNECTION
# ==========================================================
def get_sf_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        role=st.secrets["snowflake"]["role"]
    )

sf_conn = get_sf_connection()
sf_cursor = sf_conn.cursor()

# ==========================================================
# TABS
# ==========================================================
tab1, tab2, tab3 = st.tabs([
    "🔁 Snowflake → Snowflake",
    "📁 File Upload",
    "🌐 External DB → Snowflake"
])

# ==========================================================
# TAB 1 - SNOWFLAKE TO SNOWFLAKE
# ==========================================================
with tab1:

    st.subheader("Snowflake Internal ETL")

    sf_cursor.execute("SHOW DATABASES")
    databases = [row[1] for row in sf_cursor.fetchall()]

    source_db = st.selectbox("Source Database", databases, key="sf_src_db")
    target_db = st.selectbox("Target Database", databases, key="sf_tgt_db")

    sf_cursor.execute(f"SHOW SCHEMAS IN DATABASE {source_db}")
    schemas = [row[1] for row in sf_cursor.fetchall()]

    source_schema = st.selectbox("Source Schema", schemas)
    target_schema = st.selectbox("Target Schema", schemas)

    sf_cursor.execute(f"SHOW TABLES IN {source_db}.{source_schema}")
    tables = [row[1] for row in sf_cursor.fetchall()]

    source_table = st.selectbox("Source Table", tables)
    target_table = st.text_input("Target Table Name")

    load_type = st.radio("Load Type", ["APPEND", "OVERWRITE"])

    if st.button("🚀 Run Snowflake ETL"):

        try:
            start = time.time()
            query = f"SELECT * FROM {source_db}.{source_schema}.{source_table}"
            full_target = f"{target_db}.{target_schema}.{target_table}"

            if load_type == "OVERWRITE":
                sf_cursor.execute(f"CREATE OR REPLACE TABLE {full_target} AS {query}")
            else:
                sf_cursor.execute(f"INSERT INTO {full_target} {query}")

            sf_conn.commit()
            st.success(f"Completed in {round(time.time()-start,2)} sec")

        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================================
# TAB 2 - FILE UPLOAD
# ==========================================================
with tab2:

    st.subheader("Upload CSV / Excel")

    file = st.file_uploader("Upload File", type=["csv", "xlsx"])

    if file:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        st.dataframe(df.head(100))
        st.info(f"Rows: {len(df)} | Columns: {len(df.columns)}")

        sf_cursor.execute("SHOW DATABASES")
        databases = [row[1] for row in sf_cursor.fetchall()]

        target_db = st.selectbox("Target Database", databases, key="file_db")
        sf_cursor.execute(f"SHOW SCHEMAS IN DATABASE {target_db}")
        schemas = [row[1] for row in sf_cursor.fetchall()]

        target_schema = st.selectbox("Target Schema", schemas, key="file_schema")
        target_table = st.text_input("Target Table Name", key="file_table")

        if st.button("🚀 Upload to Snowflake"):

            try:
                df.columns = [col.upper() for col in df.columns]
                full_table = f"{target_db}.{target_schema}.{target_table}"

                sf_cursor.execute(
                    f"CREATE OR REPLACE TABLE {full_table} AS SELECT * FROM VALUES {tuple(df.iloc[0])}"
                )

                for _, row in df.iterrows():
                    placeholders = ", ".join(["%s"] * len(row))
                    sf_cursor.execute(
                        f"INSERT INTO {full_table} VALUES ({placeholders})",
                        tuple(row)
                    )

                sf_conn.commit()
                st.success("File uploaded successfully.")

            except Exception as e:
                st.error(f"Upload Failed: {e}")

# ==========================================================
# TAB 3 - EXTERNAL DATABASE ETL
# ==========================================================
with tab3:

    st.subheader("External Database → Snowflake")

    db_type = st.selectbox("Select Source Database Type", ["MSSQL", "MySQL"])

    host = st.text_input("Host")
    port = st.text_input("Port")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("🔌 Connect to Source"):

        try:
            if db_type == "MSSQL":
                ext_conn = pyodbc.connect(
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={host},{port};"
                    f"UID={username};PWD={password}"
                )
                db_query = "SELECT name FROM sys.databases"

            else:
                ext_conn = mysql.connector.connect(
                    host=host,
                    port=int(port),
                    user=username,
                    password=password
                )
                db_query = "SHOW DATABASES"

            ext_cursor = ext_conn.cursor()
            ext_cursor.execute(db_query)
            dbs = [row[0] for row in ext_cursor.fetchall()]

            st.session_state["ext_conn"] = ext_conn
            st.session_state["ext_dbs"] = dbs

            st.success("Connected Successfully")

        except Exception as e:
            st.error(f"Connection Failed: {e}")

    # After connection
    if "ext_dbs" in st.session_state:

        ext_conn = st.session_state["ext_conn"]
        ext_cursor = ext_conn.cursor()

        source_db = st.selectbox("Source Database", st.session_state["ext_dbs"])

        if db_type == "MSSQL":
            ext_cursor.execute(f"USE {source_db}")
            ext_cursor.execute(
                "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
            )
            tables = [f"{row[0]}.{row[1]}" for row in ext_cursor.fetchall()]
        else:
            ext_cursor.execute(f"USE {source_db}")
            ext_cursor.execute("SHOW TABLES")
            tables = [row[0] for row in ext_cursor.fetchall()]

        source_table = st.selectbox("Source Table", tables)

        # Snowflake Target
        sf_cursor.execute("SHOW DATABASES")
        databases = [row[1] for row in sf_cursor.fetchall()]

        target_db = st.selectbox("Target Database", databases, key="ext_sf_db")
        sf_cursor.execute(f"SHOW SCHEMAS IN DATABASE {target_db}")
        schemas = [row[1] for row in sf_cursor.fetchall()]

        target_schema = st.selectbox("Target Schema", schemas, key="ext_sf_schema")
        target_table = st.text_input("Target Table Name", key="ext_sf_table")

        load_type = st.radio("Load Type", ["APPEND", "OVERWRITE"], key="ext_load")

        if st.button("🚀 Run External ETL"):

            try:
                start = time.time()

                df = pd.read_sql(f"SELECT * FROM {source_table}", ext_conn)

                df.columns = [col.upper() for col in df.columns]
                full_target = f"{target_db}.{target_schema}.{target_table}"

                if load_type == "OVERWRITE":
                    sf_cursor.execute(
                        f"CREATE OR REPLACE TABLE {full_target} AS SELECT * FROM VALUES {tuple(df.iloc[0])}"
                    )

                for _, row in df.iterrows():
                    placeholders = ", ".join(["%s"] * len(row))
                    sf_cursor.execute(
                        f"INSERT INTO {full_target} VALUES ({placeholders})",
                        tuple(row)
                    )

                sf_conn.commit()

                st.success(
                    f"Loaded {len(df)} rows in {round(time.time()-start,2)} sec"
                )

            except Exception as e:
                st.error(f"ETL Failed: {e}")

sf_cursor.close()
sf_conn.close()
