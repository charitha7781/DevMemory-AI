
import streamlit as st
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="DevMemory AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SESSION STATE
# =========================================================

if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

if "memory_results" not in st.session_state:
    st.session_state.memory_results = []

if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = False


# =========================================================
# EMERALD & CHARCOAL DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700;800&display=swap'
);

/* COLOUR VARIABLES */

:root {
    --bg: #10251F;
    --sidebar: #0C1D18;
    --surface: #174C3C;
    --surface-hover: #205C48;
    --border: #315D4D;
    --primary: #20B486;
    --mint: #D4F2E5;
    --ivory: #F0EDE4;
    --text: #F5F5EE;
    --muted: #A7C7B5;
    --amber: #E6B878;
}

/* MAIN BACKGROUND */

.stApp {
    background-color: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
}

.block-container {
    max-width: 1450px;
    padding: 2rem 3rem 3rem;
}

/* TYPOGRAPHY */

h1, h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--ivory) !important;
    letter-spacing: -0.5px;
}

h1 {
    font-size: 34px !important;
    font-weight: 800 !important;
}

h2 {
    font-size: 25px !important;
    font-weight: 700 !important;
}

h3 {
    font-size: 19px !important;
    font-weight: 600 !important;
}

p, label, .stMarkdown, li {
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

[data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
    font-size: 13px;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background-color: var(--sidebar);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--ivory);
}

[data-testid="stSidebar"] .stRadio label {
    font-size: 15px;
    font-weight: 500;
}

/* INPUTS */

.stTextArea textarea,
.stTextInput input {
    background-color: #0D2920 !important;
    color: var(--ivory) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
    border: 1px solid var(--primary) !important;
    box-shadow: 0 0 0 1px var(--primary) !important;
}

[data-baseweb="select"] > div {
    background-color: #0D2920 !important;
    border-color: var(--border) !important;
    color: var(--ivory) !important;
}

/* BUTTONS */

.stButton > button,
.stFormSubmitButton > button {
    background: var(--primary);
    color: #09251B !important;
    border: none;
    border-radius: 9px;
    padding: 0.55rem 1.2rem;
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    transition: 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #48D3A5;
    color: #09251B !important;
    border: none;
    transform: translateY(-1px);
}

/* CARDS */

