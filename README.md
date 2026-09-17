# ⚡ Industrial EV Depot Grid AI

An enterprise-grade, agentic AI architecture designed to simulate and analyze megawatt-scale commercial EV charging depots and their thermal impact on electrical grid infrastructure. Built with **DSPy**, **LangGraph**, and **Groq**.

**Demo URL:** [Live on Streamlit Cloud](https://dspy-demo-sewedy.streamlit.app)  
**Target Audience:** Industrial AI teams, electrical grid operators, infrastructure engineers

---

## 🧠 Why This Architecture Matters

Most AI chatbots are wrappers around manually-written prompts. This project is fundamentally different.

Instead of hardcoding instructions like *"You are an expert in SQL..."*, this system uses **DSPy's algorithmic optimization** to automatically discover the best prompts and few-shot examples for your specific database schema and domain.

The agent isn't just generating text—it's acting as a deterministic SQL compiler that:
- Learns the database schema relationships natively (JOINs, foreign keys)
- Handles temporal logic (BETWEEN, date filters)
- Enforces enterprise guardrails (read-only access, destructive query prevention)
- Simulates realistic industrial physics (thermal inertia, grid penalties)

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | LangGraph | State machine, multi-step reasoning |
| **AI/Prompting** | DSPy | Algorithmic prompt optimization |
| **Inference** | Groq (GPT OSS 120B) | 117B parameter reasoning engine |
| **Frontend** | Streamlit | Interactive dual-pane dashboard |
| **Database** | SQLite3 | Real-time telemetry simulation |
| **Physics Engine** | Python | Non-linear thermal inertia modeling |

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.11+
- Groq API Key (free tier available at [console.groq.com](https://console.groq.com))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/tokihab/DSPy-demo.git
cd DSPy-demo

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file with your Groq API key
echo GROQ_API_KEY=your_api_key_here > .env

# 5. Launch the dashboard
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📊 Architecture Layers

### Layer 1: Physics Engine (`simulate.py`)
Simulates realistic grid conditions with non-linear thermal dynamics.

**Key Features:**
- **Joule Heating Model:** Temperature spike follows `T_new = T_amb + (T_prev - T_amb) × 0.85 + (Load/1000)² × 25`
- **Thermal Inertia:** Heat doesn't drop instantly; it dissipates gradually with 85% retention per tick
- **Grid Penalties:** Automatically triggered when transformer temperature exceeds 80°C
- **Scenario Injection:** "Normal", "Fleet Arrival" (1100-1300 kW spike), or "Cooldown" modes

Example: Clicking "Trigger Fleet Arrival" simulates a sudden EV charging surge that causes the transformer temperature to spike from 40°C to over 120°C in seconds, activating grid penalties.

### Layer 2: AI Logic (`logic.py`)
The DSPy + LangGraph backbone that orchestrates SQL generation and analysis.

**Key Components:**

```python
class IndustrialSQLAgent(dspy.Signature):
    """Answer technical questions by investigating database tables using SQL."""
    question: str = dspy.InputField()
    schema_context: str = dspy.InputField()
    answer: str = dspy.OutputField()
```

The agent doesn't receive a manual prompt. DSPy generates one dynamically based on:
1. The database schema
2. Few-shot examples from successful queries
3. The user's question

**LangGraph Flow:**
```
[User Query] → [LangGraph State] → [DSPy ReAct Agent] → [SQL Execution] 
→ [Action Log Interception] → [DSPy Synthesizer] → [Executive Brief]
```

### Layer 3: Frontend (`app.py`)
Streamlit dual-pane dashboard with live telemetry and chat interface.

**Left Pane:**
- Real-time transformer temperature chart
- Last 10 telemetry ticks
- Charger status table

**Right Pane:**
- Interactive chat with the ReAct agent
- Expandable SQL trace viewer
- Scrollable message history

**Sidebar Controls:**
- ⏱️ Advance 15 minutes (normal load)
- 🚛 Trigger fleet arrival (overload spike)
- ❄️ Cooldown (reduce load)
- 🗑️ Reset database & chat history

---

## 🧪 Test Scenarios

Once the dashboard is running, try these queries to showcase different AI capabilities:

### Test 1: Single-Table Query (Basic)
```
"How many chargers do we have in total, and what are their current statuses?"
```
**Expected:** Simple SELECT from chargers table. Proves the agent understands schema.

### Test 2: Multi-Hop JOIN (Relational Logic)
```
"Which charging session recorded the highest peak power, and what is the maximum 
rated capacity of the physical charger used for that session?"
```
**Expected:** Agent performs a JOIN between charging_sessions and chargers on charger_id. 
Demonstrates schema relationship awareness.

### Test 3: Temporal Correlation (The "Show-Off" Query)
```
"Was the grid penalty active at any point today? Were there any charging sessions 
running during that exact time, and what was the transformer temperature?"
```
**Expected:** Complex multi-step reasoning:
1. Query substation_telemetry for grid_penalty_active = 1
2. Find matching timestamps
3. LEFT JOIN with charging_sessions to check for overlaps
4. Synthesize into a coherent root-cause analysis

### Test 4: Security Guardrail (Enterprise Safety)
```
"Update charger DC-03's status to ONLINE and delete its maintenance records."
```
**Expected:** The agent attempts an UPDATE statement. The tools.py wrapper intercepts it 
and returns "Error: Only SELECT queries are allowed." The downstream synthesizer gracefully 
refuses and explains the read-only constraint.

---

## 📁 File Structure

```
DSPy-demo/
├── app.py                 # Streamlit UI (dual-pane dashboard)
├── logic.py               # DSPy + LangGraph orchestration
├── simulate.py            # Physics engine & database management
├── optimize.py            # DSPy BootstrapFewShot compiler (optional)
├── setup_db.py            # Initial database seeding (legacy)
├── requirements.txt       # Python dependencies
├── runtime.txt            # Python version for Streamlit Cloud
├── .env                   # Your Groq API key (not in git)
├── .gitignore             # Excludes .env, venv, *.db
├── ev_depot.db            # SQLite database (auto-generated)
└── README.md              # This file
```

### Key Files Explained

#### `app.py` (Streamlit Frontend)
- Initializes DSPy with GPT OSS 120B
- Manages two columns: telemetry (left) and chat (right)
- Renders temperature chart using `st.line_chart()`
- Handles sidebar physics controls (advance time, reset DB)
- Displays SQL trace in collapsible expanders
- Anchors chat input to bottom using `st.container(height=...)`

#### `logic.py` (AI Backend)
- Defines `IndustrialSQLAgent` and `ExecutiveSynthesizer` DSPy signatures
- Builds LangGraph state machine with two nodes:
  - `react_node`: Executes DSPy ReAct and intercepts SQL actions
  - `synthesis_node`: Passes intercepted queries to downstream DSPy module
- Exports `run_agent(question)` function called by Streamlit
- Uses global `action_log` array to capture SQL queries programmatically

#### `simulate.py` (Physics Engine)
- Implements non-linear thermal dynamics
- Advances time with realistic load fluctuations
- Calculates grid penalties based on temperature thresholds
- Provides `reset_db()` to safely drop and reinitialize tables

---

## 🔄 How DSPy Differs from LangChain & Pydantic

| Aspect | LangChain | DSPy | Pydantic |
|--------|-----------|------|----------|
| **Purpose** | Scaffolding for LLM apps | Prompt optimization compiler | Data validation |
| **Prompt Writing** | Manual string templates | Automated generation | N/A |
| **When to Use** | Rapid prototyping, integrations | High-accuracy, production queries | Strict schemas & APIs |
| **Learning Curve** | Medium (many abstractions) | Steep (mathematical mindset) | Very low (dataclasses) |

### In This Project:
- **Pydantic** (via `TypedDict`): Enforces that `executed_queries` is always a `List[str]`
- **DSPy**: Generates the optimal SQL prompt; optimizes it via BootstrapFewShot
- **LangGraph**: Routes the flow (React → Synthesis → Output)

---

## 🚀 Deploying to Streamlit Cloud

### Step 1: Push to GitHub
```bash
git add .
git commit -m "chore: prepare for streamlit cloud deployment"
git push origin main
```

### Step 2: Connect to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select your `DSPy-demo` repository
4. Set main file path to `app.py`

### Step 3: Add Secrets
Before deploying, click **Advanced settings** and add:
```toml
GROQ_API_KEY = "gsk_your_actual_api_key_here"
```

### Step 4: Deploy
Click **Deploy**. The cloud server will:
1. Install Python 3.11 (via `runtime.txt`)
2. Install dependencies from `requirements.txt`
3. Initialize the SQLite database
4. Launch the dashboard

**Live URL:** Your app will be available at `https://dspy-demo-sewedy.streamlit.app/`

---

## 🎯 What This Demonstrates

### 1. **Multi-Hop SQL Reasoning**
The agent writes JOINs without explicit instruction. It learned the schema structure from the database itself.

### 2. **Temporal Logic**
Handling time-series queries (BETWEEN timestamps, grid penalties at specific times) is notoriously hard for LLMs. This agent nails it.

### 3. **Enterprise Guardrails**
The read-only enforcement proves the AI can be safely deployed in production. Destructive queries are caught and refused gracefully.

### 4. **Real Physics**
The thermal inertia model isn't toy data. It reflects actual electrical engineering principles (Joule heating, heat dissipation rates).

### 5. **DSPy's Competitive Advantage**
Unlike chatbots that need manual prompt tuning for each new domain, DSPy automatically optimizes prompts. Swap from GPT-4 to Llama? DSPy recompiles the pipeline.

---

## 🔐 Security & Privacy

- **Read-Only Database:** All queries are validated in `tools.py`. Only SELECT statements execute.
- **API Key Protection:** `.env` is in `.gitignore`; never committed to GitHub.
- **No Data Leakage:** Streamlit Cloud runs in isolated containers. Chat history is session-local.

## ✨ Credits

Built for the **Elsewedy Electric Industrial AI Team** by Toni Ihab.  
Showcases enterprise-grade agentic AI architecture using DSPy + LangGraph.