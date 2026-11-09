import streamlit as st
from datetime import datetime

from ai_engine import (
    analyse_incident,
    review_code,
    analyse_deployment,
    store_feedback_result,
    retrieve_memory,
    reflect_on_memories,
    list_memories,
    health_check
)

# =========================================================
# 0. HTML RENDERING FIX
# =========================================================
# Markdown treats any line indented by 4+ spaces as a CODE BLOCK, and a blank line ends an
# HTML block. Most HTML in this file is indented inside `with` / `if` blocks, so Streamlit was
# showing raw <div> tags as text. This wrapper strips that indentation and the blank lines
# for every st.markdown(..., unsafe_allow_html=True) call, so no HTML block needs rewriting.
# The guard keeps Streamlit's reruns from wrapping the function again and again.

import re

if not getattr(st.markdown, "_dm_html_safe", False):
    _original_markdown = st.markdown

    def _html_safe_markdown(body, *args, **kwargs):
        if kwargs.get("unsafe_allow_html") and isinstance(body, str):
            body = re.sub(r"^[ \t]+", "", body, flags=re.MULTILINE)
            body = re.sub(r"\n\s*\n+", "\n", body).strip()
        return _original_markdown(body, *args, **kwargs)

    _html_safe_markdown._dm_html_safe = True
    st.markdown = _html_safe_markdown

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="DevMemory AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. SESSION STATE
# =========================================================

DEFAULTS = {
    "analysis_history": [],
    "memory_results": [],
    "backend_connected": False,
    "health_status": None,
    "last_results": {},
    "feedback_status": {},
    "reflection_result": None,
    "stored_memories": []
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 3. PLUM, MAUVE AND CREAM DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700;800&display=swap'
);

/* COLOUR VARIABLES */

:root {
    --bg: #FBF4E9;
    --sidebar: #502D55;
    --sidebar-light: #67416B;
    --surface: #FFFFFF;
    --surface-soft: #F6DBC0;
    --primary: #935073;
    --primary-hover: #78415E;
    --primary-light: #F1DCE6;
    --border: #E8D5D0;
    --text: #502D55;
    --muted: #806A7A;
    --success: #38765B;
    --warning: #A66C32;
}

/* MAIN PAGE */

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
    color: var(--text) !important;
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
    font-weight: 700 !important;
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
    border-right: 1px solid #76577A;
}

[data-testid="stSidebar"] * {
    color: #FBF4E9;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #F6DBC0;
}

[data-testid="stSidebar"] .stRadio label {
    font-size: 14px;
    font-weight: 600;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 8px;
    padding: 5px 8px;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: var(--sidebar-light);
}

/* INPUTS */

.stTextArea textarea,
.stTextInput input {
    background-color: #FFFFFF !important;
    color: #502D55 !important;
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
    background-color: #FFFFFF !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}

[data-baseweb="popover"] {
    color: var(--text);
}

/* BUTTONS */

.stButton > button,
.stFormSubmitButton > button {
    background: var(--primary);
    color: #FFFFFF !important;
    border: none;
    border-radius: 9px;
    padding: 0.55rem 1.2rem;
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    transition: 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: var(--primary-hover);
    color: #FFFFFF !important;
    border: none;
    transform: translateY(-1px);
}

/* CARDS */

.dm-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 22px;
    min-height: 145px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(80, 45, 85, 0.07);
}

.dm-card h3 {
    font-size: 18px !important;
    margin-top: 0;
    margin-bottom: 8px;
}

.dm-card p {
    color: var(--muted) !important;
    font-size: 13px;
    line-height: 1.7;
    margin-bottom: 0;
}

.dm-icon {
    font-size: 25px;
    margin-bottom: 12px;
}

/* METRICS */

.dm-metric {
    background: #FFFFFF;
    border: 1px solid var(--border);
    padding: 20px;
    border-radius: 13px;
    box-shadow: 0 4px 14px rgba(80, 45, 85, 0.06);
}

.dm-metric-label {
    font-size: 12px;
    color: var(--muted) !important;
    margin-bottom: 8px;
    font-weight: 600;
    letter-spacing: 0.4px;
}

