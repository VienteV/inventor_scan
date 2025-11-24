import sqlite3

con = sqlite3.connect("assemly.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS assembly_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partNumber TEXT  UNIQUE,
    name TEXT,
    amount INTEGER,
    drawing_link TEXT DEFAULT NULL,
    file_link TEXT DEFAULT NULL,
    parent_id INTEGER DEFAULT NULL,  
    Drawing INTEGER DEFAULT 0,
    Checked INTEGER DEFAULT 0,
    
    FOREIGN KEY (parent_id) REFERENCES assembly_details(id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS assembly_standards(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    standart_name TEXT,
    amount INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS assembly_others(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    amount INTEGER
)
""")