import sqlite3

con = sqlite3.connect("assemly.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS assembly_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partNumber TEXT UNIQUE,
    name TEXT,
    amount INTEGER,
    drawing_link TEXT DEFAULT NULL,
    file_link TEXT DEFAULT NULL,
    Drawing INTEGER DEFAULT 0,
    Checked INTEGER DEFAULT 0,
    Is_borrowed INTEGER DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS assembly_structure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL,  -- ID сборки
    child_id INTEGER NOT NULL,   -- ID детали в этой сборке
    quantity INTEGER DEFAULT 0,  -- Количество деталей в сборке
    UNIQUE(parent_id, child_id), -- Уникальная связь
    FOREIGN KEY (parent_id) REFERENCES assembly_details(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES assembly_details(id) ON DELETE CASCADE
);""")

cur.execute("""CREATE INDEX IF NOT EXISTS idx_parent_id ON assembly_structure(parent_id);""")
cur.execute("""CREATE INDEX IF NOT EXISTS idx_child_id ON assembly_structure(child_id);
""")