.dm-metric-value {
    font-family: 'DM Sans', sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: var(--text) !important;
}

/* HERO SECTION */

.dm-hero {
    background: linear-gradient(120deg, #F6DBC0, #FBF4E9);
    border: 1px solid #E9C9B7;
    border-radius: 18px;
    padding: 32px;
    margin-bottom: 25px;
}

.dm-hero h1 {
    margin-top: 15px;
    margin-bottom: 8px;
    color: #502D55 !important;
}

.dm-hero p {
    color: #806A7A !important;
    font-size: 15px;
    line-height: 1.7;
}

/* STATUS BADGE */

.dm-status {
    display: inline-block;
    background: #F1DCE6;
    color: #502D55 !important;
    border: 1px solid #DDBBCC;
    padding: 5px 11px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
}

/* FORMS */

[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 13px;
    padding: 18px;
}

/* EXPANDERS */

[data-testid="stExpander"] {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 10px;
}

/* ALERTS */

[data-testid="stAlert"] {
    border-radius: 10px;
}

/* The sidebar rule above makes ALL sidebar text cream, which is invisible on the light
   status box and the light "Connection details" expander. Use dark plum text on them. */
[data-testid="stSidebar"] [data-testid="stAlert"] *,
[data-testid="stSidebar"] [data-testid="stExpander"] * {
    color: #3B1F40 !important;
}

/* METRIC WIDGETS */

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid var(--border);
    padding: 15px;
    border-radius: 12px;
}

/* DIVIDERS */

hr {
    border-color: var(--border) !important;
}

/* FOOTER AND STREAMLIT BRANDING */

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
# 4. HELPER FUNCTIONS
# =========================================================

