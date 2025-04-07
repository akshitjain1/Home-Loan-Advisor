import streamlit as st
import requests
import json
import time
from dotenv import load_dotenv
import os

# Page Configuration
st.set_page_config(
    page_title="Home Loan Advisor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables from .env file
load_dotenv()

# Load API Key from Environment Variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# API Configuration
MODEL_NAME = "gemini-1.5-pro"

# Initialize Session State
if 'loan_data' not in st.session_state:
    st.session_state.loan_data = {}
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Simplified Response Formatting
def format_loan_response(text):
    """Format response into clean, readable sections"""
    formatted = text.replace("**", "").replace("*", "")
    formatted = formatted.replace("- ", "✓ ").replace("1.", "➊").replace("2.", "➋").replace("3.", "➌")
    return formatted

# API Call Function
def get_structured_response(user_data, question=None):
    prompt = f"""
    You are a friendly home loan advisor. Keep responses concise and clear:
    1. Quick Profile Overview (1-2 sentences)
    2. Loan Approval Chance (Simple percentage)
    3. Interest Rate Range (Short and clear)
    4. Tips to Improve (3-4 short bullets)
    5. Next Steps (2-3 clear steps)
    
    Client Info: {user_data}
    {'Question: ' + question if question else ''}
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return format_loan_response(response.json()['candidates'][0]['content']['parts'][0]['text'])
        return "Oops! Something went wrong. Try again?"
    except Exception:
        return "Connection issue. Please try again."

# Typing Animation
def type_message(message, container):
    message_placeholder = container.empty()
    full_text = ""
    for char in message:
        full_text += char
        message_placeholder.markdown(full_text + "▌")
        time.sleep(0.01)
    message_placeholder.markdown(full_text)

# Main UI
if not st.session_state.chat_started:
    st.title("🏠 Your Dream Home Loan Advisor")
    st.markdown("""
        Buying a home is a big step! Let's simplify it for you. Fill in your details below, 
        and we'll provide personalized advice tailored to your needs.
    """)

    # Form Container
    with st.form("loan_form"):
        st.subheader("Tell Us About Yourself")
        col1, col2 = st.columns(2)

        with col1:
            gender = st.selectbox("Gender", ["Male", "Female"])
            marital_status = st.selectbox("Marital Status", ["Yes", "No"])
            dependents = st.number_input("Number of Dependents", min_value=0, max_value=10, value=0)
            education = st.selectbox("Education Level", ["Graduate", "Not Graduate"])
            self_employed = st.selectbox("Self-Employed", ["Yes", "No"])

        with col2:
            applicant_income = st.number_input("Applicant Income (₹)", min_value=0, max_value=500000, value=0, step=5000)
            coapplicant_income = st.number_input("Co-Applicant Income (₹)", min_value=0, max_value=500000, value=0, step=5000)
            loan_amount = st.number_input("Loan Amount Needed (₹ Lakhs)", min_value=5, max_value=200, value=50)
            tenure = st.slider("Loan Duration (Years)", 5, 30, 15)
            credit_score = st.selectbox("Credit Score", ["<600", "600-700", "700-750", "750-800", "800+"])

        # Submit Button
        submitted = st.form_submit_button("Get Personalized Advice", use_container_width=True)
        if submitted:
            st.session_state.loan_data = {
                "gender": gender,
                "marital_status": marital_status,
                "dependents": dependents,
                "education": education,
                "self_employed": self_employed,
                "applicant_income": applicant_income,
                "coapplicant_income": coapplicant_income,
                "loan_amount": loan_amount * 100000,
                "tenure": tenure,
                "credit_score": credit_score
            }
            st.session_state.chat_started = True
            st.rerun()

else:
    st.title("🏠 Your Loan Assistant")

    # Profile Summary
    with st.sidebar:
        st.subheader("Your Profile")
        st.info(f"""
        **Gender:** {st.session_state.loan_data['gender']}
        **Marital Status:** {st.session_state.loan_data['marital_status']}
        **Dependents:** {st.session_state.loan_data['dependents']}
        **Education:** {st.session_state.loan_data['education']}
        **Self-Employed:** {st.session_state.loan_data['self_employed']}
        **Income:** ₹{st.session_state.loan_data['applicant_income']:,}
        **Co-Applicant Income:** ₹{st.session_state.loan_data['coapplicant_income']:,}
        **Loan:** ₹{st.session_state.loan_data['loan_amount']/100000:.1f}L
        **Tenure:** {st.session_state.loan_data['tenure']} yrs
        **Credit:** {st.session_state.loan_data['credit_score']}
        """)
        if st.button("Edit Profile"):
            st.session_state.chat_started = False
            st.rerun()

    # Chat Area
    chat_container = st.container(height=400)

    # Initial Response
    if not st.session_state.messages:
        with chat_container:
            with st.chat_message("assistant", avatar="🏦"):
                response = get_structured_response(st.session_state.loan_data)
                type_message(response, st)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # Display Chat History
    for msg in st.session_state.messages:
        with chat_container:
            with st.chat_message(msg["role"], avatar="🏦" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    # Chat Input with Suggestions
    st.subheader("Ask More Questions or Get Quick Answers!")
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.chat_input("Ask me anything about your loan...")
    with col2:
        quick_questions = [
            "", 
            "Can I get a lower rate?",
            "How can I improve my chances?",
            "What’s my monthly EMI?",
            "Are there government schemes for me?",
            "What documents do I need?",
            "What if my credit score is low?",
            "Can I prepay my loan?",
        ]
        st.selectbox("Quick Questions", quick_questions, key="quick_q", on_change=lambda: st.session_state.update({"prompt": st.session_state.quick_q}))

    if prompt or "prompt" in st.session_state:
        user_input = prompt or st.session_state.pop("prompt")
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            with st.chat_message("assistant", avatar="🏦"):
                response = get_structured_response(st.session_state.loan_data, user_input)
                type_message(response, st)
                st.session_state.messages.append({"role": "assistant", "content": response})