"""
Streamlit Dashboard for Priyanka's Beauty Salon Supervisor.

Design Decision:
- Use Streamlit for rapid development
- Real-time updates with auto-refresh
- Simple, intuitive interface
- All in Python (no TypeScript needed)
"""

import streamlit as st
import requests
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Priyanka's Beauty Salon Dashboard",
    page_icon="💇‍♀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #1f2937;
    }
    .sub-header {
        color: #666;
        margin-bottom: 2rem;
    }
    .stat-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    .stat-label {
        color: #666;
        font-size: 0.875rem;
    }
    .request-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: white;
        color: #1f2937;
    }
    .priority-high {
        border-left: 4px solid #ef4444;
    }
    .priority-medium {
        border-left: 4px solid #f59e0b;
    }
    .priority-low {
        border-left: 4px solid #10b981;
    }
    .kb-entry {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f9fafb;
        margin-bottom: 0.5rem;
        border-left: 3px solid #8b5cf6;
        color: #1f2937;
    }
</style>
""",
    unsafe_allow_html=True,
)


# API Helper Functions
class API:
    """Helper class for API calls."""

    @staticmethod
    def get(endpoint: str):
        """GET request to backend API."""
        try:
            response = requests.get(f"{API_URL}{endpoint}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            return None

    @staticmethod
    def patch(endpoint: str, data: dict):
        """PATCH request to backend API."""
        try:
            response = requests.patch(f"{API_URL}{endpoint}", json=data, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            return None

    @staticmethod
    def post(endpoint: str, data: dict = None):
        """POST request to backend API."""
        try:
            response = requests.post(f"{API_URL}{endpoint}", json=data, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            return None


def format_time_ago(timestamp):
    """Format timestamp as 'X minutes ago'."""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except:
            return "Unknown"
    else:
        dt = timestamp

    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    delta = now - dt

    minutes = delta.total_seconds() / 60
    if minutes < 1:
        return "Just now"
    elif minutes < 60:
        return f"{int(minutes)} min ago"
    else:
        hours = int(minutes / 60)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"


def render_request_card(request):
    """Render a single request card."""
    priority_class = f"priority-{request['priority']}"

    # Calculate time ago
    time_ago = format_time_ago(request["created_at"])

    # Status badge color
    status_colors = {
        "pending": "🔵",
        "in_progress": "🟣",
        "resolved": "🟢",
        "timeout": "⚫",
    }
    status_emoji = status_colors.get(request["status"], "⚪")

    with st.container():
        st.markdown(
            f"""
        <div class="request-card {priority_class}">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <div>
                    <strong style="color: #1f2937;">📞 {request.get('caller_name') or request['caller_id']}</strong>
                    <br/>
                    <span style="font-size: 0.875rem; color: #666;">
                        {status_emoji} {request['status'].replace('_', ' ').title()} | 
                        {request['priority'].title()} Priority
                    </span>
                </div>
                <div style="text-align: right; color: #666; font-size: 0.875rem;">
                    ⏰ {time_ago}
                </div>
            </div>
            <div style="margin-bottom: 1rem;">
                <strong style="color: #666;">Question:</strong><br/>
                <span style="font-size: 1.1rem; color: #1f2937;">{request['question']}</span>
            </div>
            <div style="font-size: 0.875rem; color: #666;">
                <strong>Context:</strong> {request.get('context', 'N/A')}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Response section for resolved requests
        if request["status"] == "resolved" and request.get("supervisor_response"):
            st.success(f"**Response:** {request['supervisor_response']}")
            st.caption(f"Resolved by: {request.get('supervisor_id', 'Unknown')}")

        # Respond button for pending requests
        elif request["status"] == "pending":
            if st.button("Respond", key=f"respond_{request['id']}", type="primary"):
                st.session_state.responding_to = request["id"]
                st.rerun()