def add_activity(module, description):
    """Add a new activity to the dashboard."""

    activity = {
        "module": module,
        "description": description,
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

    st.session_state.analysis_history.insert(0, activity)


def show_page_header(title, description):
    """Display a consistent heading on every page."""

    st.title(title)
    st.caption(description)
    st.markdown("---")


def safe_list(value):
    """Convert a result into a list safely."""

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def render_memory_items(memories):
    """Display memories returned by Hindsight."""

    if not memories:
        st.caption("No relevant previous memories found.")
        return

    for memory in safe_list(memories):

        if isinstance(memory, dict):

            memory_text = (
                memory.get("text")
                or memory.get("content")
                or str(memory)
            )

            memory_type = memory.get("type")
            status = memory.get("status")

            with st.container(border=True):

                if memory_type:
                    st.caption(f"Type: {memory_type}")

                st.write(memory_text)

                if status:
                    st.caption(f"Status: {status}")

        else:
            st.info(str(memory))


def render_recommendations(recommendations):
    """Display AI recommendations."""

    recommendations = safe_list(recommendations)

    if not recommendations:
        st.caption("No recommendations were returned.")
        return

    for recommendation in recommendations:
        st.markdown(f"- {recommendation}")


def render_warnings(result):
    """Display backend warnings."""

    for warning in safe_list(result.get("warnings")):
        st.warning(str(warning))


def render_common_memory_details(result):
    """Display shared Hindsight memory information."""

    insight = result.get("memory_insight")

    if insight:
        st.markdown("**Memory Insight**")
        st.write(insight)

    recalled = result.get("recalled_memories", [])

    st.markdown("**Previous Engineering Experiences**")
    render_memory_items(recalled)

    verified = result.get("previously_verified_solutions", [])

    if verified:
        st.markdown("**Previously Developer-Verified Fixes**")

        for fix in safe_list(verified):
            st.success(str(fix))

    failed = result.get("previously_failed_attempts", [])

    if failed:
        st.markdown("**Previously Unsuccessful Attempts**")

        for attempt in safe_list(failed):
            st.warning(str(attempt))

    st.caption(
        f"Memory status: {result.get('memory_status', 'unknown')}"
    )

    render_warnings(result)


# =========================================================
# 5. DEVELOPER FEEDBACK
# =========================================================

def render_feedback(module_key):
    """
    Record feedback only when a developer explicitly submits it.
    Feedback is retained in Hindsight through the backend.
    """

    result = st.session_state.last_results.get(module_key)

    if not result:
        return

    problem_id = result.get("problem_id")

    if not problem_id:
        return

    st.markdown("---")
    st.subheader("📝 Developer Feedback")

    st.caption(
        "Only record an outcome after applying and testing a fix. "
        "This feedback helps Hindsight learn from real experience."
    )

    with st.form(f"feedback_form_{module_key}"):

        outcome = st.selectbox(
            "What happened after applying the fix?",
            [
                "Choose an outcome",
                "Success - Fix worked",
                "Failure - Fix did not work"
            ],
            key=f"outcome_{module_key}"
        )

        fix_applied = st.text_area(
            "Fix applied (optional)",
            placeholder="Describe the change you actually made...",
            key=f"fix_applied_{module_key}"
        )

        developer_note = st.text_area(
            "Additional developer notes (optional)",
            placeholder="What did you observe after testing?",
            key=f"developer_note_{module_key}"
        )

        submitted = st.form_submit_button(
            "Save Developer Feedback",
            use_container_width=True
        )

        if submitted:

            if outcome == "Choose an outcome":

                st.error("Please select the actual outcome first.")

            else:

                outcome_value = (
                    "success"
                    if outcome.startswith("Success")
                    else "failure"
                )

                with st.spinner(
                    "Retaining developer feedback in Hindsight..."
                ):

                    try:

                        response = store_feedback_result(
                            problem_id,
                            outcome_value,
                            developer_note=developer_note,
                            fix_applied=fix_applied
                        )

                        if response.get("ok"):

                            st.session_state.feedback_status[module_key] = (
                                response
                            )

                            st.success(
                                "Developer feedback retained successfully."
                            )

                        else:

                            st.error(
                                response.get(
                                    "error",
                                    "Feedback could not be retained."
                                )
                            )

                    except Exception as exc:
                        st.error(f"Feedback error: {exc}")

    saved_feedback = st.session_state.feedback_status.get(module_key)

    if saved_feedback:

        st.success(
            f"Last recorded outcome: "
            f"{saved_feedback.get('outcome', 'saved')}"
        )


# =========================================================
# 6. INCIDENT RESULT DISPLAY
# =========================================================

def render_incident_result(result):

    st.subheader("🔍 Incident Analysis Results")

    st.markdown("**Incident Identified**")
    st.write(result.get("title", "Not identified"))

    st.markdown("**Possible Root Cause**")
    st.write(result.get("root_cause", "Not available"))

    st.markdown("**Confidence**")
    st.write(str(result.get("confidence", "Not available")).title())

    st.markdown("**Recommended Actions**")
    render_recommendations(result.get("recommendations"))

    render_common_memory_details(result)


# =========================================================
# 7. CODE REVIEW RESULT DISPLAY
# =========================================================

def render_code_review_result(result):

    st.subheader("🔍 Code Review Results")

    summary = result.get("summary")

    if summary:
        st.markdown("**Review Summary**")
        st.write(summary)

    findings = (
        result.get("findings_detailed")
        or result.get("findings")
        or []
    )

    st.markdown("**Findings**")

    if not findings:

        st.info("No findings were returned.")

    else:

        for index, finding in enumerate(
            safe_list(findings),
            start=1
        ):

            with st.container(border=True):

                if isinstance(finding, dict):

                    heading = (
                        finding.get("title")
                        or finding.get("issue")
                        or finding.get("category")
                        or f"Finding {index}"
                    )

                    st.markdown(f"**{index}. {heading}**")

                    severity = finding.get("severity")

                    if severity:
                        st.caption(f"Severity: {severity}")

                    line = finding.get("line")

                    if line:
                        st.caption(f"Line: {line}")

                    description = (
                        finding.get("description")
                        or finding.get("explanation")
                        or finding.get("details")
                    )

                    if description:
                        st.write(description)

                    recommendation = (
                        finding.get("recommendation")
                        or finding.get("suggestion")
                        or finding.get("fix")
                    )

                    if recommendation:

                        st.markdown("**Suggested improvement:**")
                        st.write(recommendation)

                else:

                    st.write(f"{index}. {finding}")

    suggestions = result.get("suggestions", [])

    if suggestions:

        st.markdown("**Additional Suggestions**")
        render_recommendations(suggestions)

    st.markdown("---")
    render_common_memory_details(result)


# =========================================================
# 8. DEPLOYMENT RESULT DISPLAY
# =========================================================

def render_deployment_result(result):

    st.subheader("🔍 Deployment Analysis Results")

    st.markdown("**Failed Pipeline Stage**")
    st.write(result.get("failed_stage", "Not identified"))

    st.markdown("**Possible Cause**")
    st.write(result.get("possible_cause", "Not available"))

    st.markdown("**Confidence**")
    st.write(str(result.get("confidence", "Not available")).title())

    st.markdown("**Recommended Actions**")
    render_recommendations(result.get("recommendations"))

    render_common_memory_details(result)


# =========================================================
# 9. BACKEND HEALTH CHECK
# =========================================================

def run_health_check():
    """
    Check both Hindsight and Groq.
    The connection status is based on the actual health check,
    not merely on whether an analysis returned successfully.
    """

    try:

        status = health_check()

        st.session_state.health_status = status

        hindsight_ok = (
            status.get("hindsight", {}).get("ok", False)
        )

        llm_ok = (
            status.get("llm", {}).get("ok", False)
        )

        st.session_state.backend_connected = (
            hindsight_ok and llm_ok
        )

    except Exception as exc:

        st.session_state.backend_connected = False

        st.session_state.health_status = {
            "error": str(exc)
        }


# Run health check once when the app session starts.

if st.session_state.health_status is None:
    run_health_check()


# =========================================================
# 10. SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="padding: 10px 0 20px 0;">

            <div style="font-size: 34px;">
                🧠
            </div>

            <div style="
                font-family: 'DM Sans', sans-serif;
                font-size: 25px;
                font-weight: 800;
                color: #FBF4E9;">
                DevMemory<span style="color:#F6DBC0;"> AI</span>
            </div>

            <div style="
                color: #F6DBC0;
                font-size: 10px;
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
        """
        <span style="
            background:#F6DBC0;
            color:#502D55;
            padding:5px 10px;
            border-radius:20px;
            font-size:11px;
            font-weight:700;">
            ● MVP DEVELOPMENT
        </span>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.backend_connected:

        st.success("AI Backend Connected")

    else:

        st.warning("AI Backend Not Fully Connected")

        if st.session_state.health_status:

            with st.expander("Connection details"):

                st.write(
                    st.session_state.health_status
                )

    if st.button(
        "Refresh Connection Status",
        use_container_width=True
    ):

        with st.spinner("Checking services..."):
            run_health_check()

        st.rerun()

    st.caption("Powered by Hindsight Memory")


# =========================================================
# 11. DASHBOARD
# =========================================================

if page == "Dashboard":

    # HERO SECTION

    st.markdown("""
    <div class="dm-hero">

        <div class="dm-status">
            INTELLIGENT ENGINEERING WORKSPACE
        </div>

        <h1>
            Engineering, with memory.
        </h1>

        <p>
            Learn from every incident. Improve every code review.
            Make every deployment smarter.
        </p>

    </div>
    """, unsafe_allow_html=True)

    st.subheader("Your Engineering Overview")

    col1, col2, col3 = st.columns(3)

    total_activities = len(
        st.session_state.analysis_history
    )

    # TOTAL ACTIVITIES

    with col1:

        st.markdown(f"""
        <div class="dm-metric">

            <div class="dm-metric-label">
                TOTAL ACTIVITIES
            </div>

            <div class="dm-metric-value">
                {total_activities}
            </div>

            <div class="dm-metric-label">
                This session
            </div>

        </div>
        """, unsafe_allow_html=True)

    # INTELLIGENCE MODULES

    with col2:

        st.markdown("""
        <div class="dm-metric">

            <div class="dm-metric-label">
                INTELLIGENCE MODULES
            </div>

            <div class="dm-metric-value">
                03
            </div>

            <div class="dm-metric-label">
                Incident · Code · Deployment
            </div>

        </div>
        """, unsafe_allow_html=True)

    # HINDSIGHT STATUS

    with col3:

        memory_status = (
            "Connected"
            if st.session_state.backend_connected
            else "Check Connection"
        )

        st.markdown(f"""
        <div class="dm-metric">

            <div class="dm-metric-label">
                HINDSIGHT MEMORY
            </div>

            <div class="dm-metric-value"
                 style="font-size:22px;">
                {memory_status}
            </div>

            <div class="dm-metric-label">
                Shared engineering memory
            </div>

        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # MODULE CARDS

    st.subheader("Explore Intelligence Modules")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="dm-card">

            <div class="dm-icon">🚨</div>

            <h3>
                Incident Intelligence
            </h3>

            <p>
                Analyse error logs, identify possible root causes
                and retrieve relevant solutions from past incidents.
            </p>

        </div>

        <div class="dm-card">

            <div class="dm-icon">🚀</div>

            <h3>
                Deployment Intelligence
            </h3>

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

            <h3>
                Intelligent Code Review
            </h3>

            <p>
                Examine code for potential bugs, security risks
                and coding convention violations.
            </p>

        </div>

        <div class="dm-card">

            <div class="dm-icon">🧠</div>

            <h3>
                Memory Explorer
            </h3>

            <p>
                Explore stored engineering experiences and
                retrieve relevant memories across all modules.
            </p>

        </div>
        """, unsafe_allow_html=True)

    # RECENT ACTIVITY

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
            "No activity yet. Start by analysing an incident, "
            "reviewing code or checking a deployment."
        )

    st.markdown("---")

    st.caption(
        "DevMemory AI | An engineering assistant that learns from experience."
    )


# =========================================================
# 12. INCIDENT INTELLIGENCE
# =========================================================

elif page == "Incident Intelligence":

    show_page_header(
        "🚨 Incident Intelligence",
        "Understand production errors and learn from previous incidents."
    )

    st.markdown("""
    <div class="dm-card">

        <h3>
            Investigate an Incident
        </h3>

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

            st.error(
                "Please enter incident logs before submitting."
            )

        else:

            add_activity(
                "Incident Intelligence",
                incident_title.strip() or f"{severity} incident submitted"
            )

            incident_context = (
                f"Incident title: {incident_title.strip() or 'Not provided'}\n"
                f"Severity: {severity}\n\n"
                f"{incident_logs}"
            )

            # Remove an older result before starting a new analysis.

            st.session_state.last_results.pop(
                "incident",
                None
            )

            with st.spinner(
                "AI is investigating the incident..."
            ):

                try:

                    result = analyse_incident(
                        incident_context
                    )

                    if result.get("error"):

                        st.error(result["error"])

                    else:

                        st.session_state.last_results["incident"] = result

                        st.success(
                            "Incident analysis completed!"
                        )

                except Exception as exc:

                    st.error(
                        f"Incident analysis failed: {exc}"
                    )

    result = st.session_state.last_results.get("incident")

    if result:

        render_incident_result(result)

        render_feedback("incident")

    # MODULE CAPABILITIES

    st.markdown("---")

    st.subheader("What this module provides")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="dm-card">

            <h3>
                🔍 Investigation
            </h3>

            <p>
                Possible root cause, error classification
                and related historical incidents.
            </p>

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="dm-card">

            <h3>
                🧠 Learning
            </h3>

            <p>
                Previously confirmed fixes, troubleshooting
                recommendations and feedback-based memory retention.
            </p>

        </div>
        """, unsafe_allow_html=True)


# =========================================================
# 13. INTELLIGENT CODE REVIEW
# =========================================================

elif page == "Code Review":

    show_page_header(
        "💻 Intelligent Code Review",
        "Identify potential code issues and recall engineering conventions."
    )

    st.markdown("""
    <div class="dm-card">

        <h3>
            Review Your Code
        </h3>

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
            default=[
                "Bug Detection",
                "Code Quality"
            ]
        )

        submitted = st.form_submit_button(
            "Review Code",
            use_container_width=True
        )

    if submitted:

        if not code_input.strip():

            st.error(
                "Please paste some code before submitting."
            )

        else:

            add_activity(
                "Code Review",
                f"{language} code submitted for review"
            )

            st.session_state.last_results.pop(
                "code_review",
                None
            )

            with st.spinner(
                "AI is reviewing your code..."
            ):

                try:

                    # The current backend accepts code and language.
                    # Review-focus selections are displayed in the UI,
                    # but are not yet passed as backend arguments.

                    result = review_code(
                        code_input,
                        language
                    )

                    if result.get("error"):

                        st.error(result["error"])

                    else:

                        st.session_state.last_results["code_review"] = (
                            result
                        )

                        st.success(
                            "Code review completed!"
                        )

                except Exception as exc:

                    st.error(
                        f"Code review failed: {exc}"
                    )

    result = st.session_state.last_results.get("code_review")

    if result:

        render_code_review_result(result)

        render_feedback("code_review")

    # REVIEW CAPABILITIES

    st.markdown("---")

    st.subheader("Review Capabilities")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""
        <div class="dm-card">

            <div class="dm-icon">🐛</div>

            <h3>
                Bug Detection
            </h3>

            <p>
                Identify potential logical and runtime errors.
            </p>

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="dm-card">

            <div class="dm-icon">🔐</div>

            <h3>
                Security
            </h3>

            <p>
                Highlight possible security vulnerabilities.
            </p>

        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown("""
        <div class="dm-card">

            <div class="dm-icon">✨</div>

            <h3>
                Code Quality
            </h3>

            <p>
                Suggest improvements to readability
                and maintainability.
            </p>

        </div>
        """, unsafe_allow_html=True)