.dm-card {
    background: linear-gradient(145deg, #174C3C, #143B30);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 22px;
    min-height: 145px;
    margin-bottom: 14px;
}

.dm-card h3 {
    font-size: 18px !important;
    margin-bottom: 8px;
}

.dm-card p {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.6;
}

.dm-icon {
    font-size: 25px;
    margin-bottom: 12px;
}

.dm-metric {
    background: #174C3C;
    border: 1px solid var(--border);
    padding: 18px;
    border-radius: 13px;
}

.dm-metric-label {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 8px;
}

.dm-metric-value {
    font-family: 'DM Sans', sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: var(--ivory);
}

/* HERO */

.dm-hero {
    background: linear-gradient(120deg, #174C3C, #10251F);
    border: 1px solid #315D4D;
    border-radius: 18px;
    padding: 30px;
    margin-bottom: 25px;
}

.dm-hero h1 {
    margin-bottom: 8px;
}

.dm-hero p {
    color: var(--muted);
    font-size: 15px;
}

/* STATUS */

.dm-status {
    display: inline-block;
    background: #284C3B;
    color: #A7E8C9;
    border: 1px solid #3D7458;
    padding: 5px 11px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
}

/* DIVIDERS */

hr {
    border-color: var(--border) !important;
}

/* EXPANDERS */

[data-testid="stExpander"] {
    background: #143B30;
    border: 1px solid var(--border);
    border-radius: 10px;
}

/* ALERTS */

[data-testid="stAlert"] {
    border-radius: 10px;
}

/* HIDE STREAMLIT BRANDING */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def add_activity(module, description):
    """Store user activity in the current session."""

    activity = {
        "module": module,
        "description": description,
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

    st.session_state.analysis_history.insert(0, activity)


def show_page_header(title, description):
    st.title(title)
    st.caption(description)
    st.markdown("---")


def show_backend_message():
    st.info(
        "AI backend integration is being connected. "
        "This module's analysis will become available once "
        "the Hindsight and LLM services are integrated."
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="padding: 10px 0 20px 0;">
            <div style="font-size: 34px;">🧠</div>
            <div style="
                font-family: 'DM Sans';
                font-size: 25px;
                font-weight: 800;
                color: #F0EDE4;">
                DevMemory<span style="color:#20B486;"> AI</span>
            </div>
            <div style="
                color: #A7C7B5;
                font-size: 11px;
                letter-spacing: 1px;">
                INTELLIGENT ENGINEERING ASSISTANT
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("##### WORKSPACE")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Incident Intelligence",
            "Code Review",
            "Deployment Intelligence",
            "Memory Explorer"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("##### SYSTEM STATUS")

    st.markdown(
        '<span class="dm-status">● MVP DEVELOPMENT</span>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.backend_connected:
        st.success("AI Backend Connected")
    else:
        st.warning("AI Backend Pending")

    st.caption("Powered by Hindsight Memory")


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.markdown("""
    <div class="dm-hero">
        <div class="dm-status">INTELLIGENT ENGINEERING WORKSPACE</div>
        <h1>Engineering, with memory.</h1>
        <p>
            Learn from every incident. Improve every code review.
            Make every deployment smarter.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Your Engineering Overview")

    col1, col2, col3 = st.columns(3)

    total_activities = len(st.session_state.analysis_history)

    with col1:
        st.markdown(f"""
        <div class="dm-metric">
            <div class="dm-metric-label">TOTAL ACTIVITIES</div>
            <div class="dm-metric-value">{total_activities}</div>
            <div class="dm-metric-label">This session</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dm-metric">
            <div class="dm-metric-label">INTELLIGENCE MODULES</div>
            <div class="dm-metric-value">03</div>
            <div class="dm-metric-label">Incident · Code · Deployment</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        memory_status = (
            "Connected" if st.session_state.backend_connected
            else "Pending"
        )

        st.markdown(f"""
        <div class="dm-metric">
            <div class="dm-metric-label">HINDSIGHT MEMORY</div>
            <div class="dm-metric-value" style="font-size:23px;">
                {memory_status}
            </div>
            <div class="dm-metric-label">Shared engineering memory</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("Explore Intelligence Modules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">🚨</div>
            <h3>Incident Intelligence</h3>
            <p>
                Analyse error logs, identify possible root causes
                and retrieve relevant solutions from past incidents.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">🚀</div>
            <h3>Deployment Intelligence</h3>
            <p>
                Investigate CI/CD failures, identify failed stages
                and recall previous deployment solutions.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">💻</div>
            <h3>Intelligent Code Review</h3>
            <p>
                Examine code for potential bugs, security risks
                and coding convention violations.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">🧠</div>
            <h3>Memory Explorer</h3>
            <p>
                Explore stored engineering experiences and
                retrieve relevant memories across all modules.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Recent Activity")

    if st.session_state.analysis_history:

        for item in st.session_state.analysis_history[:5]:

            with st.container(border=True):
                st.markdown(f"**{item['module']}**")
                st.write(item["description"])
                st.caption(item["time"])

    else:
        st.caption("No activity yet. Start by analysing an incident, reviewing code or checking a deployment.")

    st.markdown("---")

    st.caption(
        "DevMemory AI | An engineering assistant that learns from experience."
    )


# =========================================================
# INCIDENT INTELLIGENCE
# =========================================================

elif page == "Incident Intelligence":

    show_page_header(
        "🚨 Incident Intelligence",
        "Understand production errors and learn from previous incidents."
    )

    st.markdown("""
    <div class="dm-card">
        <h3>Investigate an Incident</h3>
        <p>
            Submit an error log or stack trace. The AI engine will
            identify possible causes and retrieve relevant past experiences.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("incident_form"):

        incident_title = st.text_input(
            "Incident Title",
            placeholder="Example: Database connection timeout"
        )

        severity = st.selectbox(
            "Severity",
            ["Critical", "High", "Medium", "Low"]
        )

        incident_logs = st.text_area(
            "Paste Incident Logs / Stack Trace",
            placeholder="Paste your error logs here...",
            height=220
        )

        submitted = st.form_submit_button(
            "Analyse Incident",
            use_container_width=True
        )

        if submitted:

            if not incident_logs.strip():
                st.error("Please enter incident logs before submitting.")

            else:
                add_activity(
                    "Incident Intelligence",
                    incident_title if incident_title.strip()
                    else "Incident log submitted"
                )

                st.success("Incident submitted successfully.")
                show_backend_message()

    st.markdown("---")

    st.subheader("What this module will provide")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        - Possible root cause
        - Error classification
        - Related historical incidents
        """)

    with col2:
        st.markdown("""
        - Previously confirmed fixes
        - Recommended troubleshooting steps
        - Feedback-based memory retention
        """)


# =========================================================
# CODE REVIEW
# =========================================================

elif page == "Code Review":

    show_page_header(
        "💻 Intelligent Code Review",
        "Identify potential code issues and recall engineering conventions."
    )

    st.markdown("""
    <div class="dm-card">
        <h3>Review Your Code</h3>
        <p>
            Submit a code snippet to inspect possible bugs,
            security concerns and maintainability issues.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("code_review_form"):

        language = st.selectbox(
            "Programming Language",
            [
                "Python",
                "Java",
                "JavaScript",
                "C",
                "C++",
                "Other"
            ]
        )

        code_input = st.text_area(
            "Paste Your Code",
            placeholder="Paste your source code here...",
            height=280
        )

        review_type = st.multiselect(
            "Review Focus",
            [
                "Bug Detection",
                "Security",
                "Code Quality",
                "Performance",
                "Best Practices"
            ],
            default=["Bug Detection", "Code Quality"]
        )

        submitted = st.form_submit_button(
            "Review Code",
            use_container_width=True
        )

        if submitted:

            if not code_input.strip():
                st.error("Please paste some code before submitting.")

            else:
                add_activity(
                    "Code Review",
                    f"{language} code submitted for review"
                )

                st.success("Code submitted successfully.")
                show_backend_message()

    st.markdown("---")

    st.subheader("Review Capabilities")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">🐛</div>
            <h3>Bug Detection</h3>
            <p>Identify potential logical and runtime errors.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">🔐</div>
            <h3>Security</h3>
            <p>Highlight possible security vulnerabilities.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">✨</div>
            <h3>Code Quality</h3>
            <p>Suggest improvements to readability and maintainability.</p>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# DEPLOYMENT INTELLIGENCE
# =========================================================

elif page == "Deployment Intelligence":

    show_page_header(
        "🚀 Deployment Intelligence",
        "Investigate pipeline failures and learn from deployment history."
    )

    st.markdown("""
    <div class="dm-card">
        <h3>Investigate a Deployment</h3>
        <p>
            Submit CI/CD or deployment logs to identify potential
            failures, configuration issues and previous solutions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("deployment_form"):

        platform = st.selectbox(
            "Deployment Environment",
            [
                "GitHub Actions",
                "Jenkins",
                "Docker",
                "Kubernetes",
                "Other"
            ]
        )

        stage = st.selectbox(
            "Pipeline Stage",
            [
                "Build",
                "Test",
                "Package",
                "Deploy",
                "Runtime",
                "Unknown"
            ]
        )

        deployment_logs = st.text_area(
            "Paste Deployment Logs",
            placeholder="Paste your CI/CD or deployment error logs here...",
            height=220
        )

        submitted = st.form_submit_button(
            "Analyse Deployment",
            use_container_width=True
        )

        if submitted:

            if not deployment_logs.strip():
                st.error("Please enter deployment logs before submitting.")

            else:
                add_activity(
                    "Deployment Intelligence",
                    f"{platform} - {stage} stage submitted"
                )

                st.success("Deployment logs submitted successfully.")
                show_backend_message()

    st.markdown("---")

    st.subheader("Deployment Analysis Capabilities")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        - Failed pipeline stage identification
        - Build and dependency error analysis
        - Configuration issue detection
        """)

    with col2:
        st.markdown("""
        - Similar historical deployment failures
        - Previously confirmed fixes
        - Troubleshooting recommendations
        """)


# =========================================================
# MEMORY EXPLORER
# =========================================================

elif page == "Memory Explorer":

    show_page_header(
        "🧠 Memory Explorer",
        "Explore engineering knowledge retained and retrieved by DevMemory AI."
    )

    st.markdown("""
    <div class="dm-card">
        <h3>One Shared Engineering Memory</h3>
        <p>
            DevMemory AI connects incidents, code reviews and deployment
            experiences through a shared Hindsight memory system.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Search Engineering Memories")

    with st.form("memory_search_form"):

        search_query = st.text_input(
            "What would you like to remember?",
            placeholder="Example: Previous database connection failures"
        )

        memory_type = st.selectbox(
            "Memory Category",
            [
                "All Memories",
                "Incidents",
                "Code Reviews",
                "Deployments",
                "Confirmed Fixes"
            ]
        )

        submitted = st.form_submit_button(
            "Search Memory",
            use_container_width=True
        )

        if submitted:

            if not search_query.strip():
                st.error("Enter a search query.")

            else:
                st.info(
                    "Memory search will be connected to Hindsight "
                    "when the backend integration is ready."
                )

    st.markdown("---")

    st.subheader("Memory Architecture")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">📥</div>
            <h3>Retain</h3>
            <p>Store useful engineering experiences and outcomes.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">🔍</div>
            <h3>Recall</h3>
            <p>Retrieve relevant knowledge from previous experiences.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">💡</div>
            <h3>Reflect</h3>
            <p>Identify patterns and learn from accumulated experience.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Stored Memories")

    if st.session_state.memory_results:

        for memory in st.session_state.memory_results:
            st.write(memory)

    else:
        st.caption(
            "No Hindsight memories are being displayed yet. "
            "Real retained memories will appear here after integration."
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#A7C7B5;
        font-size:12px;
        padding:10px;">
        <b style="color:#20B486;">DevMemory AI</b>
        &nbsp; | &nbsp;
        Engineering Intelligence Powered by Memory
    </div>
    """,
    unsafe_allow_html=True
)
