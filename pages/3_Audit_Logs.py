import streamlit as st
import pandas as pd
from modules.database import get_snowflake_session

# --- PAGE CONFIG ---
st.set_page_config(page_title="DS Group | Security Audit", layout="wide")

if "user_info" not in st.session_state or st.session_state.user_info is None:
    st.warning("⚠️ Session expired. Please login again.")
    st.stop()

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .audit-card {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e2e8f0;
            margin-bottom: 10px;
        }
        .stDataFrame {
            border: 1px solid #e2e8f0;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Security Forensic Logs")
st.write("Complete immutable trail of all administrative actions, system modifications, and access events.")

session = get_snowflake_session()

if session:
    # --- FETCH DATA ---
    query = """
        SELECT A.AUDIT_ID, A.ACTION_TYPE, A.ACTION_AT, A.CHANGED_BY, 
               A.HOST_IP, A.HOST_NAME, A.ACTION_DETAILS 
        FROM AUDIT_LOGS A ORDER BY A.ACTION_AT DESC
    """
    df = session.sql(query).to_pandas()
    df['ACTION_AT'] = pd.to_datetime(df['ACTION_AT'])

    # --- TOP ROW: SECURITY METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    
    # 24-hour activity check
    last_24h = df[df['ACTION_AT'] > (pd.Timestamp.now() - pd.Timedelta(days=1))].shape[0]
    unique_admins = df['CHANGED_BY'].nunique()
    critical_events = df[df['ACTION_TYPE'].str.contains('DELETE|UPDATE|CREATE', case=False, na=False)].shape[0]

    with m1:
        st.metric("Total Logs", len(df))
    with m2:
        st.metric("Last 24h Activity", last_24h, delta="Events")
    with m3:
        st.metric("Unique Operators", unique_admins)
    with m4:
        st.metric("Provisioning Events", critical_events, delta_color="inverse")

    st.divider()

    # --- FILTERING SIDEBAR ---
    with st.sidebar:
        st.header("🔍 Audit Filters")
        event_filter = st.multiselect("Event Type", options=df['ACTION_TYPE'].unique())
        admin_filter = st.multiselect("Operator", options=df['CHANGED_BY'].unique())
        date_range = st.date_input("Date Range", [])

    # Apply Filters
    filtered_df = df.copy()
    if event_filter:
        filtered_df = filtered_df[filtered_df['ACTION_TYPE'].isin(event_filter)]
    if admin_filter:
        filtered_df = filtered_df[filtered_df['CHANGED_BY'].isin(admin_filter)]
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['ACTION_AT'].dt.date >= start_date) & 
            (filtered_df['ACTION_AT'].dt.date <= end_date)
        ]

    # --- MAIN LOG VIEW ---
    tab1, tab2 = st.tabs(["📑 Detailed Logs", "📊 Activity Heatmap"])

    with tab1:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "AUDIT_ID": st.column_config.TextColumn("ID", width="small"),
                "ACTION_TYPE": st.column_config.TextColumn("Event Type"),
                "ACTION_AT": st.column_config.DatetimeColumn("Timestamp", format="D MMM, hh:mm a"),
                "CHANGED_BY": st.column_config.TextColumn("Operator Email"),
                "HOST_IP": st.column_config.TextColumn("Source IP", width="medium"),
                "HOST_NAME": st.column_config.TextColumn("Device Name"),
                "ACTION_DETAILS": st.column_config.TextColumn("Metadata/Payload", width="large")
            }
        )

    with tab2:
        # Mini-viz for the audit page
        st.subheader("Event Frequency")
        if not filtered_df.empty:
            type_counts = filtered_df['ACTION_TYPE'].value_counts().reset_index()
            import plotly.express as px
            fig = px.pie(type_counts, values='count', names='ACTION_TYPE', hole=0.7, 
                         color_discrete_sequence=px.colors.sequential.Reds_r)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Apply filters to view heatmap.")

    # --- EXPORT FEATURE ---
    st.divider()
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Forensic Report (CSV)",
        data=csv,
        file_name="ds_security_audit.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.error("Audit System Offline: Connection to Snowflake failed.")