# =========================================================
# 14. DEPLOYMENT INTELLIGENCE
# =========================================================

elif page == "Deployment Intelligence":

    show_page_header(
        "🚀 Deployment Intelligence",
        "Investigate pipeline failures and learn from deployment history."
    )

    st.markdown("""
    <div class="dm-card">

        <h3>
            Investigate a Deployment
        </h3>

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

            st.error(
                "Please enter deployment logs before submitting."
            )

        else:

            add_activity(
                "Deployment Intelligence",
                f"{platform} - {stage} stage submitted"
            )

            deployment_context = (
                f"Deployment platform: {platform}\n"
                f"Pipeline stage selected by developer: {stage}\n\n"
                f"{deployment_logs}"
            )

            st.session_state.last_results.pop(
                "deployment",
                None
            )

            with st.spinner(
                "AI is investigating the deployment..."
            ):

                try:

                    result = analyse_deployment(
                        deployment_context
                    )

                    if result.get("error"):

                        st.error(result["error"])

                    else:

                        st.session_state.last_results["deployment"] = (
                            result
                        )

                        st.success(
                            "Deployment analysis completed!"
                        )

                except Exception as exc:

                    st.error(
                        f"Deployment analysis failed: {exc}"
                    )

    result = st.session_state.last_results.get("deployment")

    if result:

        render_deployment_result(result)

        render_feedback("deployment")

    # DEPLOYMENT CAPABILITIES

    st.markdown("---")

    st.subheader("Deployment Analysis Capabilities")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="dm-card">

            <h3>
                ⚙️ Failure Investigation
            </h3>

            <p>
                Failed pipeline stage identification, build errors
                and configuration issue detection.
            </p>

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="dm-card">

            <h3>
                🧠 Historical Learning
            </h3>

            <p>
                Similar historical failures, previously confirmed fixes
                and troubleshooting recommendations.
            </p>

        </div>
        """, unsafe_allow_html=True)


