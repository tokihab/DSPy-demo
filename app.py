import streamlit as st
import pandas as pd
import sqlite3
import os
from dotenv import load_dotenv
import dspy

# We now import the reset_db function
from simulate import init_db, advance_time, reset_db, DB_PATH
from logic import run_agent

# Initialize environment & LLM
load_dotenv()
if "llm_configured" not in st.session_state:
    # 1. MODEL FIX: Pointing to GPT OSS 120B on Groq
    lm = dspy.LM('groq/openai/gpt-oss-120b', api_key=os.environ.get("GROQ_API_KEY"))
    dspy.configure(lm=lm)
    
    init_db()
    st.session_state.llm_configured = True
    st.session_state.chat_history = []

st.set_page_config(page_title="EV Grid Analytics", layout="wide")

# --- SIDEBAR: PHYSICS CONTROLS ---
with st.sidebar:
    st.header("⚡ Grid Physics Simulator")
    st.write("Manipulate time to alter the SQL database dynamically.")
    
    if st.button("Advance 15 Mins (Normal)"):
        advance_time(scenario="normal")
        st.rerun()
        
    if st.button("Trigger Fleet Arrival (Spike)"):
        advance_time(scenario="fleet_arrival")
        st.rerun()
        
    if st.button("Trigger Cooldown"):
        advance_time(scenario="cooldown")
        st.rerun()
        
    st.divider()
    
    # 2. DATABASE RESET BUTTON
    if st.button("Reset Database & Chat", type="primary"):
        reset_db()
        st.session_state.chat_history = [] # Clear agent memory
        st.rerun()

# --- MAIN LAYOUT: DUAL PANE ---
col1, col2 = st.columns([1, 1], gap="large")

# PANE 1: Live Database View
with col1:
    st.subheader("Transformer Temperature Trend")
    conn = sqlite3.connect(DB_PATH)
    
    # 3. THE TEMPERATURE CHART
    # Fetch all chronological data so the chart draws left-to-right correctly
    df_chart = pd.read_sql("SELECT timestamp, transformer_temp_c FROM substation_telemetry ORDER BY timestamp ASC", conn)
    if not df_chart.empty:
        df_chart.set_index('timestamp', inplace=True)
        st.line_chart(df_chart, y="transformer_temp_c", color="#ff4b4b")
    
    st.subheader("Live Substation Telemetry (Last 10 Ticks)")
    df_telemetry = pd.read_sql("SELECT * FROM substation_telemetry ORDER BY timestamp DESC LIMIT 10", conn)
    # Fixed the terminal warning by replacing use_container_width with width="stretch"
    st.dataframe(df_telemetry, width="stretch")
    
    st.subheader("Charger Status")
    df_chargers = pd.read_sql("SELECT * FROM chargers", conn)
    st.dataframe(df_chargers, width="stretch")
    
    conn.close()

# PANE 2: The Agent Chat
with col2:
    st.subheader("ReAct Investigator")
    
    # 1. Create a fixed-height, scrollable container for the chat history
    chat_container = st.container(border=False)
    
    # 2. Render all past messages inside the container
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                if msg["role"] == "assistant" and "trace" in msg:
                    with st.expander("View DSPy SQL Trace"):
                        for idx, (q, obs) in enumerate(zip(msg["trace"]["queries"], msg["trace"]["observations"]), 1):
                            st.code(f"-- Step {idx}\n{q}", language="sql")
                            st.caption(f"Observation: {obs}")

    # 3. The input box automatically anchors to the bottom of the column
    if user_input := st.chat_input("Ask about the grid conditions..."):
        
        # Immediately append and display the user's message inside the container
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Run the agent and display the response inside the container
            with st.chat_message("assistant"):
                with st.spinner("Compiling SQL and analyzing physics..."):
                    result = run_agent(user_input)
                    st.markdown(result["executive_brief"])
                    
                    with st.expander("View DSPy SQL Trace"):
                        for idx, (q, obs) in enumerate(zip(result["executed_queries"], result["db_observations"]), 1):
                            st.code(f"-- Step {idx}\n{q}", language="sql")
                            st.caption(f"Observation: {obs}")
        
        # Save the assistant's response to memory so it persists on reload
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": result["executive_brief"],
            "trace": {
                "queries": result["executed_queries"], 
                "observations": result["db_observations"]
            }
        })