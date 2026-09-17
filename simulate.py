import sqlite3
import datetime
import random

DB_PATH = "ev_depot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chargers (charger_id TEXT PRIMARY KEY, max_kw INTEGER, status TEXT)
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS charging_sessions (session_id TEXT PRIMARY KEY, charger_id TEXT, start_time TEXT, end_time TEXT, peak_kw REAL)
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS substation_telemetry (timestamp TEXT, total_load_kw REAL, transformer_temp_c REAL, grid_penalty_active INTEGER)
    """)
    
    # Seed if empty
    cursor.execute("SELECT COUNT(*) FROM chargers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO chargers VALUES (?, ?, ?)", [("DC-01", 350, "ONLINE"), ("DC-02", 350, "ONLINE")])
        cursor.execute("INSERT INTO substation_telemetry VALUES (?, ?, ?, ?)", ("2026-09-14 12:00:00", 250.0, 40.0, 0))
    
    conn.commit()
    conn.close()

def calculate_thermal_inertia(prev_temp: float, new_load_kw: float) -> float:
    """
    Non-linear heating physics: T_new = T_amb + (T_prev - T_amb)*0.85 + (Load/1000)^2 * 25
    """
    t_ambient = 35.0
    retention_factor = 0.85
    load_ratio = new_load_kw / 1000.0 
    heat_generated = (load_ratio ** 2) * 25.0 
    
    return round(t_ambient + (prev_temp - t_ambient) * retention_factor + heat_generated, 2)

def advance_time(scenario="normal"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT timestamp, total_load_kw, transformer_temp_c FROM substation_telemetry ORDER BY timestamp DESC LIMIT 1")
    last_time_str, last_load, last_temp = cursor.fetchone()
    last_time = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
    new_time = last_time + datetime.timedelta(minutes=15)
    
    # Scenario injection
    if scenario == "fleet_arrival":
        new_load = random.uniform(1100.0, 1300.0) # Overload (Max is 1000)
    elif scenario == "cooldown":
        new_load = random.uniform(100.0, 200.0)
    else:
        new_load = max(50.0, last_load + random.uniform(-100.0, 100.0))
        
    new_temp = calculate_thermal_inertia(last_temp, new_load)
    penalty = 1 if new_temp >= 80.0 else 0
    
    cursor.execute("INSERT INTO substation_telemetry VALUES (?, ?, ?, ?)", 
                   (new_time.strftime("%Y-%m-%d %H:%M:%S"), round(new_load, 2), new_temp, penalty))
    
    conn.commit()
    conn.close()

def reset_db():
    """Drops all tables and re-initializes the database from scratch."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS chargers")
    cursor.execute("DROP TABLE IF EXISTS charging_sessions")
    cursor.execute("DROP TABLE IF EXISTS substation_telemetry")
    conn.commit()
    conn.close()
    
    # Re-seed the clean database
    init_db()