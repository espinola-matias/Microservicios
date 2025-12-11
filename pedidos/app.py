from flask import Flask, jsonify, request
from autorizacion import verificar_token
import sqlite3
import os
import requests
from dotenv import load_dotenv

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "pedidos.db")
load_dotenv()

ADMIN_EMAIL =os.getenv("ADMIN_EMAIL")
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
        if "error" in validacion or validacion.get("usuario_id") != "admin":
            return jsonify({"error": "Autorizacion denegada"}), 403
        return f(*args, **kwargs)
    warpper.__name__ = f.__name__
    return warpper

@app.route("/pedidos", methods=["GET"])
@verificar_admin
def listar_pedidos():
    conn = conexion_db()
    pedidos = conn.execute("SELECT * FROM pedidos").fetchall()
    conn.close()

    headers = {"Authorization": request.headers.get("Authorization")}
    pedidos_detallados = []

    for pedido in pedidos:
        pedido_dict = dict(pedido)

        respuesta_cliente = requests.get(f"http://127.0.0.1:5002/clientes/{pedido_dict['id_cliente']}",
            headers=headers)
        
        if respuesta_cliente.status_code == 200:
            pedido_dict["cliente"] = respuesta_cliente.json()
        else:
            pedido_dict["cliente"] = {"error": "No se pudo obtener cliente"}

        respuesta_producto = requests.get(
            f"http://127.0.0.1:5003/productos/{pedido_dict['id_producto']}",
            headers=headers)
        
        if respuesta_producto.status_code == 200:
            pedido_dict["producto"] = respuesta_producto.json()
        else:
            pedido_dict["producto"] = {"error": "No se pudo obtener producto"}

        pedidos_detallados.append(pedido_dict)

    return jsonify(pedidos_detallados), 200

@app.route("/pedidos/<int:id_pedido>", methods=["GET"])
@verificar_admin
def obtener_pedido(id_pedido):
    conn = conexion_db()
    pedido = conn.execute("SELECT * FROM pedidos WHERE id_pedido=?", (id_pedido,)).fetchone()
    conn.close()

    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404

    pedido_dict = dict(pedido)
    headers = {"Authorization": request.headers.get("Authorization")}

    respuesta_cliente = requests.get(
        f"http://127.0.0.1:5002/clientes/{pedido_dict['id_cliente']}",
        headers=headers)
    if respuesta_cliente.status_code == 200:
        pedido_dict["cliente"] = respuesta_cliente.json()
    else:
        pedido_dict["cliente"] = {"error": "No se pudo obtener cliente"}

    respuesta_producto = requests.get(
        f"http://127.0.0.1:5003/productos/{pedido_dict['id_producto']}",
        headers=headers)
    if respuesta_producto.status_code == 200:
        pedido_dict["producto"] = respuesta_producto.json()
    else:
        pedido_dict["producto"] = {"error": "No se pudo obtener producto"}

    return jsonify(pedido_dict), 200

@app.route("/pedidos", methods=["POST"])
@verificar_admin
def crear_pedido():
    data = request.json
    id_cliente = data.get("id_cliente")
    id_producto = data.get("id_producto")
    cantidad = data.get("cantidad")

    if not id_cliente or not id_producto or not cantidad:
        return jsonify ({"error": "Faltan datos"}), 400
    
    if cantidad <= 0:
        return jsonify({"error": "Cantidad debe ser mayor a cero"}), 400

    
    token_header = request.headers.get("Authorization")
    headers = {"Authorization": token_header}

    cliente = requests.get(f"http://127.0.0.1:5002/clientes/{id_cliente}", headers= headers)
    if cliente.status_code != 200:
        return jsonify({"error": "El cliente no existe"}), 400
    
    producto = requests.get(f"http://127.0.0.1:5003/productos/{id_producto}", headers= headers)
    if producto.status_code != 200:
        return jsonify({"error": "El producto no existe"}), 400
    
    producto_data = producto.json()
    if producto_data["stock"] < cantidad:
        return jsonify({"error": "Stock insuficiente"}), 400

    conn = conexion_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pedidos (id_cliente, id_producto, cantidad, estado) VALUES (?, ?, ?, ?)",
        (data["id_cliente"], data["id_producto"], data["cantidad"], data.get("estado", "pendiente"))
    )
    conn.commit()
    pedido_id = cursor.lastrowid
    conn.close()
    return jsonify({"message": "Pedido creado", "id_pedido": pedido_id}), 201


@app.route("/pedidos/<int:id_pedido>", methods=["PUT"])
@verificar_admin
def actualizar_pedido(id_pedido):
    data = request.json
    nuevo_estado = data.get("estado")

    if nuevo_estado not in ["pendiente", "aprobado", "rechazado"]:
        return jsonify({"error": "Estado invalido"}), 400
    
    conn = conexion_db()
    pedido = conn.execute("SELECT * FROM pedidos WHERE id_pedido=?", (id_pedido,)).fetchone()

    if not pedido:
        conn.close()
        return jsonify({"error": "Pedido no encontrado"}), 404
    
    if nuevo_estado == "aprobado":
        id_producto = pedido["id_producto"]
        cantidad = pedido["cantidad"]

        headers = {"Authorization": request.headers.get("Authorization")}

        respuesta = requests.get(f"http://127.0.0.1:5003/productos/{id_producto}", headers=headers)
        if respuesta.status_code != 200:
            conn.close()
            return jsonify({"error": "Producto no encontrado"}), 400
        
        producto = respuesta.json()
        if producto["stock"] < cantidad:
            conn.execute("UPDATE pedidos SET estado=? WHERE id_pedido=?", ("rechazado", id_pedido))
            conn.commit()
            conn.close()
            return jsonify({"error": "Stock insuficiente, pedido rechazado automaticamente"}), 400
        
        nuevo_stock = producto["stock"] - cantidad
        actualizar = requests.put(f"http://127.0.0.1:5003/productos/{id_producto}",
            headers=headers,
            json={
                "nombre": producto["nombre"],
                "descripcion": producto["descripcion"],
                "precio": producto["precio"],
                "stock": nuevo_stock
            }
        )

        if actualizar.status_code != 200:
            conn.close()
            return jsonify({"error": "No se pudo actualizar stock"}), 500
        
        conn.execute("UPDATE pedidos SET estado=? WHERE id_pedido=?", (nuevo_estado, id_pedido))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Pedido actualizado a {nuevo_estado}"}), 200
    
    else:
        conn.execute("UPDATE pedidos SET estado=? WHERE id_pedido=?", (nuevo_estado, id_pedido))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Pedido actualizado a {nuevo_estado}"}), 200


@app.route("/pedidos/<int:id_pedido>", methods=["DELETE"])
@verificar_admin
def eliminar_pedido(id_pedido):
    conn = conexion_db()
    cursor = conn.execute("DELETE FROM pedidos WHERE id_pedido=?", (id_pedido,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Pedido no encontrado"}), 404
    conn.close()
    return jsonify({"message": "Pedido eliminado"}), 200

if __name__ == "__main__":
    app.run(port=5004, debug=True)