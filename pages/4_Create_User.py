import streamlit as st
import time
from modules.database import create_new_snowflake_user

# --- PAGE CONFIG ---
st.set_page_config(page_title="DS Group | Provision User", layout="centered")

# --- RBAC CHECK ---
if "user_info" not in st.session_state or not st.session_state.user_info.get('CAN_EDIT_USERS'):
    st.error("🚫 **Unauthorized Access:** You do not have permission to provision new identities.")
    st.stop()

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
        .stForm {
            background-color: #6e6969;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            border: 1px solid #f0f2f6;
        }
        .step-header {
            color: #1e293b;
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }
    </style>
""", unsafe_allow_html=True)

st.title("➕ User Provisioning Portal")
st.write("Register a new employee into the DS Group ecosystem and assign their digital credentials.")

# --- FORM DESIGN ---
with st.form("user_onboarding_wizard", clear_on_submit=True):
    
    # SECTION 1: IDENTITY
    st.markdown('<div class="step-header">👤 Step 1: Employee Identity</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        u_id = st.text_input("Employee ID", placeholder="e.g., DS-9981")
        name = st.text_input("Full Name", placeholder="e.g., Vikram Singh")
    with c2:
        email = st.text_input("Corporate Email", placeholder="v.singh@dsgroup.com")
        dept = st.selectbox("Department", ["IT", "Sales", "Finance", "HR", "Marketing", "Logistics", "R&D"])

    st.markdown("---")

    # SECTION 2: ACCESS CONTROL
    st.markdown('<div class="step-header">🔐 Step 2: Access & Permissions</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        role = st.select_slider(
            "Security Role",
            options=["VIEWER", "ADMIN", "SUPER_ADMIN"],
            help="Determines page visibility and edit permissions."
        )
    with c4:
        brand = st.multiselect(
            "Brand Data Access",
            options=["Catch", "Pulse", "Pass Pass", "Chingles", "Mouth Freshener"],
            default=["Catch"]
        )

    st.markdown("---")

    # SECTION 3: SECURITY
    st.markdown('<div class="step-header">🛡️ Step 3: Security Credentials</div>', unsafe_allow_html=True)
    pw = st.text_input("Temporary Password", type="password", help="The user will be prompted to change this on first login.")
    
    # Password complexity visual aid
    if pw:
        if len(pw) < 6:
            st.warning("⚠️ Weak: Password should be at least 6 characters.")
        else:
            st.success("✅ Strong: Password meets complexity requirements.")

    st.markdown("###")

    # SUBMIT
    
    submit_btn = st.form_submit_button("🚀 Finalize & Provision Account", use_container_width=True)

    if submit_btn:
        if not (u_id and name and email and pw):
            st.error("🛑 **Validation Error:** Please complete all required fields before provisioning.")
        elif "@" not in email or "." not in email:
            st.error("🛑 **Validation Error:** Please enter a valid corporate email format.")
        else:
            with st.spinner("🔄 Communicating with Snowflake Security Layer..."):
                # Convert brand list to comma separated string for DB storage
                brand_str = ", ".join(brand) if brand else "None"
                
                success = create_new_snowflake_user(
                    u_id, name, email, dept, brand_str, role, pw, 
                    st.session_state.user_info['EMAIL']
                )
                
                if success:
                    st.balloons()
                    st.success(f"🎊 **Success!** Account for **{name}** has been successfully provisioned.")
                    st.info("The new user can now log in using their corporate email and the temporary password provided.")
                    time.sleep(2)
                    # st.rerun()  # Optional: Refresh to clear form

# --- SIDEBAR GUIDANCE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/100/add-user-group-man-man.png")
    st.subheader("Onboarding Tips")
    st.write("""
    - **Roles:** 
    - **Auditing:**
    - **Next Steps:**
    """)