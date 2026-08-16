import sqlite3
import os
import json

DB_NAME = "partidas.db"

def obtener_conexion():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # 1. Tablas de Insumos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Materiales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            descripcion TEXT NOT NULL,
            unidad TEXT NOT NULL,
            precio_usd REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            descripcion TEXT NOT NULL,
            unidad TEXT NOT NULL,
            tarifa_dia_usd REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ManoObra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            cargo TEXT NOT NULL,
            unidad TEXT NOT NULL,
            salario_dia_usd REAL NOT NULL
        )
    """)
    
    # 2. Tabla Partidas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Partidas (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT NOT NULL,
            unidad TEXT NOT NULL,
            rendimiento_diario REAL NOT NULL
        )
    """)
    
    # 3. Tablas Pivote (Composición APU)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Partida_Materiales (
            partida_codigo TEXT,
            material_id INTEGER,
            cantidad REAL NOT NULL,
            FOREIGN KEY(partida_codigo) REFERENCES Partidas(codigo),
            FOREIGN KEY(material_id) REFERENCES Materiales(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Partida_Equipos (
            partida_codigo TEXT,
            equipo_id INTEGER,
            cantidad REAL NOT NULL, -- Cantidad del equipo a utilizar en un día
            FOREIGN KEY(partida_codigo) REFERENCES Partidas(codigo),
            FOREIGN KEY(equipo_id) REFERENCES Equipos(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Partida_ManoObra (
            partida_codigo TEXT,
            mano_obra_id INTEGER,
            cantidad REAL NOT NULL, -- Cuántos trabajadores de este cargo
            FOREIGN KEY(partida_codigo) REFERENCES Partidas(codigo),
            FOREIGN KEY(mano_obra_id) REFERENCES ManoObra(id)
        )
    """)
    
    # 4. Tablas SaaS (Usuarios, Suscripciones y Presupuestos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Suscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            plan TEXT NOT NULL DEFAULT 'free',
            status TEXT NOT NULL DEFAULT 'active',
            metodo_pago TEXT,
            referencia_pago TEXT,
            current_period_end TEXT,
            FOREIGN KEY(user_id) REFERENCES Usuarios(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Presupuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nombre_proyecto TEXT NOT NULL,
            cliente TEXT NOT NULL,
            telefono TEXT,
            ubicacion TEXT,
            tasa_bcv REAL NOT NULL,
            items_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sugerencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipo TEXT NOT NULL, -- 'soporte' o 'sugerencia'
            mensaje TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Usuarios(id)
        )
    """)

    # Verificar si está vacía
    cursor.execute("SELECT COUNT(*) FROM Partidas")
    count = cursor.fetchone()[0]
    
    if count == 0:
        _sembrar_datos_ejemplo(cursor)
        conn.commit()
        print("Base de datos APU inicializada y sembrada con éxito.")
        
    # Sembrar usuarios administradores por defecto si no existen
    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE email = ?", ("admin@jrobotwweb.com",))
    if cursor.fetchone()[0] == 0:
        # Registrar admin@jrobotwweb.com con contraseña admin123
        cursor.execute("""
            INSERT INTO Usuarios (email, password_hash, nombre)
            VALUES (?, ?, ?)
        """, (
            "admin@jrobotwweb.com",
            "dc9686d9a020b6eeb5043f9f988cdd84:99e628cb68bbb3485c6af2ec88e06dc02c53d40c40e1751778550b040c2d7bbe",
            "Administrador JRobotWeb"
        ))
        
        # También registrar admin@jrobotweb.com con contraseña admin123
        cursor.execute("""
            INSERT INTO Usuarios (email, password_hash, nombre)
            VALUES (?, ?, ?)
        """, (
            "admin@jrobotweb.com",
            "dc9686d9a020b6eeb5043f9f988cdd84:99e628cb68bbb3485c6af2ec88e06dc02c53d40c40e1751778550b040c2d7bbe",
            "Administrador JRobotWeb (Variacion)"
        ))
        
        # También sembrar la suscripción activa para estos administradores
        cursor.execute("SELECT id FROM Usuarios WHERE email = ?", ("admin@jrobotwweb.com",))
        admin1_id = cursor.fetchone()[0]
        cursor.execute("INSERT OR IGNORE INTO Suscripciones (user_id, plan, status) VALUES (?, 'pro', 'active')", (admin1_id,))
        
        cursor.execute("SELECT id FROM Usuarios WHERE email = ?", ("admin@jrobotweb.com",))
        admin2_id = cursor.fetchone()[0]
        cursor.execute("INSERT OR IGNORE INTO Suscripciones (user_id, plan, status) VALUES (?, 'pro', 'active')", (admin2_id,))
        
        conn.commit()
        print("Usuarios administradores creados por defecto.")
    
    conn.close()

def _sembrar_datos_ejemplo(cursor):
    # Materiales
    mats = [
        ("M-001", "Cemento Portland", "saco", 8.50),
        ("M-002", "Arena Lavada", "m3", 15.00),
        ("M-003", "Piedra Picada", "m3", 18.00),
        ("M-004", "Agua", "lts", 0.02),
        ("M-005", "Cabilla 1/2 pulg (12m)", "und", 7.00),
        ("M-006", "Alambre Dulce", "kg", 2.50),
        ("M-007", "Bloque Arcilla 15cm", "und", 0.50),
        ("M-008", "Pintura Caucho Clase A", "gal", 25.00),
        ("M-009", "Fondo Antialcalino", "gal", 20.00)
    ]
    cursor.executemany("INSERT INTO Materiales (codigo, descripcion, unidad, precio_usd) VALUES (?, ?, ?, ?)", mats)

    # Equipos
    eqs = [
        ("E-001", "Herramientas Menores", "dia", 3.00),
        ("E-002", "Mezcladora 1 Saco", "dia", 35.00),
        ("E-003", "Cortadora de Cabilla", "dia", 15.00),
        ("E-004", "Andamios (Cuerpo)", "dia", 5.00),
        ("E-005", "Rodillos y Brochas", "dia", 5.00)
    ]
    cursor.executemany("INSERT INTO Equipos (codigo, descripcion, unidad, tarifa_dia_usd) VALUES (?, ?, ?, ?)", eqs)

    # Mano de Obra
    mos = [
        ("MO-001", "Obrero", "dia", 15.00),
        ("MO-002", "Albañil de 1ra", "dia", 25.00),
        ("MO-003", "Cabillero", "dia", 25.00),
        ("MO-004", "Pintor", "dia", 20.00)
    ]
    cursor.executemany("INSERT INTO ManoObra (codigo, cargo, unidad, salario_dia_usd) VALUES (?, ?, ?, ?)", mos)

    # Insertar Partidas
    partidas = [
        ("E-311.110.150", "Excavación a mano para asiento de fundaciones", "m3", 4.0),
        ("C-512.200.100", "Concreto f'c=250 kgf/cm2 para vigas y columnas", "m3", 5.0),
        ("A-611.110.120", "Acero de refuerzo (Cabillas)", "kg", 150.0),
        ("M-411.100.120", "Construcción de pared bloques 15cm", "m2", 12.0),
        ("P-621.110.200", "Pintura de caucho en interiores (2 manos)", "m2", 40.0)
    ]
    cursor.executemany("INSERT INTO Partidas (codigo, descripcion, unidad, rendimiento_diario) VALUES (?, ?, ?, ?)", partidas)

    # Relaciones para APU
    # 1. Excavación (Rend: 4 m3/día)
    # 2 obreros y herramientas
    cursor.execute("INSERT INTO Partida_Equipos (partida_codigo, equipo_id, cantidad) VALUES ('E-311.110.150', 1, 1)")
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('E-311.110.150', 1, 2)")

    # 2. Concreto (Rend: 5 m3/día) - Cantidades para 1 m3 de concreto
    # Materiales para 1 m3
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('C-512.200.100', 1, 7.5)") # Cemento
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('C-512.200.100', 2, 0.45)") # Arena
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('C-512.200.100', 3, 0.85)") # Piedra
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('C-512.200.100', 4, 200)") # Agua
    # Equipo por dia
    cursor.execute("INSERT INTO Partida_Equipos (partida_codigo, equipo_id, cantidad) VALUES ('C-512.200.100', 2, 1)")
    # MO por dia
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('C-512.200.100', 2, 1)") # 1 Albañil
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('C-512.200.100', 1, 3)") # 3 Obreros

    # 3. Acero (Rend: 150 kg/día)
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('A-611.110.120', 5, 0.1)") # 1 und cabilla pesa ~10kg, usamos 0.1 und por kg
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('A-611.110.120', 6, 0.05)") # Alambre
    cursor.execute("INSERT INTO Partida_Equipos (partida_codigo, equipo_id, cantidad) VALUES ('A-611.110.120', 3, 1)")
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('A-611.110.120', 3, 1)") # Cabillero
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('A-611.110.120', 1, 1)") # Obrero

    # 4. Pared de Bloque 15cm (Rend: 12 m2/día)
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('M-411.100.120', 7, 12.5)") # Bloques
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('M-411.100.120', 1, 0.25)") # Cemento
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('M-411.100.120', 2, 0.02)") # Arena
    cursor.execute("INSERT INTO Partida_Equipos (partida_codigo, equipo_id, cantidad) VALUES ('M-411.100.120', 4, 2)") # Andamios
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('M-411.100.120', 2, 1)") # Albañil
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('M-411.100.120', 1, 1)") # Obrero

    # 5. Pintura (Rend: 40 m2/día)
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('P-621.110.200', 8, 0.04)") # Pintura
    cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES ('P-621.110.200', 9, 0.02)") # Fondo
    cursor.execute("INSERT INTO Partida_Equipos (partida_codigo, equipo_id, cantidad) VALUES ('P-621.110.200', 5, 1)") # Rodillos
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('P-621.110.200', 4, 1)") # Pintor
    cursor.execute("INSERT INTO Partida_ManoObra (partida_codigo, mano_obra_id, cantidad) VALUES ('P-621.110.200', 1, 0.5)") # Ayudante medio tiempo

def calcular_precio_partida(codigo):
    """Calcula el precio unitario total de una partida en base a su APU."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Rendimiento
    cursor.execute("SELECT rendimiento_diario FROM Partidas WHERE codigo = ?", (codigo,))
    row_partida = cursor.fetchone()
    if not row_partida:
        return 0.0
    rendimiento = row_partida["rendimiento_diario"]

    # Costo Materiales (Directo por unidad)
    cursor.execute("""
        SELECT SUM(pm.cantidad * m.precio_usd) as total_mats
        FROM Partida_Materiales pm
        JOIN Materiales m ON pm.material_id = m.id
        WHERE pm.partida_codigo = ?
    """, (codigo,))
    total_mats = cursor.fetchone()["total_mats"] or 0.0

    # Retornamos solo materiales como pidieron
    conn.close()
    return total_mats

def obtener_todas_partidas():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, descripcion, unidad FROM Partidas ORDER BY codigo ASC")
    filas = cursor.fetchall()
    
    partidas = []
    for fila in filas:
        precio_usd = calcular_precio_partida(fila["codigo"])
        partidas.append({
            "codigo": fila["codigo"],
            "descripcion": fila["descripcion"],
            "unidad": fila["unidad"],
            "precio_usd": precio_usd
        })
    
    conn.close()
    return partidas

def buscar_partidas(criterio=""):
    if not criterio:
        return obtener_todas_partidas()
        
    conn = obtener_conexion()
    cursor = conn.cursor()
    criterio_like = f"%{criterio}%"
    cursor.execute("""
        SELECT codigo, descripcion, unidad FROM Partidas 
        WHERE codigo LIKE ? OR descripcion LIKE ?
        ORDER BY codigo ASC
    """, (criterio_like, criterio_like))
    filas = cursor.fetchall()
    
    partidas = []
    for fila in filas:
        precio_usd = calcular_precio_partida(fila["codigo"])
        partidas.append({
            "codigo": fila["codigo"],
            "descripcion": fila["descripcion"],
            "unidad": fila["unidad"],
            "precio_usd": precio_usd
        })
        
    conn.close()
    return partidas

def insertar_partida(codigo, descripcion, unidad, precio_usd):
    # En un sistema APU real, no se inserta "precio_usd", se construye el análisis.
    # Como el UI actual solo pide precio, simularemos que el precio es un "Material" único 
    # para mantener retrocompatibilidad de la UI sin romper el esquema APU.
    conn = obtener_conexion()
    cursor = conn.cursor()
    exito = False
    try:
        # Insertar partida con rendimiento dummy (1.0)
        cursor.execute("INSERT INTO Partidas (codigo, descripcion, unidad, rendimiento_diario) VALUES (?, ?, ?, 1.0)", 
                      (codigo.strip(), descripcion.strip(), unidad.strip()))
        
        # Crear un material dummy para esta partida que absorba el costo total
        cursor.execute("INSERT INTO Materiales (codigo, descripcion, unidad, precio_usd) VALUES (?, ?, ?, ?)",
                      (f"MAT-{codigo}", f"Material global para {codigo}", unidad, float(precio_usd)))
        mat_id = cursor.lastrowid
        
        # Relacionar material dummy con la partida
        cursor.execute("INSERT INTO Partida_Materiales (partida_codigo, material_id, cantidad) VALUES (?, ?, 1.0)", 
                      (codigo.strip(), mat_id))
        
        conn.commit()
        exito = True
    except Exception as e:
        print(f"Error al insertar partida: {e}")
        exito = False
    finally:
        conn.close()
    return exito

def actualizar_partida(codigo, descripcion, unidad, precio_usd):
    # Como usamos el material dummy para precio fijo (por la UI administrativa), lo actualizamos
    conn = obtener_conexion()
    cursor = conn.cursor()
    exito = False
    try:
        cursor.execute("UPDATE Partidas SET descripcion = ?, unidad = ? WHERE codigo = ?", 
                      (descripcion.strip(), unidad.strip(), codigo.strip()))
        
        # Buscar si existe el material dummy, si no, es una partida real y no deberia editarse así
        # Pero para que funcione la UI actual, actualizamos o insertamos el dummy
        cursor.execute("SELECT id FROM Materiales WHERE codigo = ?", (f"MAT-{codigo}",))
        mat = cursor.fetchone()
        if mat:
            cursor.execute("UPDATE Materiales SET precio_usd = ? WHERE id = ?", (float(precio_usd), mat["id"]))
        conn.commit()
        exito = True
    except Exception as e:
        print(f"Error al actualizar partida: {e}")
        exito = False
    finally:
        conn.close()
    return exito

def eliminar_partida(codigo):
    conn = obtener_conexion()
    cursor = conn.cursor()
    exito = False
    try:
        # Borrar relaciones en cascada (manual si no tenemos pragma activado)
        cursor.execute("DELETE FROM Partida_Materiales WHERE partida_codigo = ?", (codigo,))
        cursor.execute("DELETE FROM Partida_Equipos WHERE partida_codigo = ?", (codigo,))
        cursor.execute("DELETE FROM Partida_ManoObra WHERE partida_codigo = ?", (codigo,))
        
        # Borrar material dummy asociado si existia
        cursor.execute("DELETE FROM Materiales WHERE codigo = ?", (f"MAT-{codigo}",))
        
        # Borrar la partida
        cursor.execute("DELETE FROM Partidas WHERE codigo = ?", (codigo.strip(),))
        conn.commit()
        exito = True
    except Exception as e:
        print(f"Error al eliminar partida: {e}")
        exito = False
    finally:
        conn.close()
    return exito

def obtener_materiales_partida(codigo):
    """
    Dada una partida, retorna un listado de los materiales requeridos para 1 unidad,
    incluyendo su descripción, unidad y cantidad (ya escalada por el rendimiento si aplica).
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    # Para los materiales, la cantidad guardada en Partida_Materiales es directamente la cantidad por unidad de partida
    cursor.execute("""
        SELECT m.codigo, m.descripcion, m.unidad, pm.cantidad 
        FROM Partida_Materiales pm
        JOIN Materiales m ON pm.material_id = m.id
        WHERE pm.partida_codigo = ?
    """, (codigo,))
    
    filas = cursor.fetchall()
    materiales = []
    for f in filas:
        materiales.append({
            "codigo": f["codigo"],
            "descripcion": f["descripcion"],
            "unidad": f["unidad"],
            "cantidad": f["cantidad"]
        })
    conn.close()
    return materiales

# =========================================================================
# FUNCIONES SAAS: AUTENTICACIÓN, SUSCRIPCIONES Y PRESUPUESTOS EN LA NUBE
# =========================================================================

def registrar_usuario(email, password, nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    import user_auth
    password_hash = user_auth.hash_password(password)
    try:
        cursor.execute("INSERT INTO Usuarios (email, password_hash, nombre) VALUES (?, ?, ?)",
                       (email.strip().lower(), password_hash, nombre.strip()))
        user_id = cursor.lastrowid
        # Crear suscripción por defecto 'free'
        cursor.execute("INSERT INTO Suscripciones (user_id, plan, status) VALUES (?, 'free', 'active')", (user_id,))
        conn.commit()
        return {"id": user_id, "email": email, "nombre": nombre}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def obtener_usuario_por_email(email):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.email, u.password_hash, u.nombre, s.plan, s.status, s.metodo_pago, s.referencia_pago, s.current_period_end
        FROM Usuarios u
        LEFT JOIN Suscripciones s ON u.id = s.user_id
        WHERE u.email = ?
    """, (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def obtener_usuario_por_id(user_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.email, u.nombre, s.plan, s.status, s.metodo_pago, s.referencia_pago, s.current_period_end
        FROM Usuarios u
        LEFT JOIN Suscripciones s ON u.id = s.user_id
        WHERE u.id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def actualizar_suscripcion(user_id, plan, status, metodo_pago=None, referencia_pago=None):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Suscripciones (user_id, plan, status, metodo_pago, referencia_pago)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            plan = excluded.plan,
            status = excluded.status,
            metodo_pago = excluded.metodo_pago,
            referencia_pago = excluded.referencia_pago
    """, (user_id, plan, status, metodo_pago, referencia_pago))
    conn.commit()
    conn.close()

def guardar_presupuesto(presupuesto_id, user_id, nombre_proyecto, cliente, telefono, ubicacion, tasa_bcv, items):
    conn = obtener_conexion()
    cursor = conn.cursor()
    items_json = json.dumps(items)
    
    # Si presupuesto_id existe y pertenece a este usuario, actualizar
    if presupuesto_id:
        cursor.execute("""
            UPDATE Presupuestos 
            SET nombre_proyecto = ?, cliente = ?, telefono = ?, ubicacion = ?, tasa_bcv = ?, items_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (nombre_proyecto, cliente, telefono, ubicacion, tasa_bcv, items_json, presupuesto_id, user_id))
        filas_afectadas = cursor.rowcount
        conn.commit()
        conn.close()
        if filas_afectadas > 0:
            return presupuesto_id
        return None
    else:
        # Insertar nuevo
        cursor.execute("""
            INSERT INTO Presupuestos (user_id, nombre_proyecto, cliente, telefono, ubicacion, tasa_bcv, items_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, nombre_proyecto, cliente, telefono, ubicacion, tasa_bcv, items_json))
        nuevo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return nuevo_id

def obtener_presupuestos_usuario(user_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre_proyecto, cliente, telefono, ubicacion, tasa_bcv, created_at, updated_at
        FROM Presupuestos
        WHERE user_id = ?
        ORDER BY updated_at DESC
    """, (user_id,))
    filas = cursor.fetchall()
    conn.close()
    return [dict(f) for f in filas]

def obtener_presupuesto_por_id(presupuesto_id, user_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, nombre_proyecto, cliente, telefono, ubicacion, tasa_bcv, items_json, created_at, updated_at
        FROM Presupuestos
        WHERE id = ? AND user_id = ?
    """, (presupuesto_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        res = dict(row)
        res["items"] = json.loads(res["items_json"])
        return res
    return None

def eliminar_presupuesto(presupuesto_id, user_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Presupuestos WHERE id = ? AND user_id = ?", (presupuesto_id, user_id))
    exito = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return exito

def obtener_conteo_presupuestos(user_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Presupuestos WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def obtener_detalles_apu(codigo):
    """
    Obtiene los detalles del Análisis de Precios Unitarios (APU) para una partida específica.
    Retorna materiales, equipos y mano de obra estructurados.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # 1. Obtener datos básicos de la partida
    cursor.execute("SELECT descripcion, unidad, rendimiento_diario FROM Partidas WHERE codigo = ?", (codigo.strip(),))
    row_partida = cursor.fetchone()
    if not row_partida:
        conn.close()
        return None
        
    rendimiento = row_partida["rendimiento_diario"] or 1.0
    
    # 2. Materiales
    cursor.execute("""
        SELECT m.codigo, m.descripcion, m.unidad, pm.cantidad, m.precio_usd
        FROM Partida_Materiales pm
        JOIN Materiales m ON pm.material_id = m.id
        WHERE pm.partida_codigo = ?
    """, (codigo.strip(),))
    materiales = [dict(r) for r in cursor.fetchall()]
    
    # 3. Equipos
    cursor.execute("""
        SELECT e.codigo, e.descripcion, e.unidad, pe.cantidad, e.tarifa_dia_usd
        FROM Partida_Equipos pe
        JOIN Equipos e ON pe.equipo_id = e.id
        WHERE pe.partida_codigo = ?
    """, (codigo.strip(),))
    equipos = [dict(r) for r in cursor.fetchall()]
    
    # 4. Mano de Obra
    cursor.execute("""
        SELECT mo.codigo, mo.cargo as descripcion, mo.unidad, pmo.cantidad, mo.salario_dia_usd
        FROM Partida_ManoObra pmo
        JOIN ManoObra mo ON pmo.mano_obra_id = mo.id
        WHERE pmo.partida_codigo = ?
    """, (codigo.strip(),))
    mano_obra = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "codigo": codigo.strip(),
        "descripcion": row_partida["descripcion"],
        "unidad": row_partida["unidad"],
        "rendimiento": rendimiento,
        "materiales": materiales,
        "equipos": equipos,
        "mano_obra": mano_obra
    }

def obtener_todos_usuarios():
    """Retorna una lista con todos los usuarios registrados y su estado de suscripción."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.email, u.nombre, u.created_at, s.plan, s.status, s.metodo_pago, s.referencia_pago, s.current_period_end,
               (SELECT COUNT(*) FROM Presupuestos WHERE user_id = u.id) as total_presupuestos
        FROM Usuarios u
        LEFT JOIN Suscripciones s ON u.id = s.user_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def actualizar_suscripcion_admin(user_id, plan, status, current_period_end=None):
    """Actualiza o crea una suscripción con plan y fecha de vencimiento."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Suscripciones WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("""
            UPDATE Suscripciones
            SET plan = ?, status = ?, current_period_end = ?
            WHERE user_id = ?
        """, (plan, status, current_period_end, user_id))
    else:
        cursor.execute("""
            INSERT INTO Suscripciones (user_id, plan, status, current_period_end)
            VALUES (?, ?, ?, ?)
        """, (user_id, plan, status, current_period_end))
    conn.commit()
    conn.close()
    return True

def registrar_sugerencia(user_id, tipo, mensaje):
    """Guarda una sugerencia o reporte de soporte técnico en la base de datos."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Sugerencias (user_id, tipo, mensaje)
        VALUES (?, ?, ?)
    """, (user_id, tipo, mensaje))
    conn.commit()
    conn.close()
    return True

def obtener_todas_sugerencias():
    """Retorna todas las sugerencias y reportes enviados por los usuarios."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.user_id, u.email, u.nombre, s.tipo, s.mensaje, s.created_at
        FROM Sugerencias s
        JOIN Usuarios u ON s.user_id = u.id
        ORDER BY s.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    inicializar_db()
    print("Base de datos inicializada con soporte SaaS.")
