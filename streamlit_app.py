import streamlit as st
import requests
import streamlit.components.v1 as components

BASE_URL =  "https://accucare-production.up.railway.app"

st.set_page_config(page_title="AccuCare | Clinical Decision Support", layout="wide", page_icon="🩺")


# =========================================================
# THEME - warm rose/blush light mode, matching the AccuCare
# landing page (static/index.html). Streamlit renders its own
# DOM, so this styles the existing structure via data-testid
# selectors (documented, reasonably stable across versions)
# rather than restructuring anything - no layout logic below
# this block changes.
# =========================================================
def inject_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 50% -10%, #F7ECE9 0%, #FDF8F6 45%, #FDF8F6 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: rgba(247, 236, 233, 0.85);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(122, 59, 76, 0.15);
    }
    [data-testid="stSidebar"] * {
        color: #2B1E22;
    }

    h1, h2, h3 {
        font-family: 'Fraunces', serif !important;
        color: #7A3B4C !important;
        font-weight: 500 !important;
        text-shadow: none !important;
    }

    .accucare-hero {
        text-align: center;
        padding: 2rem 0 0.5rem 0;
    }
    .accucare-hero h1 {
        font-family: 'Fraunces', serif !important;
        font-size: clamp(3.5rem, 7vw, 5.5rem) !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em;
        color: #7A3B4C !important;
        -webkit-text-fill-color: #7A3B4C;
        margin-bottom: 0 !important;
        line-height: 1;
    }
    .accucare-subtitle {
        letter-spacing: 0.25em;
        text-transform: uppercase;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        color: #B9718A;
        margin-top: 0.6rem;
    }
    .accucare-hero-compact h1 {
        font-size: clamp(2rem, 4vw, 2.8rem) !important;
    }
    @keyframes dropIn {
        0% { opacity: 0; transform: translateY(-40px); }
        60% { opacity: 1; transform: translateY(6px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .accucare-hero h1 {
        animation: dropIn 0.9s cubic-bezier(.2,.8,.2,1) both;
    }
    .accucare-subtitle {
        animation: dropIn 0.9s cubic-bezier(.2,.8,.2,1) both;
        animation-delay: 0.15s;
    }
    .portal-lede {
        text-align: center;
        color: #6B5A5E;
        font-size: 1rem;
        max-width: 38ch;
        margin: 18px auto 0;
        animation: dropIn 0.9s cubic-bezier(.2,.8,.2,1) both;
        animation-delay: 0.3s;
    }
    .accucare-illustration {
        display: flex;
        justify-content: center;
        margin: 0.5rem 0 1.5rem 0;
    }
    .accucare-illustration svg {
        max-width: 620px;
        width: 100%;
    }
    .portal-cta {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(button[kind="primary"]) {
        display: flex;
        justify-content: center;
    }

    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
        background: #ffffff;
        color: #7A3B4C;
        border: 1.5px solid #B9718A;
        border-radius: 999px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        background: #F7ECE9;
        border-color: #7A3B4C;
        color: #5f2e3b;
    }
    button[kind="primary"] {
        background: #7A3B4C !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.9rem 2.8rem !important;
        font-size: 1.02rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        letter-spacing: 0.02em;
        box-shadow: 0 12px 30px -14px rgba(122, 59, 76, 0.5) !important;
    }
    button[kind="primary"]:hover {
        background: #5f2e3b !important;
        transform: translateY(-1px);
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    [data-baseweb="select"] > div {
        background-color: #FDF8F6 !important;
        border: 1.5px solid #E8DAD8 !important;
        border-radius: 8px !important;
        color: #2B1E22 !important;
        caret-color: #2B1E22 !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stNumberInput"] input:focus,
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: #B9718A !important;
        box-shadow: 0 0 0 3px rgba(185, 113, 138, 0.15) !important;
    }

  [data-testid="stExpander"], [data-testid="stChatMessage"], [data-testid="stForm"] {
    background: #ffffff !important;
    border: 1px solid #E8DAD8 !important;
    border-radius: 14px !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessageContent"] * {
    color: #2B1E22 !important;
    opacity: 1 !important;
}
    [data-testid="stExpander"]:hover {
        border-color: #B9718A !important;
        box-shadow: 0 12px 30px -20px rgba(122, 59, 76, 0.3);
    }

    [data-baseweb="tab-list"] {
        gap: 8px;
    }
    [role="tablist"] [role="tab"],
    [role="tablist"] [role="tab"] *,
    [data-baseweb="tab-list"] [data-baseweb="tab"],
    [data-baseweb="tab-list"] [data-baseweb="tab"] *,
    [data-testid="stTabs"] button,
    [data-testid="stTabs"] button * {
        color: #2B1E22 !important;
        fill: #2B1E22 !important;
    }
    [role="tablist"] [aria-selected="true"],
    [role="tablist"] [aria-selected="true"] *,
    [data-baseweb="tab-list"] [aria-selected="true"],
    [data-baseweb="tab-list"] [aria-selected="true"] * {
        color: #000000 !important;
        fill: #000000 !important;
        font-weight: 700 !important;
    }
    [data-baseweb="tab-highlight"] {
        background-color: #7A3B4C !important;
    }
    [data-testid="stAlert"] {
        border-radius: 10px !important;
    }

    [data-testid="stChatInput"] button {
        background-color: #2B1E22 !important;
        border: none !important;
        border-radius: 8px !important;
    }
    [data-testid="stChatInput"] button svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }

    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
        color: #2B1E22 !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)


inject_theme()

# =========================================================
# HERO ILLUSTRATION - kept as a fallback/unused asset. The
# live login screen now shows the doctor photo instead (see
# show_login_page), but this SVG is left defined in case you
# want to switch back later.
# =========================================================
HERO_ILLUSTRATION_SVG = """
<div class="accucare-illustration">
<svg viewBox="0 0 700 340" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="350" cy="312" rx="290" ry="16" fill="#7A3B4C" opacity="0.08"/>

  <rect x="65" y="215" width="225" height="10" rx="3" fill="#F7ECE9" stroke="#7A3B4C" stroke-width="1.5" opacity="0.9"/>
  <line x1="85" y1="225" x2="85" y2="268" stroke="#B9718A" stroke-width="6"/>
  <line x1="262" y1="225" x2="262" y2="268" stroke="#B9718A" stroke-width="6"/>

  <rect x="130" y="176" width="92" height="56" rx="4" fill="#FDF8F6" stroke="#7A3B4C" stroke-width="2"/>
  <rect x="136" y="182" width="80" height="41" rx="2" fill="#F7ECE9"/>
  <rect x="119" y="232" width="112" height="7" rx="2" fill="#F7ECE9" stroke="#7A3B4C" stroke-width="1.2"/>
  <line x1="145" y1="194" x2="207" y2="194" stroke="#B9718A" stroke-width="2" opacity="0.85"/>
  <line x1="145" y1="204" x2="192" y2="204" stroke="#B9718A" stroke-width="2" opacity="0.6"/>
  <line x1="145" y1="214" x2="202" y2="214" stroke="#B9718A" stroke-width="2" opacity="0.4"/>

  <path d="M 52 240 Q 52 198 88 198" stroke="#B9718A" stroke-width="6" fill="none"/>
  <line x1="52" y1="240" x2="52" y2="292" stroke="#B9718A" stroke-width="6"/>

  <g>
    <circle cx="85" cy="148" r="22" fill="#F7ECE9" stroke="#7A3B4C" stroke-width="2.5"/>
    <path d="M 54 233 Q 49 178 85 173 Q 121 178 119 233 Z" fill="#F7ECE9" stroke="#7A3B4C" stroke-width="2.5"/>
    <path d="M 96 188 Q 132 194 142 217" stroke="#7A3B4C" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M 64 231 Q 62 250 42 254" stroke="#7A3B4C" stroke-width="7" fill="none" stroke-linecap="round"/>
    <path d="M 107 231 Q 112 250 88 258" stroke="#7A3B4C" stroke-width="7" fill="none" stroke-linecap="round"/>
  </g>
  <path d="M 74 173 Q 74 194 85 197 Q 96 194 96 173" stroke="#B9718A" stroke-width="2" fill="none" opacity="0.7"/>

  <g opacity="0.85">
    <circle cx="348" cy="138" r="3" fill="#B9718A"/>
    <circle cx="378" cy="126" r="3" fill="#B9718A"/>
    <circle cx="408" cy="138" r="3" fill="#B9718A"/>
    <path d="M 328 150 Q 378 96 432 150" stroke="#B9718A" stroke-width="1.5" fill="none" stroke-dasharray="4 6" opacity="0.6"/>
  </g>
  <g>
    <rect x="332" y="150" width="136" height="42" rx="14" fill="#7A3B4C" stroke="#7A3B4C" stroke-width="1.8"/>
    <path d="M 352 192 L 342 206 L 364 192 Z" fill="#7A3B4C" stroke="#7A3B4C" stroke-width="1.8"/>
    <text x="400" y="176" font-family="'Inter', sans-serif" font-size="12" fill="#ffffff" text-anchor="middle">"any precautions?"</text>
  </g>

  <path d="M 612 240 Q 612 188 572 188" stroke="#B9718A" stroke-width="6" fill="none"/>
  <line x1="612" y1="240" x2="612" y2="292" stroke="#B9718A" stroke-width="6"/>
  <line x1="522" y1="272" x2="622" y2="272" stroke="#B9718A" stroke-width="5" opacity="0.5"/>

  <g>
    <circle cx="565" cy="148" r="22" fill="#F7ECE9" stroke="#B9718A" stroke-width="2.5"/>
    <path d="M 530 258 Q 525 183 565 176 Q 605 183 602 258 Z" fill="#F7ECE9" stroke="#B9718A" stroke-width="2.5"/>
    <path d="M 545 198 Q 500 203 480 218" stroke="#B9718A" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M 545 256 Q 545 273 570 276" stroke="#B9718A" stroke-width="7" fill="none" stroke-linecap="round"/>
    <path d="M 585 256 Q 590 273 615 273" stroke="#B9718A" stroke-width="7" fill="none" stroke-linecap="round"/>
  </g>
</svg>
</div>
"""

# --- Session state setup ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "doctor_name" not in st.session_state:
    st.session_state.doctor_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = None

# The landing page's "Enter Clinical Portal" link (inside the embedded
# iframe) can't call Streamlit's Python code directly - it's a separate
# HTML page. Instead, it navigates the TOP-level browser window (via
# target="_top") to this same Streamlit URL with ?portal=1 attached.
# We read that flag here, on every script run, and flip straight to the
# login form if it's present.
if st.query_params.get("portal") == "1":
    st.session_state.show_portal_form = True
    st.query_params.clear()


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


def is_logged_in():
    return st.session_state.access_token is not None


def safe_json(resp, fallback_message="The server returned an unexpected response."):
    try:
        return resp.json()
    except requests.exceptions.JSONDecodeError:
        st.error(
            f"{fallback_message} (status {resp.status_code}). "
            "This usually means the backend crashed or restarted mid-request - "
            "check the uvicorn terminal for errors, then try again."
        )
        return None


def show_login_page():
    if "show_portal_form" not in st.session_state:
        st.session_state.show_portal_form = False

    if not st.session_state.show_portal_form:
        # --- LANDING STATE: embeds the real AccuCare marketing page
        # (static/index.html, served by FastAPI at BASE_URL) directly,
        # so it's guaranteed identical to what you already approved -
        # no risk of the Streamlit copy drifting from the real one.
        # Everything inside the iframe (nav links, demo form) is purely
        # visual; it isn't wired to this app's session state. The real
        # "enter the app" action is the Streamlit-native button below it.
        # Strip Streamlit's default page padding/margins and hide its
        # top header bar just for this landing screen, so the embedded
        # page can go edge-to-edge instead of sitting in a padded column.
        # This only runs while show_portal_form is False - once the user
        # clicks through to the real app, a fresh script run happens and
        # this CSS is never injected again, so it can't affect any other
        # page (chat, reports, sidebar, etc).
        st.markdown("""
            <style>
            [data-testid="stAppViewContainer"] .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }
            [data-testid="stHeader"] {
                display: none;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <iframe src="{BASE_URL}" scrolling="yes"
                style="width:100vw; height:100vh; border:none; display:block; border-radius:0; position:relative; left:50%; right:50%; margin-left:-50vw; margin-right:-50vw;">
            </iframe>
        """, unsafe_allow_html=True)

        return

    # --- FORM STATE: compact header + login/register tabs ---
    st.markdown("""
        <div class="accucare-hero accucare-hero-compact">
            <h1>AccuCare</h1>
            <div class="accucare-subtitle">accurate + care</div>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Guideline-grounded clinical decision support. Please log in to continue.")

    if st.button("← Back"):
        st.session_state.show_portal_form = False
        st.rerun()

    login_tab, register_tab = st.tabs(["Enter Clinical Portal", "Register"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In")

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                try:
                    resp = requests.post(
                        f"{BASE_URL}/auth/login",
                        data={"username": email, "password": password},
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        token_data = safe_json(resp)
                        if token_data is not None:
                            st.session_state.access_token = token_data["access_token"]
                            st.session_state.doctor_name = email
                            st.rerun()
                    else:
                        data = safe_json(resp, "Login failed.")
                        if data is not None:
                            st.error(data.get("detail", "Login failed."))
                except requests.exceptions.ConnectionError:
                    st.error(
                        "Could not connect to the backend server. "
                        "Make sure uvicorn is running on port 8000."
                    )

    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Full Name", key="reg_name")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_submitted = st.form_submit_button("Create Account")

        if reg_submitted:
            if not full_name or not reg_email or not reg_password:
                st.error("Please fill in all fields.")
            else:
                try:
                    resp = requests.post(
                        f"{BASE_URL}/auth/register",
                        json={
                            "full_name": full_name,
                            "email": reg_email,
                            "password": reg_password,
                        },
                        timeout=15,
                    )
                    if resp.status_code == 201:
                        st.success("Account created. You can now log in from the Login tab.")
                    else:
                        data = safe_json(resp, "Registration failed.")
                        if data is not None:
                            st.error(data.get("detail", "Registration failed."))
                except requests.exceptions.ConnectionError:
                    st.error(
                        "Could not connect to the backend server. "
                        "Make sure uvicorn is running on port 8000."
                    )



def show_chat_page():
    st.header("Clinical Guideline Chat")
    st.caption("Ask a clinical question and get a cited answer from the local guideline database.")

    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])

    question = st.chat_input("Ask a clinical question...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Consulting local guidelines and AI model..."):
                try:
                    resp = requests.post(
                        f"{BASE_URL}/api/v1/clinical/chat",
                        headers=auth_headers(),
                        json={
                            "question": question,
                            "chat_history": st.session_state.chat_history[:-1],
                            "session_id": st.session_state.chat_session_id,
                        },
                        timeout=600,
                    )
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the backend server.")
                    return

                if resp.status_code == 401:
                    st.error("Your session has expired. Please log in again.")
                    st.session_state.access_token = None
                    st.rerun()
                    return

                if resp.status_code != 200:
                    error_data = safe_json(resp, "Chat request failed.")
                    if error_data is not None:
                        st.error(f"Error: {error_data.get('detail', 'Unknown error')}")
                    return

                data = safe_json(resp, "Chat request failed.")
                if data is None:
                    return
                answer = data["answer"]
                sources = data.get("sources", [])
                unverified = data.get("unverified_citation_warning", False)

                if unverified:
                    st.warning(
                        "⚠️ This answer referenced a source that could not be verified "
                        "against the local guideline database. Double-check this "
                        "recommendation manually before relying on it."
                    )

                st.write(answer)
                if sources:
                    st.caption("**Sources:** " + "; ".join(sources))

                st.session_state.chat_history.append({"role": "assistant", "content": answer})

    if st.button("Start New Conversation"):
        st.session_state.chat_history = []
        st.session_state.chat_session_id = None
        st.rerun()


def show_generate_report_page():
    st.header("Generate Patient Report")
    st.caption("Fill in the patient's details to generate a guideline-grounded clinical report.")

    with st.form("report_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            patient_name = st.text_input("Patient Name")
        with col2:
            age = st.number_input("Age", min_value=0, max_value=120, value=30)
        with col3:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])

        current_symptoms = st.text_area("Current Symptoms *")
        medical_history = st.text_area("Medical History (optional)")

        st.markdown("**Vitals**")
        v1, v2, v3, v4 = st.columns(4)
        with v1:
            blood_pressure = st.text_input("Blood Pressure", value="120/80 mmHg")
        with v2:
            pulse_rate = st.number_input("Pulse Rate (bpm)", min_value=0, max_value=300, value=72)
        with v3:
            temperature = st.number_input("Temperature (F)", min_value=80.0, max_value=115.0, value=98.6)
        with v4:
            oxygen_saturation = st.number_input("SpO2 (%)", min_value=0, max_value=100, value=98)

        lab_results = st.text_area("Lab Results (optional)")
        imaging_findings = st.text_area("Imaging Findings (optional)")
        doctor_notes = st.text_area("Doctor's Notes (optional)")

        submitted = st.form_submit_button("Generate Report")

    if submitted:
        if not patient_name or not current_symptoms:
            st.error("Patient Name and Current Symptoms are required.")
            return

        payload = {
            "patient_name": patient_name,
            "age": int(age),
            "gender": gender,
            "medical_history": medical_history or None,
            "current_symptoms": current_symptoms,
            "vitals": {
                "blood_pressure": blood_pressure,
                "pulse_rate": int(pulse_rate),
                "temperature": float(temperature),
                "oxygen_saturation": int(oxygen_saturation),
            },
            "lab_results": lab_results or None,
            "imaging_findings": imaging_findings or None,
            "doctor_notes": doctor_notes or None,
        }

        with st.spinner("Generating report - this can take a few minutes on CPU..."):
            try:
                resp = requests.post(
                    f"{BASE_URL}/api/v1/clinical/generate-report",
                    headers=auth_headers(),
                    json=payload,
                    timeout=900,
                )
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend server.")
                return

        if resp.status_code == 401:
            st.error("Your session has expired. Please log in again.")
            st.session_state.access_token = None
            st.rerun()
            return

        if resp.status_code != 200:
            try:
                detail = resp.json().get("detail", "Report generation failed.")
            except ValueError:
                detail = "Report generation failed."
            st.error(detail)
            return

        report_text = resp.content.decode("utf-8")
        st.success("Report generated and saved.")
        st.text_area("Generated Report", report_text, height=500)
        st.download_button(
            "Download Report (.txt)",
            data=report_text,
            file_name=f"Clinical_Report_{patient_name.replace(' ', '_')}.txt",
            mime="text/plain",
        )


def show_past_reports_page():
    st.header("Past Reports")

    try:
        resp = requests.get(f"{BASE_URL}/api/v1/clinical/reports", headers=auth_headers(), timeout=15)
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend server.")
        return

    if resp.status_code == 401:
        st.error("Your session has expired. Please log in again.")
        st.session_state.access_token = None
        st.rerun()
        return

    reports = safe_json(resp, "Could not load past reports.")
    if reports is None:
        return
    if not reports:
        st.info("No reports have been generated yet.")
        return

    for r in reports:
        with st.expander(f"#{r['id']} - {r['patient_name']} - {r['created_at']}"):
            st.caption(r["report_preview"] + "...")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Full Report", key=f"view_{r['id']}"):
                    detail_resp = requests.get(
                        f"{BASE_URL}/api/v1/clinical/reports/{r['id']}",
                        headers=auth_headers(),
                        timeout=15,
                    )
                    if detail_resp.status_code == 200:
                        detail_data = safe_json(detail_resp, "Could not load report.")
                        if detail_data is not None:
                            st.text_area(
                                "Full Report",
                                detail_data["report_text"],
                                height=400,
                                key=f"full_{r['id']}",
                            )

            with col2:
                pdf_resp = requests.get(
                    f"{BASE_URL}/api/v1/clinical/reports/{r['id']}/pdf",
                    headers=auth_headers(),
                    timeout=30,
                )
                if pdf_resp.status_code == 200:
                    st.download_button(
                        "Download PDF",
                        data=pdf_resp.content,
                        file_name=f"Clinical_Report_{r['patient_name'].replace(' ', '_')}_{r['id']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{r['id']}",
                    )
                else:
                    st.caption("PDF unavailable")


def show_main_app():
    st.sidebar.title("AccuCare")
    st.sidebar.caption(f"Logged in as {st.session_state.doctor_name}")

    page = st.sidebar.radio(
        "Navigate",
        ["Chat", "Generate Report", "Past Reports"],
    )

    if st.sidebar.button("Log Out"):
        st.session_state.access_token = None
        st.session_state.doctor_name = None
        st.session_state.chat_history = []
        st.session_state.chat_session_id = None
        st.rerun()

    if page == "Chat":
        show_chat_page()
    elif page == "Generate Report":
        show_generate_report_page()
    elif page == "Past Reports":
        show_past_reports_page()


if is_logged_in():
    show_main_app()
else:
    show_login_page()