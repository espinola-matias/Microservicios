# 🛒 Sistema de Gestión de Pedidos con Arquitectura de Microservicios

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?style=for-the-badge&logo=flask&logoColor=black)
![SQLite](https://img.shields.io/badge/SQLite-Data-07405e?style=for-the-badge&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)

Este proyecto es una implementación práctica de una **Arquitectura de Microservicios**. Simula el backend de una plataforma de comercio electrónico donde cada responsabilidad de negocio está desacoplada en su propio servicio independiente.

El objetivo principal es demostrar la **comunicación sincrónica entre servicios** mediante HTTP (REST APIs), la gestión de transacciones distribuidas (validación de stock) y la seguridad centralizada mediante Tokens JWT.

---

## 🧩 Arquitectura y Lógica de Negocio

El sistema no es monolítico; está dividido en tres servicios autónomos. Cada uno tiene **su propia base de datos**, lo que garantiza el principio de **Database-per-service** (Base de datos por servicio).

### 1. Servicio de Clientes (Puerto `5002`)
> **"El Gestor de Identidad"**
* **Responsabilidad:** Actúa como la fuente de verdad sobre los usuarios.
* **Seguridad:** Es el único encargado de generar los **Tokens JWT** de acceso (Login).
* **Datos:** Almacena información sensible (email, cédula) y valida que el usuario sea quien dice ser.

### 2. Servicio de Productos (Puerto `5003`)
> **"El Almacén / Inventario"**
* **Responsabilidad:** Gestiona el catálogo y, lo más importante, el **Stock**.
* **Lógica Crítica:** Expone endpoints para consultar disponibilidad y para **restar stock** cuando se confirma una venta. Si no hay stock, impide la transacción.

### 3. Servicio de Pedidos (Puerto `5004`)
> **"El Orquestador"**
* **Responsabilidad:** Es el núcleo transaccional. No tiene datos de clientes ni productos, solo IDs.
* **Flujo de Compra Inteligente:** Cuando llega una solicitud de compra, este servicio:
    1.  Consulta al **Servicio de Clientes** para verificar que el usuario existe.
    2.  Consulta al **Servicio de Productos** para verificar precio y disponibilidad.
    3.  Si todo es válido, **resta el stock** (llamada PUT a Productos) y genera la orden localmente.

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Framework Web:** Flask (Minimalista y ligero, ideal para microservicios).
* **Base de Datos:** SQLite (Una instancia aislada `clients.db`, `productos.db`, `pedidos.db` por cada servicio).
* **Autenticación:** PyJWT (JSON Web Tokens) para seguridad *stateless*.
* **Comunicación:** Librería `requests` de Python para el consumo de APIs internas.

---