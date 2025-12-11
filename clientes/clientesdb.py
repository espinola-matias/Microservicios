import sqlite3
conn = sqlite3.connect("clientes.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
nombre TEXT NOT NULL,
email TEXT UNIQUE NOT NULL,
cedula INTEGER UNIQUE NOT NULL,
telefono INTEGER,
created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
conn.commit()
conn.close()