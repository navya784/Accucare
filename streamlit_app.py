```python
import streamlit as st
import requests


# =========================================================
# CONFIGURATION
# =========================================================

BASE_URL = "https://accucare-production.up.railway.app"

st.set_page_config(
    page_title="AccuCare | Clinical Decision Support",
    layout="wide",
    page_icon="🩺",
)


# =========================================================
# THEME
# =========================================================

def inject_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700;800&display=swap');

        html, body {
            font-family: 'Inter', sans-serif;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at 50% -10%,
                    #F7ECE9 0%,
                    #FDF8F6 45%,
                    #FDF8F6 100%
                );
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

        .landing-wrapper {
            text-align: center;
            padding-top: 6rem;
        }

        .landing-title {
            font-family: 'Fraunces', serif;
            font-size: clamp(4rem, 8vw, 7rem);
            font-weight: 500;
            color: #7A3B4C;
            line-height: 1;
            margin-bottom: 0.5rem;
        }

        .landing-subtitle {
            letter-spacing: 0.25em;
            text-transform: uppercase;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            font-weight: 600;
            color: #B9718A;
            margin-bottom: 1.5rem;
        }

        .landing-description {
            max-width: 620px;
            margin: 0 auto;
            color: #6B5A5E;
            font-size: 1.05rem;
            line-height: 1.7;
        }

        .landing-note {
            max-width: 620px;
            margin: 1rem auto 0;
            color: #8C797D;
            font-size: 0.9rem;
        }

        .portal-button-container {
            display: flex;
            justify-content: center;
            margin-top: 2.5rem;
            margin-bottom: 2rem;
        }

        .stButton {
            display: flex;
            justify-content: center;
        }

        .stButton > button {
            border-radius: 999px !important;
            font-weight: 600 !important;
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
            box-shadow:
                0 12px 30px -14px rgba(122, 59, 76, 0.5)
                !important;
        }

        button[kind="primary"]:hover {
            background: #5f2e3b !important;
            transform: translateY(-1px);
        }

        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
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
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {
            border-color: #B9718A !important;
            box-shadow:
                0 0 0 3px rgba(185, 113, 138, 0.15)
                !important;
        }

        [data-testid="stExpander"],
        [data-testid="stChatMessage"],
        [data-testid="stForm"] {
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
            box-shadow:
                0 12px 30px -20px rgba(122, 59, 76, 0.3);
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

        label,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label {
            color: #2B1E22 !important;
            opacity: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_theme()


# =========================================================
# SESSION STATE
# =========================================================

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "doctor_name" not in st.session_state:
    st.session_state.doctor_name = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = None

if "show_portal_form" not in st.session_state:
    st.session_state.show_portal_form = False


# =========================================================
# HELPERS
# =========================================================

def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state.access_token}"
    }


def is_logged_in():
    return st.session_state.access_token is not None


def safe_json(
    resp,
    fallback_message="The server returned an unexpected response.",
):
    try:
        return resp.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        st.error(
            f"{fallback_message} "
            f"(HTTP {resp.status_code})."
        )
        return None


# =========================================================
# LOGIN / LANDING PAGE
# =========================================================

def show_login_page():

    # =====================================================
    # LANDING PAGE
    # =====================================================

    if not st.session_state.show_portal_form:

        st.markdown(
            """
            <div class="landing-wrapper">

                <div class="landing-title">
                    AccuCare
                </div>

                <div class="landing-subtitle">
                    accurate + care
                </div>

                <div class="landing-description">
                    Guideline-grounded clinical decision support
                    designed to help physicians make informed,
                    evidence-based decisions at the point of care.
                </div>

                <div class="landing-note">
                    Access the clinical portal to search trusted
                    clinical guidelines and generate patient reports.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="portal-button-container">',
            unsafe_allow_html=True,
        )

        if st.button(
            "Enter Clinical Portal",
            type="primary",
            key="enter_portal_button",
        ):
            st.session_state.show_portal_form = True
            st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        return

    # =====================================================
    # LOGIN / REGISTER PAGE
    # =====================================================

    st.markdown(
        """
        <div class="accucare-hero accucare-hero-compact">
            <h1>AccuCare</h1>
            <div class="accucare-subtitle">
                accurate + care
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Guideline-grounded clinical decision support. "
        "Please log in to continue."
    )

    if st.button(
        "← Back",
        key="back_to_landing",
    ):
        st.session_state.show_portal_form = False
        st.rerun()

    login_tab, register_tab = st.tabs(
        ["Enter Clinical Portal", "Register"]
    )

    # =====================================================
    # LOGIN
    # =====================================================

    with login_tab:

        with st.form("login_form"):

            email = st.text_input(
                "Email",
                key="login_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            submitted = st.form_submit_button(
                "Log In"
            )

        if submitted:

            if not email or not password:

                st.error(
                    "Please enter both email and password."
                )

            else:

                try:

                    resp = requests.post(
                        f"{BASE_URL}/auth/login",
                        data={
                            "username": email,
                            "password": password,
                        },
                        timeout=20,
                    )

                    if resp.status_code == 200:

                        token_data = safe_json(
                            resp,
                            "Login failed.",
                        )

                        if token_data is not None:

                            access_token = token_data.get(
                                "access_token"
                            )

                            if not access_token:

                                st.error(
                                    "Login succeeded but "
                                    "the server did not return "
                                    "an access token."
                                )
                                return

                            st.session_state.access_token = (
                                access_token
                            )

                            st.session_state.doctor_name = email

                            st.session_state.show_portal_form = True

                            st.rerun()

                    else:

                        data = safe_json(
                            resp,
                            "Login failed.",
                        )

                        if data is not None:

                            st.error(
                                data.get(
                                    "detail",
                                    "Login failed.",
                                )
                            )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "Could not connect to the AccuCare "
                        "backend server."
                    )

                except requests.exceptions.Timeout:

                    st.error(
                        "The backend took too long to respond. "
                        "Please try again."
                    )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"Backend connection error: {exc}"
                    )

    # =====================================================
    # REGISTER
    # =====================================================

    with register_tab:

        with st.form("register_form"):

            full_name = st.text_input(
                "Full Name",
                key="reg_name",
            )

            reg_email = st.text_input(
                "Email",
                key="reg_email",
            )

            reg_password = st.text_input(
                "Password",
                type="password",
                key="reg_password",
            )

            reg_submitted = st.form_submit_button(
                "Create Account"
            )

        if reg_submitted:

            if (
                not full_name
                or not reg_email
                or not reg_password
            ):

                st.error(
                    "Please fill in all fields."
                )

            else:

                try:

                    resp = requests.post(
                        f"{BASE_URL}/auth/register",
                        json={
                            "full_name": full_name,
                            "email": reg_email,
                            "password": reg_password,
                        },
                        timeout=20,
                    )

                    if resp.status_code == 201:

                        st.success(
                            "Account created successfully. "
                            "You can now log in from "
                            "the Clinical Portal tab."
                        )

                    else:

                        data = safe_json(
                            resp,
                            "Registration failed.",
                        )

                        if data is not None:

                            st.error(
                                data.get(
                                    "detail",
                                    "Registration failed.",
                                )
                            )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "Could not connect to the AccuCare "
                        "backend server."
                    )

                except requests.exceptions.Timeout:

                    st.error(
                        "The backend took too long to respond. "
                        "Please try again."
                    )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"Backend connection error: {exc}"
                    )


# =========================================================
# CLINICAL CHAT
# =========================================================

def show_chat_page():

    st.header("Clinical Guideline Chat")

    st.caption(
        "Ask a clinical question and receive an answer "
        "grounded in the indexed guideline database."
    )

    for turn in st.session_state.chat_history:

        with st.chat_message(turn["role"]):
            st.write(turn["content"])

    question = st.chat_input(
        "Ask a clinical question..."
    )

    if question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "Consulting local guidelines and AI model..."
            ):

                try:

                    resp = requests.post(
                        f"{BASE_URL}/api/v1/clinical/chat",
                        headers=auth_headers(),
                        json={
                            "question": question,
                            "chat_history": (
                                st.session_state.chat_history[:-1]
                            ),
                            "session_id": (
                                st.session_state.chat_session_id
                            ),
                        },
                        timeout=600,
                    )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "Could not connect to the backend server."
                    )
                    return

                except requests.exceptions.Timeout:

                    st.error(
                        "The clinical chat request timed out."
                    )
                    return

                if resp.status_code == 401:

                    st.error(
                        "Your session has expired. "
                        "Please log in again."
                    )

                    st.session_state.access_token = None
                    st.session_state.doctor_name = None
                    st.rerun()
                    return

                if resp.status_code != 200:

                    error_data = safe_json(
                        resp,
                        "Chat request failed.",
                    )

                    if error_data is not None:

                        st.error(
                            f"Error: "
                            f"{error_data.get('detail', 'Unknown error')}"
                        )

                    return

                data = safe_json(
                    resp,
                    "Chat request failed.",
                )

                if data is None:
                    return

                answer = data.get(
                    "answer",
                    "",
                )

                sources = data.get(
                    "sources",
                    [],
                )

                unverified = data.get(
                    "unverified_citation_warning",
                    False,
                )

                if unverified:

                    st.warning(
                        "⚠️ This answer contains a citation "
                        "that could not be verified against "
                        "the retrieved local guideline sources."
                    )

                if answer:

                    st.write(answer)

                if sources:

                    st.caption(
                        "**Sources:** "
                        + "; ".join(sources)
                    )

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

    if st.button(
        "Start New Conversation",
        key="new_conversation",
    ):

        st.session_state.chat_history = []
        st.session_state.chat_session_id = None
        st.rerun()


# =========================================================
# GENERATE PATIENT REPORT
# =========================================================

def show_generate_report_page():

    st.header("Generate Patient Report")

    st.caption(
        "Fill in the patient's details to generate "
        "a guideline-grounded clinical report."
    )

    with st.form("report_form"):

        col1, col2, col3 = st.columns(3)

        with col1:

            patient_name = st.text_input(
                "Patient Name"
            )

        with col2:

            age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                value=30,
            )

        with col3:

            gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Other"],
            )

        current_symptoms = st.text_area(
            "Current Symptoms *"
        )

        medical_history = st.text_area(
            "Medical History (optional)"
        )

        st.markdown("**Vitals**")

        v1, v2, v3, v4 = st.columns(4)

        with v1:

            blood_pressure = st.text_input(
                "Blood Pressure",
                value="120/80 mmHg",
            )

        with v2:

            pulse_rate = st.number_input(
                "Pulse Rate (bpm)",
                min_value=0,
                max_value=300,
                value=72,
            )

        with v3:

            temperature = st.number_input(
                "Temperature (F)",
                min_value=80.0,
                max_value=115.0,
                value=98.6,
            )

        with v4:

            oxygen_saturation = st.number_input(
                "SpO2 (%)",
                min_value=0,
                max_value=100,
                value=98,
            )

        lab_results = st.text_area(
            "Lab Results (optional)"
        )

        imaging_findings = st.text_area(
            "Imaging Findings (optional)"
        )

        doctor_notes = st.text_area(
            "Doctor's Notes (optional)"
        )

        submitted = st.form_submit_button(
            "Generate Report"
        )

    if not submitted:
        return

    if not patient_name or not current_symptoms:

        st.error(
            "Patient Name and Current Symptoms are required."
        )

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
            "oxygen_saturation": int(
                oxygen_saturation
            ),
        },
        "lab_results": lab_results or None,
        "imaging_findings": imaging_findings or None,
        "doctor_notes": doctor_notes or None,
    }

    with st.spinner(
        "Generating report - this may take a few minutes..."
    ):

        try:

            resp = requests.post(
                f"{BASE_URL}/api/v1/clinical/generate-report",
                headers=auth_headers(),
                json=payload,
                timeout=900,
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to the backend server."
            )
            return

        except requests.exceptions.Timeout:

            st.error(
                "Report generation timed out."
            )
            return

    if resp.status_code == 401:

        st.error(
            "Your session has expired. "
            "Please log in again."
        )

        st.session_state.access_token = None
        st.session_state.doctor_name = None
        st.rerun()

        return

    if resp.status_code != 200:

        try:

            detail = resp.json().get(
                "detail",
                "Report generation failed.",
            )

        except ValueError:

            detail = (
                "Report generation failed."
            )

        st.error(detail)
        return

    report_text = resp.content.decode(
        "utf-8",
        errors="replace",
    )

    st.success(
        "Report generated and saved."
    )

    st.text_area(
        "Generated Report",
        report_text,
        height=600,
    )

    st.download_button(
        "Download Report (.txt)",
        data=report_text,
        file_name=(
            f"Clinical_Report_"
            f"{patient_name.replace(' ', '_')}.txt"
        ),
        mime="text/plain",
    )


# =========================================================
# PAST REPORTS
# =========================================================

def show_past_reports_page():

    st.header("Past Reports")

    try:

        resp = requests.get(
            f"{BASE_URL}/api/v1/clinical/reports",
            headers=auth_headers(),
            timeout=20,
        )

    except requests.exceptions.ConnectionError:

        st.error(
            "Could not connect to the backend server."
        )
        return

    except requests.exceptions.Timeout:

        st.error(
            "The backend took too long to respond."
        )
        return

    if resp.status_code == 401:

        st.error(
            "Your session has expired. "
            "Please log in again."
        )

        st.session_state.access_token = None
        st.session_state.doctor_name = None
        st.rerun()

        return

    reports = safe_json(
        resp,
        "Could not load past reports.",
    )

    if reports is None:
        return

    if not reports:

        st.info(
            "No reports have been generated yet."
        )

        return

    for report in reports:

        report_id = report["id"]
        patient_name = report["patient_name"]
        created_at = report["created_at"]

        with st.expander(
            f"#{report_id} - "
            f"{patient_name} - "
            f"{created_at}"
        ):

            preview = report.get(
                "report_preview",
                "",
            )

            if preview:

                st.caption(
                    preview + "..."
                )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "View Full Report",
                    key=f"view_{report_id}",
                ):

                    try:

                        detail_resp = requests.get(
                            f"{BASE_URL}/api/v1/clinical/reports/"
                            f"{report_id}",
                            headers=auth_headers(),
                            timeout=20,
                        )

                        if detail_resp.status_code == 200:

                            detail_data = safe_json(
                                detail_resp,
                                "Could not load report.",
                            )

                            if detail_data is not None:

                                st.text_area(
                                    "Full Report",
                                    detail_data["report_text"],
                                    height=500,
                                    key=f"full_{report_id}",
                                )

                        elif detail_resp.status_code == 401:

                            st.error(
                                "Your session has expired."
                            )

                        else:

                            st.error(
                                "Could not load this report."
                            )

                    except requests.exceptions.RequestException as exc:

                        st.error(
                            f"Could not load report: {exc}"
                        )

            with col2:

                try:

                    pdf_resp = requests.get(
                        f"{BASE_URL}/api/v1/clinical/reports/"
                        f"{report_id}/pdf",
                        headers=auth_headers(),
                        timeout=30,
                    )

                    if pdf_resp.status_code == 200:

                        st.download_button(
                            "Download PDF",
                            data=pdf_resp.content,
                            file_name=(
                                f"Clinical_Report_"
                                f"{patient_name.replace(' ', '_')}_"
                                f"{report_id}.pdf"
                            ),
                            mime="application/pdf",
                            key=f"pdf_{report_id}",
                        )

                    else:

                        st.caption(
                            "PDF unavailable"
                        )

                except requests.exceptions.RequestException:

                    st.caption(
                        "PDF unavailable"
                    )


# =========================================================
# MAIN APPLICATION
# =========================================================

def show_main_app():

    st.sidebar.title("AccuCare")

    st.sidebar.caption(
        f"Logged in as "
        f"{st.session_state.doctor_name}"
    )

    page = st.sidebar.radio(
        "Navigate",
        [
            "Chat",
            "Generate Report",
            "Past Reports",
        ],
    )

    if st.sidebar.button(
        "Log Out",
        key="logout_button",
    ):

        st.session_state.access_token = None
        st.session_state.doctor_name = None
        st.session_state.chat_history = []
        st.session_state.chat_session_id = None
        st.session_state.show_portal_form = False

        st.rerun()

    if page == "Chat":

        show_chat_page()

    elif page == "Generate Report":

        show_generate_report_page()

    elif page == "Past Reports":

        show_past_reports_page()


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

if is_logged_in():

    show_main_app()

else:

    show_login_page()
```
