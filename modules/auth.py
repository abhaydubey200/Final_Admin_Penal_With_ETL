import streamlit as st
from modules.database import get_snowflake_session

def authenticate_user(email, password_input):
    session = get_snowflake_session()
    if not session: return None

    clean_email = str(email).strip().lower()
    
    # Step 1: Check if user identity exists
    user_check = session.sql(f"""
        SELECT USER_ID, PASSWORD 
        FROM DIM_USERS 
        WHERE LOWER(TRIM(EMAIL)) = '{clean_email}' AND IS_ACTIVE = TRUE
    """).collect()
    
    if not user_check:
        return None

    u_id = user_check[0]['USER_ID']
    db_pw = str(user_check[0]['PASSWORD']).strip()

    # Step 2: Validate Password
    if str(password_input).strip() != db_pw:
        return None

    # Step 3: Verify Role Assignment
    query = f"""
        SELECT U.EMAIL, U.FULL_NAME, R.ROLE_NAME, R.CAN_EDIT_USERS
        FROM DIM_USERS U
        INNER JOIN USER_ROLE_MAPPING M ON U.USER_ID = M.USER_ID
        INNER JOIN DIM_ROLES R ON M.ROLE_NAME = R.ROLE_NAME
        WHERE U.USER_ID = '{u_id}'
    """
    
    try:
        results = session.sql(query).collect()
        if not results:
            st.warning(f"⚠️ Account exists but no role assigned to ID: {u_id}. Please contact Super Admin.")
            return None
            
        return results[0].as_dict()
    except Exception as e:
        st.error(f"Authentication System Error: {e}")
        return None