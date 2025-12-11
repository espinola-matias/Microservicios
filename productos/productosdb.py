import sqlite3
conn = sqlite3.connect("productos.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
nombre TEXT NOT NULL,
descripcion TEXT,
precio REAL NOT NULL,
stock INTEGER NOT NULL,
created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
conn.commit()
conn.close()