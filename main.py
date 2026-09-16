import os
import dspy
from graph import app

def main():
    lm = dspy.LM(
        model='openai/llama-3.3-70b-versatile',
        api_key=os.environ.get("GROQ_API_KEY")
    )
    dspy.configure(lm=lm)
    
    schema_context = """
    Tables:
    1. chargers (charger_id, max_kw, status)
    2. charging_sessions (session_id, charger_id, start_time, end_time, peak_kw)
    3. substation_telemetry (timestamp, total_load_kw, transformer_temp_c, grid_penalty_active)
    """
    
    print("\n" + "="*50)
    print("🔌 EV Depot Grid AI - Interactive Console")
    print("Type 'exit' or 'quit' to close.")
    print("="*50 + "\n")
    
    # 2. THE INTERACTIVE LOOP
    while True:
        user_input = input("\n👤 Ask the Agent > ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
            
        if not user_input.strip():
            continue
            
        print("\nAgent is thinking and querying the database...")
        
        # Reset state for each new question
        initial_state = {
            "question": user_input,
            "schema_context": schema_context,
            "executed_queries": [],
            "db_observations": [],
            "agent_answer": "",
            "executive_brief": ""
        }
        
        # Execute the Graph
        try:
            result = app.invoke(initial_state)
            
            print("\n" + "="*50)
            print("SQL ACTIONS EXECUTED")
            print("="*50)
            for idx, (q, obs) in enumerate(zip(result["executed_queries"], result["db_observations"]), 1):
                print(f"\n[Step {idx}]")
                print(f"SQL Sent: {q}")
                print(f"DB Returned: {obs}")
            
            print("\n" + "="*50)
            print("EXECUTIVE BRIEF")
            print("="*50)
            print(result["executive_brief"])
            
        except Exception as e:
            print(f"\n❌ Error processing request: {e}")

if __name__ == "__main__":
    main()