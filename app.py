
import streamlit as st
from datetime import datetime
from pathlib import Path

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

DEFAULTS = {
    "analysis_history": [],
    "memory_results": [],
    "backend_connected": False,
    "incident_result": None,
    "code_result": None,
    "deployment_result": None,
    "memory_query": "",
    "incident_logs": "",
    "code_input": "",
    "deployment_logs": ""
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# DEMO DATA
# =========================================================

SAMPLE_INCIDENT = """2026-11-09 10:15:21 ERROR [OrderService] Failed to process order
2026-11-09 10:15:21 ERROR [DatabaseConnection] Connection timeout
2026-11-09 10:15:22 WARN  [DatabaseConnection] Retrying connection (1/3)
2026-11-09 10:15:27 WARN  [DatabaseConnection] Retrying connection (2/3)
2026-11-09 10:15:32 ERROR [DatabaseConnection] Connection pool exhausted
2026-11-09 10:15:32 ERROR [OrderService] SQLTransientConnectionException:
Connection is not available, request timed out after 30000ms.
2026-11-09 10:15:33 ERROR [OrderService] Order processing failed.
2026-11-09 10:15:33 INFO  [Application] Service is still running.
"""

SAMPLE_DEPLOYMENT = """2026-11-09 11:20:01 INFO [GitHub Actions] Workflow started
2026-11-09 11:20:03 INFO [Build] Installing dependencies
2026-11-09 11:20:08 INFO [Build] Dependencies installed successfully
2026-11-09 11:20:12 INFO [Test] Running application tests
2026-11-09 11:20:15 INFO [Test] Tests completed
2026-11-09 11:20:18 INFO [Docker] Building Docker image
2026-11-09 11:20:24 ERROR [Docker] Failed to build image
2026-11-09 11:20:24 ERROR [Docker] COPY failed: requirements.txt not found
2026-11-09 11:20:25 ERROR [Deploy] Deployment aborted
2026-11-09 11:20:25 INFO [GitHub Actions] Workflow failed
"""

SAMPLE_CODE = '''def execute_query(query):
    print("Executing query:", query)


def get_user(user_id):
    password = "admin123"

    query = "SELECT * FROM users WHERE id = " + user_id

    if user_id != None:
        return execute_query(query)

    return "User not found"


def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)
'''


# =========================================================
# DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700;800&display=swap');

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

.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
}

.block-container {
    max-width: 1450px;
    padding: 2rem 3rem 3rem;
}

h1, h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--ivory) !important;
}

h1 { font-size: 34px !important; font-weight: 800 !important; }
h2 { font-size: 25px !important; font-weight: 700 !important; }
h3 { font-size: 19px !important; font-weight: 600 !important; }

p, label, .stMarkdown, li {
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

[data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
    font-size: 13px;
}

[data-testid="stSidebar"] {
    background: var(--sidebar);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--ivory);
}

[data-testid="stSidebar"] .stRadio label {
    font-size: 15px;
    font-weight: 500;
}

.stTextArea textarea,
.stTextInput input {
    background: #0D2920 !important;
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
    background: #0D2920 !important;
    border-color: var(--border) !important;
    color: var(--ivory) !important;
}

.stButton > button,
.stFormSubmitButton > button {
    background: var(--primary);
    color: #09251B !important;
    border: none;
    border-radius: 9px;
    padding: 0.55rem 1.2rem;
    font-weight: 700;
    transition: 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #48D3A5;
    color: #09251B !important;
    transform: translateY(-1px);
}

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