# =========================================================
# 15. MEMORY EXPLORER
# =========================================================

elif page == "Memory Explorer":

    show_page_header(
        "🧠 Memory Explorer",
        "Explore engineering knowledge retained and retrieved by DevMemory AI."
    )

    st.markdown("""
    <div class="dm-card">

        <h3>
            One Shared Engineering Memory
        </h3>

        <p>
            DevMemory AI connects incidents, code reviews and deployment
            experiences through a shared Hindsight memory system.
        </p>

    </div>
    """, unsafe_allow_html=True)

    # MEMORY SEARCH

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

            module_map = {
                "All Memories": None,
                "Incidents": "incident",
                "Code Reviews": "code_review",
                "Deployments": "deployment",
                "Confirmed Fixes": None
            }

            query = search_query.strip()

            if memory_type == "Confirmed Fixes":

                query += (
                    " developer-verified successful fixes "
                    "confirmed by the developer"
                )

            with st.spinner(
                "Searching Hindsight memories..."
            ):

                try:

                    response = retrieve_memory(
                        query,
                        module=module_map[memory_type]
                    )

                    if response.get("ok"):

                        st.session_state.memory_results = (
                            response.get("memories", [])
                        )

                        st.success(
                            "Memory search completed!"
                        )

                    else:

                        st.error(
                            response.get(
                                "error",
                                "Memory search could not be completed."
                            )
                        )

                except Exception as exc:

                    st.error(
                        f"Memory search failed: {exc}"
                    )

    if st.session_state.memory_results:

        st.markdown("### Retrieved Memories")

        render_memory_items(
            st.session_state.memory_results
        )

    # REFLECTION

    st.markdown("---")

    st.subheader("Reflect on Engineering Experience")

    with st.form("reflection_form"):

        reflection_query = st.text_input(
            "What would you like the AI to reflect on?",
            placeholder="Example: Common causes of deployment failures"
        )

        reflect_submitted = st.form_submit_button(
            "Reflect on Memories",
            use_container_width=True
        )

    if reflect_submitted:

        if not reflection_query.strip():

            st.error(
                "Enter a topic for reflection."
            )

        else:

            with st.spinner(
                "Hindsight is reflecting on memories..."
            ):

                try:

                    response = reflect_on_memories(
                        reflection_query.strip()
                    )

                    if response.get("ok"):

                        st.session_state.reflection_result = (
                            response.get(
                                "text",
                                "No reflection returned."
                            )
                        )

                    else:

                        st.error(
                            response.get(
                                "error",
                                "Reflection could not be completed."
                            )
                        )

                except Exception as exc:

                    st.error(
                        f"Reflection failed: {exc}"
                    )

    if st.session_state.reflection_result:

        st.markdown("### Reflection Result")

        with st.container(border=True):

            st.write(
                st.session_state.reflection_result
            )

    # MEMORY ARCHITECTURE

    st.markdown("---")

    st.subheader("Memory Architecture")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""
        <div class="dm-card">

            <div class="dm-icon">📥</div>

            <h3>
                Retain
            </h3>

            <p>
                Store useful engineering experiences and
                developer-confirmed outcomes.
            </p>

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="dm-card">

            <div class="dm-icon">🔍</div>

            <h3>
                Recall
            </h3>

            <p>
                Retrieve relevant knowledge from previous
                engineering experiences.
            </p>

        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown("""
        <div class="dm-card">

            <div class="dm-icon">💡</div>

            <h3>
                Reflect
            </h3>

            <p>
                Identify patterns and learn from
                accumulated engineering experience.
            </p>

        </div>
        """, unsafe_allow_html=True)

    # STORED MEMORIES

    st.markdown("---")

    st.subheader("Stored Memories")

    if st.button(
        "Refresh Stored Memories",
        use_container_width=True
    ):

        with st.spinner(
            "Loading stored Hindsight memories..."
        ):

            try:

                response = list_memories(limit=50)

                if response.get("ok"):

                    st.session_state.stored_memories = (
                        response.get("items", [])
                    )

                    st.success(
                        "Stored memories refreshed."
                    )

                else:

                    st.error(
                        response.get(
                            "error",
                            "Could not load stored memories."
                        )
                    )

            except Exception as exc:

                st.error(
                    f"Could not load memories: {exc}"
                )

    if st.session_state.stored_memories:

        for index, memory in enumerate(
            st.session_state.stored_memories,
            start=1
        ):

            with st.container(border=True):

                st.markdown(f"**Memory {index}**")

                st.write(str(memory))

    else:

        st.caption(
            "Click Refresh Stored Memories to load actual memories "
            "from Hindsight. New experiences are retained after "
            "developer feedback is recorded."
        )


# =========================================================
# 16. FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#806A7A;
        font-size:12px;
        padding:10px;">

        <b style="color:#935073;">
            DevMemory AI
        </b>

        &nbsp; | &nbsp;

        Engineering Intelligence Powered by Memory

    </div>
    """,
    unsafe_allow_html=True
)