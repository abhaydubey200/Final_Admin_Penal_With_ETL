import streamlit as st
import socket
from snowflake.snowpark import Session

@st.cache_resource
def get_snowflake_session():
    try:
        return Session.builder.configs(st.secrets["snowflake"]).create()
    except Exception as e:
        st.error(f"Snowflake Connection Error: {e}")
        return None

def log_admin_action(admin_email, action_type, details):
    session = get_snowflake_session()
    if session:
        try:
            host_name = socket.gethostname()
            host_ip = socket.gethostbyname(host_name)
            clean_details = str(details).replace("'", "''") 
            query = f"""
                INSERT INTO AUDIT_LOGS (ACTION_TYPE, ACTION_DETAILS, CHANGED_BY, HOST_IP, HOST_NAME)
                VALUES ('{action_type}', '{clean_details}', '{admin_email}', '{host_ip}', '{host_name}')
            """
            session.sql(query).collect()
        except Exception as e:
            print(f"Audit Log Failed: {e}")

def create_new_snowflake_user(u_id, name, email, dept, brand, role, pw, admin):
    session = get_snowflake_session()
    if not session: return False
    try:
        # 1. CREATE USER IDENTITY
        session.sql(f"""
            INSERT INTO DIM_USERS (USER_ID, FULL_NAME, EMAIL, DEPARTMENT, BRAND_ACCESS, IS_ACTIVE, PASSWORD) 
            VALUES ('{u_id}', '{name}', '{email}', '{dept}', '{brand}', TRUE, '{pw}')
        """).collect()
        
        # 2. CREATE ROLE LINK (Crucial for Login)
        session.sql(f"""
            INSERT INTO USER_ROLE_MAPPING (USER_ID, ROLE_NAME) 
            VALUES ('{u_id}', '{role}')
        """).collect()
        
        log_admin_action(admin, "CREATE_USER", f"Provisioned: {email} with role {role}")
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def update_user_in_snowflake(user_id, updated_fields, admin_email):
    session = get_snowflake_session()
    if not session: return False
    set_parts = [f"{col} = '{val}'" if isinstance(val, str) else f"{col} = {val}" for col, val in updated_fields.items()]
    query = f"UPDATE DIM_USERS SET {', '.join(set_parts)} WHERE USER_ID = '{user_id}'"
    try:
        session.sql(query).collect()
        log_admin_action(admin_email, "UPDATE_USER", f"Modified: {user_id}")
        return True
    except Exception as e:
        st.error(f"Update failed: {e}")
        return False