.dm-hero {
    background: linear-gradient(120deg, #174C3C, #10251F);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 30px;
    margin-bottom: 25px;
}

.dm-hero h1 { margin-bottom: 8px; }
.dm-hero p { color: var(--muted); font-size: 15px; }

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

.dm-tag {
    display: inline-block;
    background: #0D2920;
    color: #A7E8C9;
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 5px 9px;
    font-size: 11px;
    margin: 3px;
}

hr { border-color: var(--border) !important; }

[data-testid="stExpander"] {
    background: #143B30;
    border: 1px solid var(--border);
    border-radius: 10px;
}

[data-testid="stAlert"] { border-radius: 10px; }

#MainMenu, footer { visibility: hidden; }

header[data-testid="stHeader"] {
    background: transparent;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def add_activity(module, description):
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
    st.warning(
        "The AI backend is not connected yet. "
        "Your input has been received by the frontend, but no AI analysis "
        "or Hindsight memory retrieval has been performed."
    )


def show_demo_button(label, key, sample, target):
    if st.button(label, key=key, use_container_width=True):
        st.session_state[target] = sample
        st.rerun()


def show_analysis_result(result, module):
    """Display results returned by the real backend."""

    if not result:
        return

    st.markdown("---")
    st.subheader(f"🧠 {module} Results")

    if result.get("summary"):
        st.write(result["summary"])

    if result.get("root_cause"):
        st.markdown("### Root Cause")
        st.write(result["root_cause"])

    if result.get("severity"):
        st.markdown("### Detected Severity")
        st.write(result["severity"])

    if result.get("failed_stage"):
        st.markdown("### Failed Pipeline Stage")
        st.write(result["failed_stage"])

    if result.get("findings"):
        st.markdown("### Findings")
        for finding in result["findings"]:
            with st.expander(
                str(finding.get("title", "Finding"))
            ):
                st.write(finding.get("description", ""))
                if finding.get("severity"):
                    st.caption(
                        f"Severity: {finding['severity']}"
                    )
                if finding.get("recommendation"):
                    st.info(finding["recommendation"])

    if result.get("recommended_fix"):
        st.markdown("### Recommended Fix")
        st.info(result["recommended_fix"])

    if result.get("memories"):
        st.markdown("### Similar Past Engineering Experiences")
        for memory in result["memories"]:
            with st.expander("Retrieved Memory"):
                st.write(memory)

    if result.get("confidence") is not None:
        st.caption(
            f"Analysis confidence: {result['confidence']}"
        )


def backend_not_ready(module):
    st.info(
        f"{module} is ready for backend integration. "
        "Connect the LLM and Hindsight engine to enable real analysis."
    )


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:

    st.markdown("""
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
    """, unsafe_allow_html=True)

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

    if st.session_state.backend_connected:
        st.success("AI Backend Connected")
    else:
        st.warning("AI Backend Pending")

    st.caption("Powered by Hindsight Memory")
    st.caption("Shared engineering memory across all modules")


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

    total_activities = len(st.session_state.analysis_history)
    total_memories = len(st.session_state.memory_results)

    col1, col2, col3 = st.columns(3)

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
        status = (
            "Connected" if st.session_state.backend_connected
            else "Pending"
        )
        st.markdown(f"""
        <div class="dm-metric">
            <div class="dm-metric-label">HINDSIGHT MEMORY</div>
            <div class="dm-metric-value" style="font-size:23px;">
                {status}
            </div>
            <div class="dm-metric-label">
                {total_memories} displayed memories
            </div>
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
                Submit raw error logs. Identify root causes,
                automatically classify severity and recall
                similar historical incidents.
            </p>
        </div>
        <div class="dm-card">
            <div class="dm-icon">🚀</div>
            <h3>Deployment Intelligence</h3>
            <p>
                Investigate CI/CD logs, detect failed stages
                and retrieve previous deployment solutions.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">💻</div>
            <h3>Intelligent Code Review</h3>
            <p>
                Inspect source code for bugs, security risks,
                performance issues and project conventions.
            </p>
        </div>
        <div class="dm-card">
            <div class="dm-icon">🧠</div>
            <h3>Memory Explorer</h3>
            <p>
                Search engineering experiences and explore
                knowledge shared across all three modules.
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
        st.caption(
            "No activity yet. Start with an incident, code review "
            "or deployment investigation."
        )

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
        "Submit raw error logs. Let AI investigate what went wrong."
    )

    st.markdown("""
    <div class="dm-card">
        <h3>Investigate an Incident</h3>
        <p>
            You provide the evidence. DevMemory AI identifies the
            possible issue, root cause and severity, then searches
            for relevant engineering experiences from its memory.
        </p>
        <span class="dm-tag">Automatic root-cause analysis</span>
        <span class="dm-tag">Automatic severity detection</span>
        <span class="dm-tag">Historical memory retrieval</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Incident Evidence")

    st.caption(
        "Paste your application logs or stack trace below. "
        "You do not need to identify the issue yourself."
    )

    show_demo_button(
        "Load Sample Incident Logs",
        "load_incident_demo",
        SAMPLE_INCIDENT,
        "incident_logs"
    )

    with st.form("incident_form"):

        incident_logs = st.text_area(
            "Incident Logs / Stack Trace",
            key="incident_logs",
            placeholder="Paste your error logs or stack trace here...",
            height=250
        )

        submitted = st.form_submit_button(
            "🔍 Investigate My Incident",
            use_container_width=True
        )

        if submitted:

            if not incident_logs.strip():
                st.error("Please paste incident logs before submitting.")

            else:
                add_activity(
                    "Incident Intelligence",
                    "Incident logs submitted for investigation"
                )

                st.success("Incident evidence submitted.")
                backend_not_ready("Incident Intelligence")

    show_analysis_result(
        st.session_state.incident_result,
        "Incident Analysis"
    )

    st.markdown("---")
    st.subheader("What DevMemory AI will identify")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        - Root cause and probable contributing factors
        - Automatically detected severity
        - Error classification
        - Related historical incidents
        """)

    with col2:
        st.markdown("""
        - Previously confirmed fixes
        - Recommended troubleshooting steps
        - Similarity-based memory retrieval
        - Feedback-based memory retention
        """)


# =========================================================
# INTELLIGENT CODE REVIEW
# =========================================================

elif page == "Code Review":

    show_page_header(
        "💻 Intelligent Code Review",
        "Find potential problems in code and learn from past reviews."
    )

    st.markdown("""
    <div class="dm-card">
        <h3>Review Your Code</h3>
        <p>
            Submit your source code. The AI engine examines it for
            potential bugs, vulnerabilities, performance issues and
            maintainability concerns, while recalling relevant
            project conventions from memory.
        </p>
    </div>
    """, unsafe_allow_html=True)

    show_demo_button(
        "Load Sample Python Code",
        "load_code_demo",
        SAMPLE_CODE,
        "code_input"
    )

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
            "Source Code",
            key="code_input",
            placeholder="Paste your source code here...",
            height=300
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
            "🔍 Review My Code",
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
                backend_not_ready("Code Review")

    show_analysis_result(
        st.session_state.code_result,
        "Code Review Results"
    )

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
            <p>Highlight possible vulnerabilities and unsafe patterns.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">⚡</div>
            <h3>Performance</h3>
            <p>Suggest improvements to efficiency and maintainability.</p>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# DEPLOYMENT INTELLIGENCE
# =========================================================

elif page == "Deployment Intelligence":

    show_page_header(
        "🚀 Deployment Intelligence",
        "Submit deployment logs. Let AI discover where the pipeline failed."
    )

    st.markdown("""
    <div class="dm-card">
        <h3>Investigate a Deployment</h3>
        <p>
            Paste CI/CD or deployment logs. DevMemory AI will identify
            the failed stage, investigate configuration or dependency
            problems and search for similar past deployment failures.
        </p>
        <span class="dm-tag">Automatic failed-stage detection</span>
        <span class="dm-tag">Configuration analysis</span>
        <span class="dm-tag">Historical deployment memory</span>
    </div>
    """, unsafe_allow_html=True)

    platform = st.selectbox(
        "Deployment Environment (optional)",
        [
            "Not specified",
            "GitHub Actions",
            "Jenkins",
            "Docker",
            "Kubernetes",
            "Other"
        ],
        key="deployment_platform"
    )

    show_demo_button(
        "Load Sample Deployment Logs",
        "load_deployment_demo",
        SAMPLE_DEPLOYMENT,
        "deployment_logs"
    )

    with st.form("deployment_form"):

        deployment_logs = st.text_area(
            "CI/CD or Deployment Logs",
            key="deployment_logs",
            placeholder="Paste your deployment logs here...",
            height=250
        )

        submitted = st.form_submit_button(
            "🔍 Investigate Deployment",
            use_container_width=True
        )

        if submitted:

            if not deployment_logs.strip():
                st.error("Please paste deployment logs before submitting.")

            else:
                add_activity(
                    "Deployment Intelligence",
                    f"Deployment logs submitted ({platform})"
                )

                st.success("Deployment evidence submitted.")
                backend_not_ready("Deployment Intelligence")

    show_analysis_result(
        st.session_state.deployment_result,
        "Deployment Analysis"
    )

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
            Incidents, code reviews and deployment experiences
            contribute to one shared memory system. Knowledge from
            one engineering task can help solve another.
        </p>
        <span class="dm-tag">Retain</span>
        <span class="dm-tag">Recall</span>
        <span class="dm-tag">Reflect</span>
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
            "🔍 Search Memory",
            use_container_width=True
        )

        if submitted:

            if not search_query.strip():
                st.error("Enter a search query.")

            else:
                st.session_state.memory_query = search_query
                st.info(
                    "Memory search is waiting for the Hindsight backend. "
                    "No memory retrieval has been performed yet."
                )

    st.markdown("---")
    st.subheader("How Shared Memory Works")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">📥</div>
            <h3>Retain</h3>
            <p>
                Store useful engineering experiences, findings
                and feedback with their outcomes.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">🔍</div>
            <h3>Recall</h3>
            <p>
                Retrieve relevant knowledge when a new incident,
                code review or deployment problem appears.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="dm-card">
            <div class="dm-icon">💡</div>
            <h3>Reflect</h3>
            <p>
                Identify patterns across accumulated engineering
                experiences to improve future recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Stored Memories")

    if st.session_state.memory_results:

        for memory in st.session_state.memory_results:
            with st.expander("Engineering Memory"):
                st.write(memory)

    else:
        st.caption(
            "No Hindsight memories are being displayed yet. "
            "Real retained memories will appear here after backend integration."
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown("""
<div style="
    text-align:center;
    color:#A7C7B5;
    font-size:12px;
    padding:10px;">
    <b style="color:#20B486;">DevMemory AI</b>
    &nbsp; | &nbsp;
    Engineering Intelligence Powered by Memory
</div>
""", unsafe_allow_html=True)
