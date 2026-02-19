import streamlit as st
from modules.auth import authenticate_user

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="DS Group Portal", layout="wide")

# ---------------------------------------------------
# SESSION INIT
# ---------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}

# ===================================================
# LOGIN
# ===================================================
if not st.session_state.get("authenticated"):

    _, col2, _ = st.columns([1, 1.5, 1])

    with col2:
        st.title("🏢 DS Group Portal")

        with st.container(border=True):
            email = st.text_input("Corporate Email")
            pw = st.text_input("Password", type="password")

            if st.button("Secure Sign In", use_container_width=True):
                user_data = authenticate_user(email, pw)

                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["user_info"] = user_data
                    st.rerun()
                else:
                    st.error("Invalid Login.")

# ===================================================
# MAIN APP
# ===================================================
else:

    user_info = st.session_state.get("user_info", {})

    pages = [
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊", default=True)
    ]

    if user_info.get("CAN_EDIT_USERS"):

        pages.append(st.Page("pages/2_User_Mgmt.py", title="User Management", icon="👥"))
        pages.append(st.Page("pages/4_Create_User.py", title="Create User", icon="➕"))
        pages.append(st.Page("pages/3_Audit_Logs.py", title="Security Audit", icon="🛡️"))
        pages.append(st.Page("pages/5_SQL_Studio.py", title="SQL Studio", icon="🧠"))
        pages.append(st.Page("pages/6_ETL_Console.py", title="ETL Console", icon="🔄"))

    pg = st.navigation(pages)

    with st.sidebar:
        st.write(f"Logged in: **{user_info.get('FULL_NAME', 'Unknown')}**")

        if st.button("Sign Out"):
            st.session_state["authenticated"] = False
            st.session_state["user_info"] = {}
            st.rerun()

    pg.run()
