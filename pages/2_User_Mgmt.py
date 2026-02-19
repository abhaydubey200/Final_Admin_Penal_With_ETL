import streamlit as st
import pandas as pd
from modules.database import get_snowflake_session, update_user_in_snowflake

# --- PAGE CONFIG ---
st.set_page_config(page_title="DS Group | User Management", layout="wide")

if "user_info" not in st.session_state or st.session_state.user_info is None:
    st.warning("⚠️ Access Denied. Please login.")
    st.stop()

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
        .stActionButton { display: none; }
        .user-stat-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #007bff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

st.title("👥 User Administration Console")
st.caption("Manage employee access, modify permissions, and monitor account statuses across the DS Group ecosystem.")

session = get_snowflake_session()

if session:
    # --- FETCH DATA ---
    df = session.sql("SELECT USER_ID, FULL_NAME, EMAIL, DEPARTMENT, BRAND_ACCESS, IS_ACTIVE FROM DIM_USERS").to_pandas()
    
    # --- TOP ROW: STATUS SUMMARY ---
    total_users = len(df)
    active_users = df[df['IS_ACTIVE'] == True].shape[0]
    inactive_users = total_users - active_users
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Directory", total_users)
    with col2:
        st.metric("Active Accounts", active_users, delta="Online", delta_color="normal")
    with col3:
        st.metric("Deactivated", inactive_users, delta="- Accounts", delta_color="inverse")
    with col4:
        st.metric("Departments", df['DEPARTMENT'].nunique())

    st.divider()

    # --- SEARCH & FILTER BAR ---
    search_col, filter_col = st.columns([2, 1])
    with search_col:
        search_term = st.text_input("🔍 Quick Search", placeholder="Search by name, email, or employee ID...")
    with filter_col:
        dept_filter = st.multiselect("Filter by Department", options=df['DEPARTMENT'].unique().tolist())

    # Apply Filters
    filtered_df = df.copy()
    if search_term:
        filtered_df = filtered_df[
            filtered_df['FULL_NAME'].str.contains(search_term, case=False) | 
            filtered_df['EMAIL'].str.contains(search_term, case=False) |
            filtered_df['USER_ID'].astype(str).str.contains(search_term)
        ]
    if dept_filter:
        filtered_df = filtered_df[filtered_df['DEPARTMENT'].isin(dept_filter)]

    # --- DATA EDITOR MAKEOVER ---
    st.subheader("Directory Management")
    
    

    edited_df = st.data_editor(
        filtered_df,
        key="user_mgmt_editor",
        use_container_width=True,
        hide_index=True,
        disabled=["USER_ID", "EMAIL"],
        column_config={
            "USER_ID": st.column_config.TextColumn("Employee ID", width="small"),
            "FULL_NAME": st.column_config.TextColumn("Legal Name", width="medium"),
            "EMAIL": st.column_config.TextColumn("Corporate Email", width="medium"),
            "IS_ACTIVE": st.column_config.CheckboxColumn(
                "Active Status", 
                help="Toggle to activate/deactivate account",
                default=True
            ),
            "DEPARTMENT": st.column_config.SelectboxColumn(
                "Dept", 
                options=["IT", "Sales", "HR", "Marketing", "Finance", "Logistics"],
                width="small"
            ),
            "BRAND_ACCESS": st.column_config.SelectboxColumn(
                "Primary Brand", 
                options=["All", "Catch", "Pulse", "Pass Pass", "Chingles"],
                width="small"
            )
        }
    )

    # --- SYNC BUTTON ---
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col2:
        if st.button("🚀 Commit Changes to Snowflake", type="primary", use_container_width=True):
            changes = st.session_state["user_mgmt_editor"]["edited_rows"]
            if changes:
                admin_email = st.session_state.user_info['EMAIL']
                progress_bar = st.progress(0)
                
                for i, (row_idx, updates) in enumerate(changes.items()):
                    # Identify the correct User ID even after filtering
                    u_id = filtered_df.iloc[row_idx]['USER_ID']
                    update_user_in_snowflake(u_id, updates, admin_email)
                    progress_bar.progress((i + 1) / len(changes))
                
                st.success(f"✅ Successfully updated {len(changes)} user records!")
                st.rerun()
            else:
                st.info("No pending changes detected.")

else:
    st.error("Connection Error: Unable to sync with Snowflake directory.")