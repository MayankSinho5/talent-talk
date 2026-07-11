import streamlit as st
from src.dynamic_workflow import build_workflow, AgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage, BaseMessage
import os
import json

# --- Page Config & Styling ---
st.set_page_config(page_title="Talent Talk - AI Interviewer", layout="wide", page_icon="🤖")

# Inject premium custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Main App Layout */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0B0F19;
    color: #F3F4F6;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Headings and Titles */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    letter-spacing: -0.02em;
}

.main-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
}

.subtitle {
    color: #9CA3AF;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Chat Input Bar Adjustments */
[data-testid="stChatInput"] {
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background-color: #1F2937 !important;
}

/* Expander Glassmorphism */
.streamlit-expanderHeader {
    background-color: rgba(31, 41, 55, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 8px !important;
    color: #E5E7EB !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s ease;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

/* Dynamic Stepper Styles */
.stepper-container {
    background: rgba(17, 24, 39, 0.7);
    padding: 1.25rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 1.5rem;
    backdrop-filter: blur(10px);
}

.step-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
}

.step-dot {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    font-size: 11px;
    font-weight: bold;
    background-color: #374151;
    color: #9CA3AF;
    transition: all 0.3s ease;
}

.step-dot.active {
    background-color: #6366F1;
    color: white;
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);
}

.step-dot.completed {
    background-color: #10B981;
    color: white;
}

.step-text {
    font-size: 14px;
    color: #9CA3AF;
    font-weight: 400;
}

.step-text.active {
    color: #F9FAFB;
    font-weight: 600;
}

.step-text.completed {
    color: #6B7280;
}
</style>
""", unsafe_allow_html=True)

# Main Title Headers
st.markdown('<h1 class="main-title">Talent Talk</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-powered technical interviews with dynamic resume analysis</p>', unsafe_allow_html=True)

# --- Sidebar: Setup & Configuration ---
st.sidebar.header("⚙️ Configuration")

# Setup default values
current_mode = st.session_state.state.get("mode", "friendly") if "state" in st.session_state else "friendly"
current_position = st.session_state.state.get("position", "AI Developer") if "state" in st.session_state else "AI Developer"
current_company = st.session_state.state.get("company_name", "Tech Innovators Inc.") if "state" in st.session_state else "Tech Innovators Inc."
current_num_q = st.session_state.state.get("num_of_q", 2) if "state" in st.session_state else 2
current_num_follow = st.session_state.state.get("num_of_follow_up", 1) if "state" in st.session_state else 1

# Setup Form
mode = st.sidebar.selectbox("Interviewer Mode", ["friendly", "formal", "technical"], index=["friendly", "formal", "technical"].index(current_mode))
position = st.sidebar.text_input("Position", value=current_position)
company = st.sidebar.text_input("Company Name", value=current_company)
num_of_q = st.sidebar.number_input("Number of Technical Questions", min_value=1, max_value=10, value=current_num_q)
num_of_follow_up = st.sidebar.number_input("Number of Follow-up Questions", min_value=0, max_value=3, value=current_num_follow)

params_changed = (
    "state" in st.session_state and (
        mode != st.session_state.state.get("mode") or
        position != st.session_state.state.get("position") or
        company != st.session_state.state.get("company_name") or
        num_of_q != st.session_state.state.get("num_of_q") or
        num_of_follow_up != st.session_state.state.get("num_of_follow_up")
    )
)

if params_changed:
    st.sidebar.warning("Parameters changed. Click below to apply.")
    
if st.sidebar.button("Update Parameters") and "state" in st.session_state:
    st.session_state.state["mode"] = mode
    st.session_state.state["position"] = position
    st.session_state.state["company_name"] = company
    st.session_state.state["num_of_q"] = num_of_q
    st.session_state.state["num_of_follow_up"] = num_of_follow_up
    st.sidebar.success("Parameters updated!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📁 Document Uploads")

# Resume Upload
resume_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"], key="resume_uploader")
resume_path = None
if resume_file:
    resume_dir = "./uploaded_resumes"
    os.makedirs(resume_dir, exist_ok=True)
    resume_path = os.path.join(resume_dir, resume_file.name)
    with open(resume_path, "wb") as f:
        f.write(resume_file.read())
    st.sidebar.success(f"Uploaded: {resume_file.name}")

# Questions Upload
questions_file = st.sidebar.file_uploader("Upload Custom Questions (PDF)", type=["pdf"], key="questions_uploader")
questions_path = None
if questions_file:
    questions_dir = "./uploaded_questions"
    os.makedirs(questions_dir, exist_ok=True)
    questions_path = os.path.join(questions_dir, questions_file.name)
    with open(questions_path, "wb") as f:
        f.write(questions_file.read())
    st.sidebar.success(f"Uploaded: {questions_file.name}")

# --- Initialize Workflow ---
workflow = build_workflow()

# --- Helpers ---
def get_current_step(messages, report_generated=False):
    if not messages:
        return "Setup"
    
    # Check if the interview has ended
    interview_ended = False
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and "that's it for today" in msg.content.lower():
            interview_ended = True
            break
            
    if interview_ended:
        return "Finished"
        
    # Count candidate messages
    human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    if len(human_msgs) == 0:
        return "Introduction"
    elif len(human_msgs) == 1:
        return "Resume Review"
    else:
        return "Technical Round"

def render_stepper(current_step):
    steps = ["Setup", "Introduction", "Resume Review", "Technical Round", "Finished"]
    current_idx = steps.index(current_step)
    
    html = '<div class="stepper-container">'
    html += '<h4 style="margin-top:0; margin-bottom:12px; color:#F3F4F6;">Interview Progress</h4>'
    
    for i, step in enumerate(steps):
        if i < current_idx:
            dot_class = "step-dot completed"
            text_class = "step-text completed"
            symbol = "✓"
        elif i == current_idx:
            dot_class = "step-dot active"
            text_class = "step-text active"
            symbol = str(i+1)
        else:
            dot_class = "step-dot"
            text_class = "step-text"
            symbol = str(i+1)
            
        html += f'''
        <div class="step-item">
            <span class="{dot_class}">{symbol}</span>
            <span class="{text_class}">{step}</span>
        </div>
        '''
    html += '</div>'
    st.sidebar.markdown(html, unsafe_allow_html=True)

def display_app_state():
    with st.sidebar.expander("🔬 Agent State Debugger", expanded=False):
        state_copy = dict(st.session_state.state)
        if "messages" in state_copy:
            messages_str = []
            for msg in state_copy["messages"]:
                msg_type = type(msg).__name__
                content = msg.content if hasattr(msg, "content") else str(msg)
                messages_str.append(f"{msg_type}: {content}")
            state_copy["messages"] = messages_str
        st.code(str(state_copy), language="python")

# --- Session State Management ---
if "state" not in st.session_state:
    st.session_state.state = AgentState(
        mode=mode,
        num_of_q=num_of_q,
        num_of_follow_up=num_of_follow_up,
        position=position,
        evaluation_result="",
        company_name=company,
        messages=[],
        report="",
        pdf_path=None,
        resume_path=resume_path,
        questions_path=questions_path
    )
    
    # Auto-initialize the greeting message on first load
    with st.spinner("Initializing recruiter agent..."):
        try:
            initial_result = workflow.invoke(st.session_state.state)
            st.session_state.state["messages"] = initial_result.get("messages", [])
        except Exception as e:
            st.error(f"Error initializing recruiter: {str(e)}")
else:
    # Update state paths
    if resume_path and st.session_state.state.get("resume_path") != resume_path:
        st.session_state.state["resume_path"] = resume_path
        st.sidebar.info("Resume updated!")
    if questions_path and st.session_state.state.get("questions_path") != questions_path:
        st.session_state.state["questions_path"] = questions_path
        st.sidebar.info("Questions updated!")

# Render Progress Stepper
current_step = get_current_step(st.session_state.state["messages"])
render_stepper(current_step)

# --- Main App: Chat UI ---
st.subheader("💬 Interview Session")

# Render active chat messages
for m in st.session_state.state["messages"]:
    if isinstance(m, HumanMessage):
        with st.chat_message("user", avatar="👨‍💻"):
            st.write(m.content)
    elif isinstance(m, AIMessage):
        with st.chat_message("assistant", avatar="🤖"):
            st.write(m.content)

# Detect if the interview has ended
interview_ended = False
for msg in reversed(st.session_state.state.get("messages", [])):
    if isinstance(msg, AIMessage) and "that's it for today" in msg.content.lower():
        interview_ended = True
        break

# Chat input at bottom (only visible if interview is active)
if not interview_ended:
    user_input = st.chat_input("Enter your response...")
    if user_input:
        # Add candidate message
        st.session_state.state["messages"].append(HumanMessage(content=user_input))
        
        # Prepare state for execution
        current_state = AgentState(
            mode=st.session_state.state["mode"],
            num_of_q=st.session_state.state["num_of_q"],
            num_of_follow_up=st.session_state.state["num_of_follow_up"],
            position=st.session_state.state["position"],
            company_name=st.session_state.state["company_name"],
            messages=st.session_state.state["messages"],
            evaluation_result="",
            report="",
            pdf_path=st.session_state.state.get("pdf_path"),
            resume_path=st.session_state.state.get("resume_path"),
            questions_path=st.session_state.state.get("questions_path")
        )
        
        # Execute workflow
        with st.spinner("AI Recruiter is processing..."):
            try:
                result = workflow.invoke(current_state)
                st.session_state.state["messages"] = result["messages"]
                st.rerun()
            except Exception as e:
                st.error(f"Error executing recruiter response: {str(e)}")

# Post-Interview: Evaluation & Report Actions
if interview_ended:
    st.markdown("---")
    if not st.session_state.state.get("evaluation_result"):
        st.warning("⚠️ The interview has ended. Please generate the evaluation and report below.")
        if st.button("Generate Candidate Evaluation & HR Report"):
            with st.status("Analyzing responses & creating reports...", expanded=True) as status:
                try:
                    # Run Evaluator Node
                    status.update(label="Step 1: Running AI Evaluator...", state="running")
                    from src.dynamic_workflow import evaluator
                    eval_state = AgentState(
                        mode=st.session_state.state["mode"],
                        num_of_q=st.session_state.state["num_of_q"],
                        num_of_follow_up=st.session_state.state["num_of_follow_up"],
                        position=st.session_state.state["position"],
                        company_name=st.session_state.state["company_name"],
                        messages=st.session_state.state["messages"],
                        evaluation_result="",
                        report="",
                        pdf_path=None,
                        resume_path=st.session_state.state.get("resume_path"),
                        questions_path=st.session_state.state.get("questions_path")
                    )
                    eval_res = evaluator(eval_state)
                    st.session_state.state["evaluation_result"] = eval_res["evaluation_result"]
                    
                    # Run Report Writer Node
                    status.update(label="Step 2: Writing HR Report...", state="running")
                    from src.dynamic_workflow import report_writer
                    eval_state["evaluation_result"] = eval_res["evaluation_result"]
                    rep_res = report_writer(eval_state)
                    st.session_state.state["report"] = rep_res["report"]
                    
                    # Run PDF Generator Node
                    status.update(label="Step 3: Compiling PDF Report...", state="running")
                    from src.dynamic_workflow import pdf_generator_node
                    eval_state["report"] = rep_res["report"]
                    pdf_res = pdf_generator_node(eval_state)
                    st.session_state.state["pdf_path"] = pdf_res["pdf_path"]
                    
                    status.update(label="Reports ready!", state="complete")
                    st.success("Candidate assessment generated successfully!")
                    st.rerun()
                except Exception as e:
                    status.update(label="Failed to generate reports", state="error")
                    st.error(f"Error during report compilation: {str(e)}")
                    
    # Render Evaluation Results
    if st.session_state.state.get("evaluation_result"):
        with st.expander("📊 Candidate Evaluation Details", expanded=True):
            st.markdown(st.session_state.state["evaluation_result"])
            
    # Render HR Report
    if st.session_state.state.get("report"):
        with st.expander("📋 HR Report Summary", expanded=True):
            st.markdown(st.session_state.state["report"])
            
            # Download Button
            pdf_path = st.session_state.state.get("pdf_path")
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Assessment PDF",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf"
                    )

# Sidebar Debugger & Footer
st.sidebar.markdown("---")
display_app_state()

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 13px;">
    <strong>Talent Talk</strong> | Powered by LangGraph, Gemini & Streamlit Cloud
</div>
""", unsafe_allow_html=True)