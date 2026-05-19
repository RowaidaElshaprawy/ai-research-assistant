# ── IMPORTS ──────────────────────────────────────────────────────────────────
import streamlit as st    # the entire UI framework
import requests           # to call our FastAPI backend

# ── CONFIG ───────────────────────────────────────────────────────────────────
# This must be the very first Streamlit command in your file
# page_title = browser tab title, layout="wide" uses full screen width
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide"
)

# The URL of your FastAPI backend
# When running locally, it's always localhost + the port you chose
BACKEND_URL = "http://localhost:8002"


# ── SESSION STATE ─────────────────────────────────────────────────────────────
# Streamlit reruns the entire script every time the user interacts with it
# st.session_state is how we remember values between those reruns
# Think of it like a whiteboard that persists across page refreshes
if "report" not in st.session_state:
    st.session_state.report = ""       # stores the generated report
if "history" not in st.session_state:
    st.session_state.history = []      # stores past research queries


# ── SIDEBAR — RESEARCH HISTORY ───────────────────────────────────────────────
# st.sidebar puts content in the left panel
with st.sidebar:
    st.title("📚 Research History")

    # Button to load past research from the backend database
    if st.button("Refresh History"):
        try:
            # GET request to our /history endpoint
            response = requests.get(f"{BACKEND_URL}/history")
            if response.status_code == 200:
                st.session_state.history = response.json()
        except Exception as e:
            st.error(f"Could not load history: {e}")

    # Display each past query as a button
    # Clicking it would let you reload that report (bonus feature!)
    for item in st.session_state.history:
        st.write(f"🔹 {item['query']}")


# ── MAIN PAGE ────────────────────────────────────────────────────────────────
st.title("🔬 Autonomous AI Research Assistant")
st.markdown(
    "Enter a research topic below. Our team of AI agents will search academic "
    "papers, analyze findings, and generate a comprehensive literature review."
)

st.divider()  # draws a horizontal line


# ── INPUT SECTION ─────────────────────────────────────────────────────────────
# st.text_input creates a text box and returns whatever the user types
query = st.text_input(
    label="Research Topic",
    placeholder="e.g. Transformer Architectures in NLP",
    help="Be specific for better results"
)

# st.button returns True only when clicked
if st.button("🚀 Start Research", type="primary"):

    # Validate the user actually typed something
    if not query.strip():
        st.warning("Please enter a research topic first.")
    else:
        # st.spinner shows a loading animation while the code inside runs
        with st.spinner("AI agents working... This takes 1-2 minutes ⏳"):
            try:
                # POST request to our /research endpoint
                # json= automatically serializes our dict to JSON
                # timeout=180 means wait up to 3 minutes before giving up
                response = requests.post(
                    f"{BACKEND_URL}/research",
                    json={"query": query},
                    timeout=180
                )

                if response.status_code == 200:
                    # Extract the report from the response JSON
                    st.session_state.report = response.json().get("final_report", "")
                    st.success("Research complete! ✅")
                else:
                    # Show the error from the backend
                    st.error(f"Backend error: {response.text}")

            except requests.exceptions.ConnectionError:
                # This happens if the backend server isn't running
                st.error(
                    "Cannot connect to backend. "
                    "Make sure you ran `python main.py` in the backend folder."
                )
            except requests.exceptions.Timeout:
                st.error("Request timed out. The agents took too long. Try a simpler topic.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")


# ── REPORT DISPLAY ────────────────────────────────────────────────────────────
# Only show the report section if we have a report to show
if st.session_state.report:
    st.divider()
    st.subheader("📄 Generated Research Report")

    # st.markdown renders the report with proper formatting
    # (headers, bold text, bullet points — because the report is in Markdown)
    st.markdown(st.session_state.report)

    st.divider()

    # ── DOWNLOAD BUTTONS ──────────────────────────────────────────────────────
    # st.columns splits the page into equal-width columns side by side
    col1, col2 = st.columns(2)

    with col1:
        # Download as Markdown file
        # .encode() converts the string to bytes, which is what files need
        st.download_button(
            label="⬇️ Download as Markdown",
            data=st.session_state.report.encode("utf-8"),
            file_name="research_report.md",
            mime="text/markdown"
        )

    with col2:
        # Download as plain text file
        st.download_button(
            label="⬇️ Download as Text",
            data=st.session_state.report.encode("utf-8"),
            file_name="research_report.txt",
            mime="text/plain"
        )