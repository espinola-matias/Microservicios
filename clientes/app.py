from flask import Flask, jsonify, request
from autorizacion import crear_token, verificar_token
import sqlite3
from dotenv import load_dotenv
import os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "clientes.db")
load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def conexion_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/admin/login", methods= ["POST"])
def admin_login():
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Los datos enviados estan incompletos"})
    
    if data["email"] == ADMIN_EMAIL and data["password"] == ADMIN_PASSWORD:
        token = crear_token(
            usuario_id = "admin",
            scopes = ["clientes:read", "clientes:create", "clientes:update", "clientes:delete"],
            is_service = True
        )
        return jsonify({"message": "Login exitoso", "token": token}), 200
    else:
        return jsonify({"error": "Datos invalidos"}), 401
    
def verificar_admin(f):
    def wrapper(*args, **kwargs):
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
    wrapper.__name__ = f.__name__
    return wrapper

@app.route("/clientes", methods=["GET"])
@verificar_admin
def lista_clientes():
    conn = conexion_db()
    get_clientes = conn.execute("SELECT * FROM clientes").fetchall()
    conn.close()
    return jsonify([dict(cliente) for cliente in get_clientes])

@app.route("/clientes/<int:cedula>", methods=["GET"])
@verificar_admin
def obtener_cliente(cedula):
    conn = conexion_db()
    cliente = conn.execute("SELECT * FROM clientes WHERE cedula=?", (cedula,)).fetchone()
    conn.close()
    
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404
    
    return jsonify(dict(cliente)), 200


@app.route("/clientes", methods= ["POST"])
@verificar_admin
def crear_clientes():
    data = request.json
    conn = conexion_db()
    cursor = conn.cursor()
    cursor.execute(
    "INSERT INTO clientes (nombre, email, cedula, telefono) VALUES (?, ?, ?, ?)", 
    (data["nombre"], data["email"], data["cedula"], data["telefono"])
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return jsonify({"message": "Cliente registrado", "id": nuevo_id}), 201

@app.route("/clientes/<int:cedula>", methods= ["PUT"])
@verificar_admin
def actualizar_cliente(cedula):
    data = request.json
    conn = conexion_db()
    cursor = conn.execute(
        "UPDATE clientes SET nombre=?, email=?, telefono=? WHERE cedula=?",
        (data["nombre"], data["email"], data["telefono"], cedula)
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Cliente no encontrado"}), 404
    
    conn.close()
    return jsonify({"message": "Datos del cliente actualizado"}), 200

@app.route("/clientes/<int:cedula>", methods= ["DELETE"])
@verificar_admin
def eliminar_cliente(cedula):
    conn = conexion_db()
    cursor = conn.execute("DELETE from clientes WHERE cedula=?", (cedula,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Cliente no encontrado"}), 404
    conn.close()
    return jsonify({"message": "Cliente eliminado"})

if __name__ == "__main__":
    app.run(port=5002, debug= True)