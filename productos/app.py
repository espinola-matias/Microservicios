from flask import Flask, jsonify, request
from autorizacion import verificar_token
import sqlite3
from dotenv import load_dotenv
import os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "productos.db")
load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def conexion_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
    
def verificar_admin(f):
    def warpper(*args, **kwargs):
        token_header = request.headers.get("Authorization")
        if not token_header or not token_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401
        
        token = token_header.split(" ")[1]
        validacion = verificar_token(token)
        if "error" in validacion:
            return jsonify(validacion), 403
        
        if validacion.get("usuario_id") != "admin":
            return jsonify({"error": "Usuario no autorizado"}), 403
        
        return f(*args, **kwargs)
    warpper.__name__ = f.__name__
    return warpper

@app.route("/productos", methods=["GET"])
@verificar_admin
def listar_productos():
    conn = conexion_db()
    get_productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return jsonify([dict(producto) for producto in get_productos])

@app.route("/productos/<int:id_producto>", methods=["GET"])
@verificar_admin
def obtener_producto(id_producto):
    conn = conexion_db()
    producto = conn.execute("SELECT * FROM productos WHERE id_producto=?", (id_producto,)).fetchone()
    conn.close()
    
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    
    return jsonify(dict(producto)), 200

@app.route("/productos", methods= ["POST"])
@verificar_admin
def cargar_productos():
    data = request.json
    conn = conexion_db()
    cursor = conn.cursor()
    cursor.execute(
    "INSERT INTO productos (nombre, descripcion, precio, stock) VALUES (?, ?, ?, ?)", 
    (data["nombre"], data["descripcion"], data["precio"], data["stock"])
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return jsonify({"message": "Producto registrado con exito", "id_producto": nuevo_id}), 201

@app.route("/productos/<int:id_producto>", methods= ["PUT"])
@verificar_admin
def actualizar_producto(id_producto):
    data = request.json
    conn = conexion_db()
    cursor = conn.execute(
        "UPDATE productos SET nombre=?, descripcion=?, precio=?, stock=? WHERE id_producto=?",
        (data["nombre"], data["descripcion"], data["precio"], data["stock"], id_producto)
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Producto no encontrado"}), 404
    
    conn.close()
    return jsonify({"message": "Producto actualizado"}), 200

@app.route("/productos/<int:id_producto>", methods= ["DELETE"])
@verificar_admin
def eliminar_producto(id_producto):
    conn = conexion_db()
    cursor = conn.execute("DELETE from productos WHERE id_producto=?", (id_producto,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Producto no encontrado"}), 404
    conn.close()
    return jsonify({"message": "Producto eliminado"}), 200

if __name__ == "__main__":
    app.run(port=5003, debug= True)