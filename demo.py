# --------------------------
# app.py - Web-Based AI Data Analysis Agent
# --------------------------

import streamlit as st
import pandas as pd
from datetime import datetime
import re
from fuzzywuzzy import fuzz
import io

# --------------------------
# Agent State
agent_state = {
    "goal": "",
    "input_status": "Not loaded",
    "progress": "Not started",
    "reasoning": ""
}

# --------------------------
# Load Data
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file)
        agent_state["input_status"] = "File loaded successfully"
        return df
    except Exception as e:
        agent_state["input_status"] = f"Failed to load: {e}"
        return None

# --------------------------
# Report Analysis
def analyze_data(data, choice):
    if agent_state["input_status"] != "File loaded successfully":
        return pd.DataFrame(), "Cannot analyze, file not loaded."

    agent_state["progress"] = "Analysis in progress"
    reasoning = []
    output = pd.DataFrame()

    if choice == "1":
        avg = data['Salary'].mean()
        mx = data['Salary'].max()
        mn = data['Salary'].min()
        reasoning.append(f"Average salary: {avg:.2f}")
        reasoning.append(f"Max salary: {mx}, Min salary: {mn}")
        output = data[['Name','Salary']].sort_values('Salary', ascending=False)

    elif choice == "2":
        counts = data['Rank'].value_counts()
        reasoning.append("Rank counts:")
        for r,c in counts.items():
            reasoning.append(f"{r}: {c}")
        output = data[['Name','Rank']]

    elif choice == "3":
        counts = data['State'].value_counts()
        reasoning.append("State counts:")
        for s,c in counts.items():
            reasoning.append(f"{s}: {c}")
        output = data[['Name','State']]

    else:
        reasoning.append(f"Total employees: {len(data)}")
        reasoning.append(f"Avg salary: {data['Salary'].mean():.2f}")
        reasoning.append(f"Max: {data['Salary'].max()}, Min: {data['Salary'].min()}")
        reasoning.append("Rank distribution:\n" + data['Rank'].value_counts().to_string())
        reasoning.append("State distribution:\n" + data['State'].value_counts().to_string())
        output = data.copy()

    agent_state["reasoning"] = "\n".join(reasoning)
    agent_state["progress"] = "Analysis done"
    return output, agent_state["reasoning"]

# --------------------------
# Smart NLP + Urdu/English Q&A
def smart_answer(data, question):
    q = question.lower()
    num = re.findall(r'\d+', q)
    N = int(num[0]) if num else 5

    # Salary
    if "salary" in q or "tanakhwa" in q or "پیسہ" in q:
        if "highest" in q or "sabse zyada" in q or "زیادہ" in q:
            df = data.nlargest(N, 'Salary')[['Name','Salary']]
            return "Top salaries:\n" + df.to_string(index=False)
        if "lowest" in q or "sabse kam" in q or "کم" in q:
            df = data.nsmallest(N, 'Salary')[['Name','Salary']]
            return "Lowest salaries:\n" + df.to_string(index=False)
        if "average" in q or "mean" in q or "اوسط" in q:
            avg = data['Salary'].mean()
            return f"Average salary is {avg:.2f}"

    # Rank
    if "rank" in q or "darja" in q:
        return "Rank distribution:\n" + data['Rank'].value_counts().to_string()

    # State
    if "state" in q or "province" in q or "soobah" in q or "صوبہ" in q:
        return "State distribution:\n" + data['State'].value_counts().to_string()

    # Employee
    if "employee" in q or "name" in q or "list" in q:
        cols = ['Name']
        if "salary" in q: cols.append('Salary')
        if "rank" in q: cols.append('Rank')
        if "state" in q: cols.append('State')
        return data[cols].to_string(index=False)

    # Fuzzy fallback
    words = ["salary","rank","state","employee"]
    scores = [fuzz.partial_ratio(w, q) for w in words]
    if max(scores) > 60:
        best = words[scores.index(max(scores))]
        return smart_answer(data, best)

    return "Sorry, I didn't understand that. Ask about salary, rank, state or employee info."

# --------------------------
# Streamlit Interface - Portfolio Ready
st.set_page_config(
    page_title="AI Data Analysis Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <div style="background-color:#4B8BBE;padding:10px;border-radius:10px">
    <h1 style="color:white;text-align:center;">🤖 AI Data Analysis Agent (Web-Based)</h1>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file:
    data = load_data(uploaded_file)
    if data is not None:
        st.success("✅ File loaded successfully!")
        
        # Sidebar Menu
        menu = ["Analyze Salary", "Analyze Rank", "Analyze State", "Full Report", "Interactive Q&A"]
        choice = st.sidebar.selectbox("Choose a Goal", menu)

        if choice != "Interactive Q&A":
            df, reasoning = analyze_data(data, str(menu.index(choice)+1))
            st.subheader("📄 Report Reasoning")
            st.text(reasoning)
            st.subheader("📊 Data Output")
            st.dataframe(df)

            # ----------------- Download Buttons -----------------
            # CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download Report as CSV",
                data=csv_buffer.getvalue(),
                file_name=f"AI_Agent_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            # Excel
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
            st.download_button(
                label="Download Report as Excel",
                data=excel_buffer.getvalue(),
                file_name=f"AI_Agent_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.subheader("💬 Ask your Questions")
            question = st.text_input("Enter your question:")
            if question:
                ans = smart_answer(data, question)
                st.text(ans)