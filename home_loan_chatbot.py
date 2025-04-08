import streamlit as st
import requests
import json
import time
import math
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-pro"

# Streamlit page config
st.set_page_config(page_title="Home Loan Advisor", page_icon="🏠", layout="wide")

# Session state init
if 'loan_data' not in st.session_state:
    st.session_state.loan_data = {}
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False
if 'messages' not in st.session_state:
    st.session_state.messages = []

# -------- Helper Functions -------- #

def format_loan_response(text):
    formatted = text.replace("**", "").replace("*", "")
    formatted = formatted.replace("- ", "✓ ").replace("1.", "➊").replace("2.", "➋").replace("3.", "➌")
    return formatted

def get_structured_response(user_data, question=None):
    if question:
        prompt = f"""
You are a helpful home loan advisor. Based on the client profile below, answer the question in a clear, structured manner. Keep it concise, professional, and easy to follow.

Client Info: {user_data}
Question: {question}
"""
    else:
        prompt = f"""
You are a friendly home loan advisor. Keep responses concise and clear:
1. Quick Profile Overview (1-2 sentences)
2. Loan Approval Chance (Simple percentage)
3. Interest Rate Range (Short and clear)
4. Tips to Improve (3-4 short bullets)
5. Next Steps (2-3 clear steps)

Client Info: {user_data}
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

def type_message(message, container):
    message_placeholder = container.empty()
    full_text = ""
    for char in message:
        full_text += char
        message_placeholder.markdown(full_text + "▌")
        time.sleep(0.01)
    message_placeholder.markdown(full_text)

def calculate_emi(principal, annual_rate, tenure_years):
    monthly_rate = annual_rate / (12 * 100)
    months = tenure_years * 12
    if monthly_rate == 0:
        emi = principal / months
    else:
        emi = principal * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
    total_payment = emi * months
    total_interest = total_payment - principal
    return round(emi, 2), round(total_interest, 2), round(total_payment, 2)

# -------- UI Starts -------- #

if not st.session_state.chat_started:
    st.title("🏠 Your Dream Home Loan Advisor")
    st.markdown("Fill in your details to get personalized loan advice and EMI breakdown.")

    with st.form("loan_form"):
        st.subheader("👤 Tell Us About Yourself")
        col1, col2 = st.columns(2)

        with col1:
            gender = st.selectbox("Gender", ["Male", "Female"])
            marital_status = st.selectbox("Marital Status", ["Yes", "No"])
            dependents = st.number_input("Number of Dependents", min_value=0, max_value=10, value=0)
            education = st.selectbox("Education Level", ["Graduate", "Not Graduate"])
            self_employed = st.selectbox("Self-Employed", ["Yes", "No"])

        with col2:
            income_period = st.radio("Is your income monthly or yearly?", ["Monthly", "Yearly"])
            applicant_income = st.number_input("Applicant Income (₹)", min_value=0, max_value=10000000, value=0, step=5000)
            coapplicant_income = st.number_input("Co-Applicant Income (₹)", min_value=0, max_value=10000000, value=0, step=5000)
            loan_amount_lakhs = st.number_input("Loan Amount Needed (₹ Lakhs)", min_value=5, max_value=200, value=50)
            tenure = st.slider("Loan Duration (Years)", 5, 30, 15)
            credit_score = st.selectbox("Credit Score", ["<600", "600-700", "700-750", "750-800", "800+"])

        if submitted := st.form_submit_button("💡 Get Personalized Advice", use_container_width=True):
            # Normalize income to monthly
            multiplier = 1 if income_period == "Monthly" else 1/12
            applicant_income_monthly = int(applicant_income * multiplier)
            coapplicant_income_monthly = int(coapplicant_income * multiplier)

            st.session_state.loan_data = {
                "gender": gender,
                "marital_status": marital_status,
                "dependents": dependents,
                "education": education,
                "self_employed": self_employed,
                "applicant_income": applicant_income_monthly,
                "coapplicant_income": coapplicant_income_monthly,
                "loan_amount": int(loan_amount_lakhs * 100000),
                "tenure": tenure,
                "credit_score": credit_score
            }
            st.session_state.chat_started = True
            st.rerun()

else:
    st.title("🏠 Your Loan Assistant")

    # Sidebar Profile Summary
    with st.sidebar:
        st.subheader("📋 Your Profile")
        profile = st.session_state.loan_data
        st.info(f"""
**Gender:** {profile['gender']}
**Marital Status:** {profile['marital_status']}
**Dependents:** {profile['dependents']}
**Education:** {profile['education']}
**Self-Employed:** {profile['self_employed']}
**Income:** ₹{profile['applicant_income']:,}/mo
**Co-Applicant Income:** ₹{profile['coapplicant_income']:,}/mo
**Loan:** ₹{profile['loan_amount']/100000:.1f}L
**Tenure:** {profile['tenure']} yrs
**Credit Score:** {profile['credit_score']}
        """)
        if st.button("✏️ Edit Profile"):
            st.session_state.chat_started = False
            st.rerun()

    # Chat Area
    chat_container = st.container(height=400)

    if not st.session_state.messages:
        with chat_container:
            with st.chat_message("assistant", avatar="🏦"):
                response = get_structured_response(st.session_state.loan_data)
                type_message(response, st)
                st.session_state.messages.append({"role": "assistant", "content": response})

    for msg in st.session_state.messages:
        with chat_container:
            with st.chat_message(msg["role"], avatar="🏦" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    st.subheader("💬 Ask More or Use Quick Tips")
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.chat_input("Ask about loan, documents, rates, eligibility...")
    with col2:
        quick_questions = [
            "", 
            "Can I get a lower rate?",
            "What’s my monthly EMI?",
            "What documents are required?",
            "Can I prepay my loan?",
            "What if my credit score is low?",
        ]
        st.selectbox("Quick Ask", quick_questions, key="quick_q", on_change=lambda: st.session_state.update({"prompt": st.session_state.quick_q}))

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

    # EMI Calculator Section
    with st.expander("📊 EMI Calculator", expanded=False):
        st.markdown("Get an estimate of your monthly EMI, total interest, and total payable amount.")
        interest_rate = st.slider("Expected Interest Rate (%)", 6.0, 12.0, 8.5, 0.1)

        emi, total_interest, total_payment = calculate_emi(
            principal=st.session_state.loan_data["loan_amount"],
            annual_rate=interest_rate,
            tenure_years=st.session_state.loan_data["tenure"]
        )

        st.success(f"**Monthly EMI:** ₹{emi:,}")
        st.info(f"**Total Interest:** ₹{total_interest:,}\n\n**Total Payment:** ₹{total_payment:,}")
