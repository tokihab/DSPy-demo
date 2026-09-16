from typing import TypedDict, List
from langgraph.graph import StateGraph, END
import dspy
from tools import execute_sql, get_and_clear_action_log

# 1. DSPy Signatures
class IndustrialSQLAgent(dspy.Signature):
    """Answer technical questions by investigating database tables using read-only SQL queries."""
    question: str = dspy.InputField(desc="The user inquiry about EV charging telemetry")
    schema_context: str = dspy.InputField(desc="Database table definitions")
    answer: str = dspy.OutputField(desc="Final conclusive response based on SQL findings")

class ExecutiveSynthesizer(dspy.Signature):
    """Review the executed SQL queries and database observations to write an executive brief."""
    user_question: str = dspy.InputField()
    executed_queries: str = dspy.InputField(desc="Raw SQL queries run by the ReAct agent")
    db_observations: str = dspy.InputField(desc="Raw results returned from the database")
    executive_brief: str = dspy.OutputField(desc="A professional engineering summary of the findings")

# 2. LangGraph State & Nodes
class AgentGraphState(TypedDict):
    question: str
    schema_context: str
    executed_queries: List[str]
    db_observations: List[str]
    agent_answer: str
    executive_brief: str

def react_sql_node(state: AgentGraphState):
    """Runs dspy.ReAct and extracts the actions via the tool wrapper."""
    agent = dspy.ReAct(IndustrialSQLAgent, tools=[execute_sql], max_iters=5)
    result = agent(question=state["question"], schema_context=state["schema_context"])
    
    # Extract trace programmatically
    logs = get_and_clear_action_log()
    
    return {
        "agent_answer": result.answer,
        "executed_queries": [log["query"] for log in logs],
        "db_observations": [log["observation"] for log in logs]
    }

def synthesis_node(state: AgentGraphState):
    """Consumes the extracted trace arrays and generates a final brief."""
    synthesizer = dspy.Predict(ExecutiveSynthesizer)
    
    # Format arrays into strings for DSPy processing
    queries_str = "\n".join(state.get("executed_queries", []))
    obs_str = "\n".join(state.get("db_observations", []))
    
    result = synthesizer(
        user_question=state["question"],
        executed_queries=queries_str,
        db_observations=obs_str
    )
    
    return {"executive_brief": result.executive_brief}

# 3. Graph Assembly
workflow = StateGraph(AgentGraphState)
workflow.add_node("react_agent", react_sql_node)
workflow.add_node("synthesis", synthesis_node)

workflow.set_entry_point("react_agent")
workflow.add_edge("react_agent", "synthesis")
workflow.add_edge("synthesis", END)

app = workflow.compile()