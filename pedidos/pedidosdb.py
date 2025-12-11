import sqlite3
conn = sqlite3.connect("pedidos.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
id_cliente INTEGER NOT NULL,
id_producto INTEGER NOT NULL,
cantidad INTEGER NOT NULL,
estado TEXT NOT NULL DEFAULT 'pendiente',
created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
conn.commit()
conn.close()