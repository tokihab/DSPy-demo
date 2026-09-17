import sqlite3
import re
import dspy
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from simulate import DB_PATH

# 1. The Interceptor Array
action_log = []

def execute_sql(query: str) -> str:
    clean_query = re.sub(r"```sql|```", "", query).strip()
    if not clean_query.upper().startswith("SELECT"):
        obs = "Error: Read-only access."
        action_log.append({"query": clean_query, "observation": obs})
        return obs

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(clean_query)
        rows = cursor.fetchmany(15)
        conn.close()
        obs = str(rows) if rows else "Empty result set."
    except Exception as e:
        obs = f"DB Error: {str(e)}"
        
    action_log.append({"query": clean_query, "observation": obs})
    return obs

# 2. DSPy Signatures
class IndustrialSQLAgent(dspy.Signature):
    question: str = dspy.InputField()
    schema_context: str = dspy.InputField()
    answer: str = dspy.OutputField()

class ExecutiveSynthesizer(dspy.Signature):
    user_question: str = dspy.InputField()
    executed_queries: str = dspy.InputField()
    db_observations: str = dspy.InputField()
    executive_brief: str = dspy.OutputField()

# 3. LangGraph Construction
class AgentGraphState(TypedDict):
    question: str
    executed_queries: List[str]
    db_observations: List[str]
    executive_brief: str

def react_node(state: AgentGraphState):
    global action_log
    action_log.clear() # Reset log for new query
    
    schema = "Tables: 1. chargers(charger_id, max_kw, status) | 2. charging_sessions(session_id, charger_id, start_time, end_time, peak_kw) | 3. substation_telemetry(timestamp, total_load_kw, transformer_temp_c, grid_penalty_active)"
    
    agent = dspy.ReAct(IndustrialSQLAgent, tools=[execute_sql], max_iters=4)
    
    try:
        # If you run optimize.py later, this will load your trained Egyptian dialect model
        agent.load("egyptian_grid_agent.json")
    except Exception:
        pass
        
    agent(question=state["question"], schema_context=schema)
    
    return {
        "executed_queries": [log["query"] for log in action_log],
        "db_observations": [log["observation"] for log in action_log]
    }

def synthesis_node(state: AgentGraphState):
    synthesizer = dspy.Predict(ExecutiveSynthesizer)
    result = synthesizer(
        user_question=state["question"],
        executed_queries="\n".join(state["executed_queries"]),
        db_observations="\n".join(state["db_observations"])
    )
    return {"executive_brief": result.executive_brief}

workflow = StateGraph(AgentGraphState)
workflow.add_node("react", react_node)
workflow.add_node("synthesis", synthesis_node)
workflow.set_entry_point("react")
workflow.add_edge("react", "synthesis")
workflow.add_edge("synthesis", END)
app = workflow.compile()

def run_agent(question: str) -> dict:
    return app.invoke({"question": question, "executed_queries": [], "db_observations": [], "executive_brief": ""})