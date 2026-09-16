import sqlite3
import re

# Global array to hold the intercepted trace
action_log = []

def execute_sql(query: str) -> str:
    """Executes a read-only SQL SELECT query against the EV Depot database."""
    # Clean formatting hallucinations from the LLM
    clean_query = re.sub(r"```sql|```", "", query).strip()
    
    # Security: Read-only guardrail
    if not clean_query.upper().startswith("SELECT"):
        obs = "Error: Only SELECT queries are allowed."
        action_log.append({"query": clean_query, "observation": obs})
        return obs

    try:
        conn = sqlite3.connect("ev_depot.db")
        cursor = conn.cursor()
        cursor.execute(clean_query)
        rows = cursor.fetchmany(15)
        conn.close()
        obs = str(rows) if rows else "Query executed successfully: Empty result set."
    except Exception as e:
        obs = f"Database Error: {str(e)}"
        
    # Programmatically log the action and observation
    action_log.append({"query": clean_query, "observation": obs})
    return obs

def get_and_clear_action_log():
    """Retrieves the recorded tool executions and resets the log for the next run."""
    global action_log
    logs = action_log.copy()
    action_log.clear()
    return logs