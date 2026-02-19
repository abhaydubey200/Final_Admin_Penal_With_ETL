import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from modules.database import get_snowflake_session

# --- PAGE CONFIG ---
st.set_page_config(page_title="DS Group | Dashboard", layout="wide", initial_sidebar_state="expanded")

if "user_info" not in st.session_state or st.session_state.user_info is None:
    st.warning("⚠️ Please login to access the Command Center.")
    st.stop()

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
    <style>
        /* Main background and font */
        .main { background-color: #f4f7f9; }
        
        /* Metric Card Styling */
        div[data-testid="stMetric"] {
            background-color: #4d4949;
            border-radius: 10px;
            padding: 15px 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #eef2f6;
        }
        
        /* Metric Labels */
        div[data-testid="stMetricLabel"] {
            color: #64748b !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Metric Values */
        div[data-testid="stMetricValue"] {
            color: #1e293b !important;
            font-size: 32px !important;
        }

        /* Subheader styling */
        .stSubheader {
            color: #334155;
            font-weight: 700;
        }
    </style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("📊 DS Group Command Center")
    st.caption(f"Welcome back, **{st.session_state.user_info['FULL_NAME']}**. Here is the latest organizational pulse.")
with c2:
    st.info(f"📍 **Role:** {st.session_state.user_info['ROLE_NAME']}")

session = get_snowflake_session()

if session:
    # --- DATA FETCHING ---
    df_users = session.sql("SELECT DEPARTMENT, BRAND_ACCESS, IS_ACTIVE FROM DIM_USERS").to_pandas()
    df_audit = session.sql("SELECT ACTION_TYPE, ACTION_AT, CHANGED_BY FROM AUDIT_LOGS ORDER BY ACTION_AT DESC LIMIT 100").to_pandas()

    # --- TOP ROW: KPI CARDS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Workforce", len(df_users), delta="Registered")
    m2.metric("Active Sessions", df_users[df_users['IS_ACTIVE']==True].shape[0], delta="Online")
    m3.metric("Portfolios", df_users['BRAND_ACCESS'].nunique(), delta="Live Brands")
    m4.metric("Admin Actions", len(df_audit), delta="Last 24h")

    st.markdown("###") # Vertical Spacing

    # --- MIDDLE ROW: ANALYTICS VISUALS ---
    col_left, col_right = st.columns([1.2, 0.8])

    with col_left:
        with st.container(border=True):
            st.subheader("🏢 Workforce Distribution by Department")
            # Creating a modern horizontal bar chart
            dept_counts = df_users['DEPARTMENT'].value_counts().reset_index()
            dept_counts.columns = ['Dept', 'Count']
            
            fig_dept = px.bar(
                dept_counts, 
                x='Count', y='Dept', 
                orientation='h',
                color='Count',
                color_continuous_scale='Blues',
                text_auto=True,
                template="plotly_white"
            )
            fig_dept.update_layout(showlegend=False, height=350, margin=dict(l=0, r=20, t=20, b=0))
            st.plotly_chart(fig_dept, use_container_width=True)

    with col_right:
        with st.container(border=True):
            st.subheader("🎯 Brand Penetration")
            brand_counts = df_users['BRAND_ACCESS'].value_counts()
            
            fig_brand = px.pie(
                values=brand_counts.values, 
                names=brand_counts.index,
                hole=0.6,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_brand.update_traces(textinfo='percent+label')
            fig_brand.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), showlegend=False)
            st.plotly_chart(fig_brand, use_container_width=True)

    # --- BOTTOM ROW: ACTIVITY FEED ---
    st.markdown("###")
    st.subheader("🛡️ Recent Security Activity")
    
    if not df_audit.empty:
        # Transforming Audit logs into a clean, readable feed
        df_audit['ACTION_AT'] = pd.to_datetime(df_audit['ACTION_AT']).dt.strftime('%d %b, %H:%M')
        
        # Displaying with Styled Table
        st.dataframe(
            df_audit.head(10),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ACTION_AT": "Time",
                "ACTION_TYPE": "Event Type",
                "CHANGED_BY": st.column_config.TextColumn("Initiated By", help="The admin who performed the action"),
                "ACTION_DETAILS": "System Log"
            }
        )
    else:
        st.info("No recent system actions recorded.")

else:
    st.error("❌ Unable to connect to Snowflake. Please verify your connection secrets.")