def show_response_modal(request):
    """Show response modal for a request."""
    st.subheader("📝 Respond to Request")

    # Show request details
    st.info(
        f"""
    **Caller:** {request.get('caller_name') or request['caller_id']}
    
    **Question:** {request['question']}
    
    **Context:** {request.get('context', 'N/A')}
    """
    )

    # Response form
    with st.form("response_form"):
        response_text = st.text_area(
            "Your Response *",
            height=150,
            placeholder="Enter your answer to the customer's question...",
            help="This answer will be sent to the customer and added to the knowledge base.",
        )

        supervisor_id = st.text_input(
            "Your Supervisor ID",
            value="supervisor-1",
            help="In production, this would come from authentication",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("Submit Response", type="primary")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.responding_to = None
                st.rerun()

        if submitted:
            if not response_text.strip():
                st.error("Please enter a response")
            else:
                # Submit response
                result = API.patch(
                    f"/api/help-requests/{request['id']}",
                    {
                        "supervisor_response": response_text.strip(),
                        "supervisor_id": supervisor_id,
                    },
                )

                if result:
                    st.success("✅ Response submitted! Customer will be notified.")
                    time.sleep(1)
                    st.session_state.responding_to = None
                    st.rerun()


def render_stats():
    """Render statistics overview."""
    stats = API.get("/api/stats")

    if stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
            <div class="stat-box">
                <div class="stat-number" style="color: #3b82f6;">{stats['help_requests']['pending']}</div>
                <div class="stat-label">Pending</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
            <div class="stat-box">
                <div class="stat-number" style="color: #8b5cf6;">{stats['help_requests']['in_progress']}</div>
                <div class="stat-label">In Progress</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
            <div class="stat-box">
                <div class="stat-number" style="color: #10b981;">{stats['help_requests']['resolved']}</div>
                <div class="stat-label">Resolved</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                f"""
            <div class="stat-box">
                <div class="stat-number" style="color: #8b5cf6;">{stats['knowledge_base']['total_entries']}</div>
                <div class="stat-label">KB Entries</div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def show_pending_requests():
    """Show pending requests tab."""
    st.subheader("📋 Pending Requests")

    # Check if responding to a request
    if hasattr(st.session_state, "responding_to") and st.session_state.responding_to:
        # Get the request details
        request = API.get(f"/api/help-requests/{st.session_state.responding_to}")
        if request:
            show_response_modal(request)
            return

    # Load pending requests
    requests_data = API.get("/api/help-requests?status_filter=pending")

    if requests_data is None:
        st.error("Failed to load requests. Is the backend running?")
        return

    if len(requests_data) == 0:
        st.success("🎉 No pending requests! You're all caught up.")
    else:
        st.info(
            f"**{len(requests_data)}** pending request{'s' if len(requests_data) != 1 else ''}"
        )

        for request in requests_data:
            render_request_card(request)


def show_resolved_requests():
    """Show resolved requests tab."""
    st.subheader("✅ Resolved Requests")

    requests_data = API.get("/api/help-requests?status_filter=resolved")

    if requests_data is None:
        st.error("Failed to load requests")
        return

    if len(requests_data) == 0:
        st.info("No resolved requests yet")
    else:
        st.info(
            f"**{len(requests_data)}** resolved request{'s' if len(requests_data) != 1 else ''}"
        )

        for request in requests_data:
            render_request_card(request)


def show_knowledge_base():
    """Show knowledge base tab."""
    st.subheader("📚 Knowledge Base")

    # Filters
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Search knowledge base...")
    with col2:
        category_filter = st.selectbox(
            "Category",
            [
                "all",
                "hours",
                "services",
                "pricing",
                "location",
                "payment",
                "policy",
                "learned",
            ],
        )

    # Load KB entries
    endpoint = "/api/knowledge-base"
    if category_filter != "all":
        endpoint += f"?category={category_filter}"

    entries = API.get(endpoint)

    if entries is None:
        st.error("Failed to load knowledge base")
        return

    # Filter by search term
    if search_term:
        entries = [
            e
            for e in entries
            if search_term.lower() in e["question"].lower()
            or search_term.lower() in e["answer"].lower()
        ]

    st.info(f"**{len(entries)}** entries found")

    # Group by source
    initial = [e for e in entries if e["source"] == "initial_prompt"]
    learned = [e for e in entries if e["source"] == "supervisor_answer"]
    manual = [e for e in entries if e["source"] == "manual_entry"]

    # Display entries
    if initial:
        st.markdown("### 📚 Built-in Knowledge")
        for entry in initial:
            render_kb_entry(entry)

    if learned:
        st.markdown("### 🤖 Learned from Resolutions")
        for entry in learned:
            render_kb_entry(entry, show_source=True)

    if manual:
        st.markdown("### ✍️ Manual Entries")
        for entry in manual:
            render_kb_entry(entry)


def render_kb_entry(entry, show_source=False):
    """Render a knowledge base entry."""
    confidence_color = "#10b981" if entry["confidence"] >= 0.9 else "#f59e0b"

    with st.container():
        st.markdown(
            f"""
        <div class="kb-entry">
            <div style="display: flex; justify-content: between; margin-bottom: 0.5rem;">
                <span style="background-color: {confidence_color}; color: white; padding: 0.25rem 0.5rem; 
                             border-radius: 0.25rem; font-size: 0.75rem; font-weight: bold;">
                    {int(entry['confidence'] * 100)}% Confidence
                </span>
                <span style="background-color: #e5e7eb; color: #374151; padding: 0.25rem 0.5rem; 
                             border-radius: 0.25rem; font-size: 0.75rem; margin-left: 0.5rem;">
                    {entry['category']}
                </span>
            </div>
            <div style="margin-bottom: 0.5rem; color: #1f2937;">
                <strong>Q:</strong> {entry['question']}
            </div>
            <div style="margin-bottom: 0.5rem; color: #1f2937;">
                <strong>A:</strong> {entry['answer']}
            </div>
            <div style="font-size: 0.75rem; color: #666;">
                📊 Used {entry['usage_count']} times
                {f" | 🔗 From request {entry.get('source_request_id', 'N/A')[:8]}..." if show_source and entry.get('source_request_id') else ""}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def main():
    """Main dashboard application."""

    # Initialize session state
    if "responding_to" not in st.session_state:
        st.session_state.responding_to = None

    # Header
    st.markdown(
        '<div class="main-header">💇‍♀️ Priyanka\'s Beauty Salon</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Supervisor Dashboard</div>', unsafe_allow_html=True
    )

    # Stats
    render_stats()

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Pending", "✅ Resolved", "📚 Knowledge Base"])

    with tab1:
        show_pending_requests()

    with tab2:
        show_resolved_requests()

    with tab3:
        show_knowledge_base()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
            st.info(f"Dashboard will refresh every {refresh_interval} seconds")
            time.sleep(refresh_interval)
            st.rerun()

        st.markdown("---")

        # Connection status
        st.subheader("🔌 Connection Status")
        try:
            health = API.get("/health")
            if health and health.get("status") == "healthy":
                st.success("✅ Backend Connected")
            else:
                st.error("❌ Backend Not Responding")
        except:
            st.error("❌ Backend Offline")

        st.markdown("---")

        # Info
        st.subheader("ℹ️ About")
        st.markdown(
            """
        **Human-in-the-Loop AI Agent**
        
        This dashboard allows supervisors to:
        - View and respond to escalated questions
        - Monitor resolved requests
        - View the knowledge base
        
        All responses are automatically added to the knowledge base to improve the AI agent over time.
        """
        )


if __name__ == "__main__":
    main()
