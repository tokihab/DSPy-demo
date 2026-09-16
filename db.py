import sqlite3

def create_database():
    conn = sqlite3.connect("ev_depot.db")
    cursor = conn.cursor()

    # 1. Chargers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chargers (
        charger_id TEXT PRIMARY KEY,
        max_kw INTEGER,
        status TEXT
    )
    """)

    # 2. Charging Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS charging_sessions (
        session_id TEXT PRIMARY KEY,
        charger_id TEXT,
        start_time TEXT,
        end_time TEXT,
        peak_kw REAL,
        FOREIGN KEY(charger_id) REFERENCES chargers(charger_id)
    )
    """)

    # 3. Substation Telemetry Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS substation_telemetry (
        timestamp TEXT,
        total_load_kw REAL,
        transformer_temp_c REAL,
        grid_penalty_active INTEGER
    )
    """)

    # Insert Dummy Data
    cursor.executemany("INSERT OR IGNORE INTO chargers VALUES (?, ?, ?)", [
        ("DC-01", 350, "ONLINE"),
        ("DC-02", 350, "ONLINE"),
        ("DC-03", 150, "MAINTENANCE")
    ])
    
    cursor.executemany("INSERT OR IGNORE INTO charging_sessions VALUES (?, ?, ?, ?, ?)", [
        ("S-101", "DC-01", "2026-09-14 14:00:00", "2026-09-14 14:45:00", 310.5),
        ("S-102", "DC-02", "2026-09-14 14:15:00", "2026-09-14 15:00:00", 340.2)
    ])
    
    cursor.executemany("INSERT OR IGNORE INTO substation_telemetry VALUES (?, ?, ?, ?)", [
        ("2026-09-14 14:00:00", 850.0, 75.5, 0),
        ("2026-09-14 14:30:00", 1150.0, 82.1, 1),
        ("2026-09-14 15:00:00", 600.0, 70.0, 0)
    ])

    conn.commit()
    conn.close()
    print("Database 'ev_depot.db' created and seeded successfully.")

if __name__ == "__main__":
    create_database()