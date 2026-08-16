from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, status, Depends
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import os
import json

# Importar módulos locales
import database
import user_auth
import pdf_generator
import pdf_memoria
import pdf_apu
from vision_ai import VisionAI
from memoria_ai import MemoriaAI
from chat_ai import ChatAI

app = FastAPI(title="API SaaS de Presupuestos de Construcción")

# Inicializar Base de Datos SQLite con soporte SaaS
database.inicializar_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ia_engine = VisionAI()
memoria_engine = MemoriaAI()
chat_engine = ChatAI()

# =========================================================================
# MIDDLEWARE / DEPENDENCIAS DE SEGURIDAD (AUTENTICACIÓN)
# =========================================================================

async def get_current_user(request: Request):
    """Obtiene el usuario actual leyendo la cookie session_token."""
    token = request.cookies.get("session_token")
    if not token:
        return None
    payload = user_auth.verify_token(token)
    if not payload:
        return None
    user = database.obtener_usuario_por_id(payload.get("user_id"))
    return user

async def require_auth(user = Depends(get_current_user)):
    """Exige que el usuario esté logueado."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o no autorizado. Por favor inicie sesión."
        )
    return user

async def require_pro(user = Depends(require_auth)):
    """Exige que el usuario tenga un plan Pro activo."""
    if user.get("plan") != "pro" or user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Función Premium. Esta herramienta requiere una suscripción Pro activa."
        )
    return user

# =========================================================================
# ENDPOINTS DE AUTENTICACIÓN (REGISTRO / LOGIN)
# =========================================================================

class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register")
def registrar_usuario_api(req: RegisterRequest):
    user = database.registrar_usuario(req.email, req.password, req.nombre)
    if not user:
        raise HTTPException(status_code=400, detail="El correo electrónico ya se encuentra registrado.")
    return {"status": "success", "message": "Usuario registrado correctamente.", "user": user}

@app.post("/api/auth/login")
def iniciar_sesion_api(req: LoginRequest):
    user = database.obtener_usuario_por_email(req.email)
    if not user or not user_auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Correo electrónico o contraseña incorrectos.")
    
    # Crear token JWT simulado
    token = user_auth.create_token({"user_id": user["id"], "email": user["email"]})
    
    is_admin = (user["email"] in ["admin@jrobotweb.com", "admin@presupuestos.jrobotweb.com", "jrobotweb@gmail.com", "admin@jrobotwweb.com"])
    response = JSONResponse(content={
        "status": "success",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "nombre": user["nombre"],
            "plan": user["plan"],
            "status": user["status"],
            "is_admin": is_admin
        }
    })
    # Guardar en cookie segura
    response.set_cookie(key="session_token", value=token, httponly=True, max_age=86400, samesite="lax")
    return response

@app.post("/api/auth/logout")
def cerrar_sesion_api():
    response = JSONResponse(content={"status": "success", "message": "Sesión cerrada correctamente."})
    response.delete_cookie("session_token")
    return response

@app.get("/api/auth/me")
def obtener_perfil_api(user = Depends(get_current_user)):
    if not user:
        return {"logged_in": False}
    is_admin = (user["email"] in ["admin@jrobotweb.com", "admin@presupuestos.jrobotweb.com", "jrobotweb@gmail.com", "admin@jrobotwweb.com"])
    return {
        "logged_in": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "nombre": user["nombre"],
            "plan": user["plan"],
            "status": user["status"],
            "is_admin": is_admin,
            "metodo_pago": user.get("metodo_pago"),
            "referencia_pago": user.get("referencia_pago"),
            "current_period_end": user.get("current_period_end")
        }
    }

# =========================================================================
# ENDPOINTS DE SUSCRIPCIONES (SAAS - PAYPAL / TRANSFERENCIA BANCARIA)
# =========================================================================

class SubscribeRequest(BaseModel):
    metodo_pago: str  # 'paypal' o 'transferencia'
    referencia_pago: str

@app.post("/api/saas/subscribe")
def suscribir_pro_api(req: SubscribeRequest, user = Depends(require_auth)):
    # Simular aprobación automática para entorno de pruebas, activando de inmediato
    plan = "pro"
    status_sub = "active"
    
    database.actualizar_suscripcion(
        user_id=user["id"],
        plan=plan,
        status=status_sub,
        metodo_pago=req.metodo_pago,
        referencia_pago=req.referencia_pago
    )
    return {
        "status": "success",
        "message": f"Suscripción registrada vía {req.metodo_pago.upper()} con referencia {req.referencia_pago}.",
        "plan": plan,
        "status_suscripcion": status_sub
    }

@app.post("/api/saas/cancel")
def cancelar_suscripcion_api(user = Depends(require_auth)):
    database.actualizar_suscripcion(
        user_id=user["id"],
        plan="free",
        status="active",
        metodo_pago=None,
        referencia_pago=None
    )
    return {"status": "success", "message": "Suscripción cancelada. Regresó al Plan Free."}

# =========================================================================
# ENDPOINTS DE PRESUPUESTOS EN LA NUBE
# =========================================================================

class BudgetSaveRequest(BaseModel):
    id: Optional[int] = None
    nombre_proyecto: str
    cliente: str
    telefono: Optional[str] = ""
    ubicacion: Optional[str] = ""
    tasa_bcv: float
    items: List[Dict[str, Any]]

@app.get("/api/presupuestos")
def listar_presupuestos_api(user = Depends(require_auth)):
    presupuestos = database.obtener_presupuestos_usuario(user["id"])
    return {"status": "success", "presupuestos": presupuestos}

@app.get("/api/presupuestos/{presupuesto_id}")
def obtener_presupuesto_api(presupuesto_id: int, user = Depends(require_auth)):
    p = database.obtener_presupuesto_por_id(presupuesto_id, user["id"])
    if not p:
        raise HTTPException(status_code=404, detail="El presupuesto solicitado no existe o no tiene acceso.")
    return {"status": "success", "presupuesto": p}

@app.post("/api/presupuestos")
def guardar_presupuesto_api(req: BudgetSaveRequest, user = Depends(require_auth)):
    user_id = user["id"]
    es_pro = (user.get("plan") == "pro" and user.get("status") == "active")
    
    # 1. Validar límite de presupuestos para Free (máximo 1 presupuesto)
    if not es_pro and not req.id:
        conteo = database.obtener_conteo_presupuestos(user_id)
        if conteo >= 1:
            raise HTTPException(
                status_code=403, 
                detail="Límite del Plan Free alcanzado. Solo se permite 1 presupuesto en la nube. Actualice a Pro para guardar presupuestos ilimitados."
            )
            
    # 2. Validar límite de partidas por presupuesto para Free (máximo 10 partidas)
    if not es_pro and len(req.items) > 10:
        raise HTTPException(
            status_code=403, 
            detail="Límite del Plan Free alcanzado. El presupuesto gratis solo permite hasta 10 partidas. Actualice a Pro para registrar más de 10 partidas."
        )
        
    p_id = database.guardar_presupuesto(
        presupuesto_id=req.id,
        user_id=user_id,
        nombre_proyecto=req.nombre_proyecto,
        cliente=req.cliente,
        telefono=req.telefono,
        ubicacion=req.ubicacion,
        tasa_bcv=req.tasa_bcv,
        items=req.items
    )
    
    return {"status": "success", "id": p_id, "message": "Presupuesto guardado en la nube."}

@app.delete("/api/presupuestos/{presupuesto_id}")
def eliminar_presupuesto_api(presupuesto_id: int, user = Depends(require_auth)):
    exito = database.eliminar_presupuesto(presupuesto_id, user["id"])
    if not exito:
        raise HTTPException(status_code=404, detail="El presupuesto no se pudo encontrar para eliminar.")
    return {"status": "success", "message": "Presupuesto eliminado correctamente de la nube."}

# =========================================================================
# ENDPOINTS GENERALES DEL SISTEMA (CON CONTROL DE PLANES)
# =========================================================================

@app.get("/api/catalogo")
def obtener_catalogo(q: Optional[str] = ""):
    # El catálogo es accesible para búsqueda por todos
    return database.buscar_partidas(q)

@app.post("/api/analizar")
async def analizar_imagen(
    imagen: UploadFile = File(...),
    largo: float = Form(...),
    ancho: float = Form(...),
    alto: float = Form(...),
    requerimientos: Optional[str] = Form(""),
    user = Depends(require_pro) # Protegido: Exige Pro
):
    # Guardar imagen temporal
    temp_path = f"temp_saas_{imagen.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await imagen.read())
        
    try:
        resultados = ia_engine.analizar_imagen(temp_path, largo, ancho, alto, requerimientos)
        
        partidas_encontradas = []
        # Cargar catálogo completo en memoria para una búsqueda veloz
        conn = database.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, descripcion, unidad FROM Partidas")
        catalogo = [{"codigo": r[0], "descripcion": r[1], "unidad": r[2]} for r in cursor.fetchall()]
        
        STOP_WORDS = {"de", "para", "con", "en", "el", "la", "los", "las", "un", "una", "y", "a", "o", "u", "por", "sobre", "del", "al", "e", "tipo", "sobre", "e=15cm", "e=10cm", "h=2.10m"}
        
        # Grupos de sujetos clave para evitar cruzamiento incorrecto
        KEY_SUBJECT_GROUPS = [
            ["escalera", "escaleras"],
            ["reja", "rejas"],
            ["puerta", "puertas"],
            ["ventana", "ventanas"],
            ["pared", "paredes", "tabique", "tabiquería"],
            ["inodoro", "poceta"],
            ["lavamanos"],
            ["ducha"],
            ["fregadero"],
            ["batea"],
            ["tanque"],
            ["bomba", "hidroneumático"],
            ["limpieza"],
            ["deforestación"],
            ["replanteo"],
            ["excavación", "excavacion"],
            ["relleno"],
            ["tubo", "tubería", "tuberías"],
            ["cable", "cableado", "conductor"],
            ["tomacorriente", "tomacorrientes"],
            ["luminaria", "lámpara", "reflectores", "iluminación", "luz"],
            ["pintura", "esmalte"],
            ["baranda", "barandas", "barandilla", "barandillas", "pasamanos"]
        ]
        
        from difflib import SequenceMatcher
        
        def obtener_similitud(s1, s2):
            s1_lower = s1.lower()
            s2_lower = s2.lower()
            
            # Verificación estricta de sujetos clave bidireccional
            for group in KEY_SUBJECT_GROUPS:
                has_s1 = any(word in s1_lower for word in group)
                has_s2 = any(word in s2_lower for word in group)
                if has_s1 != has_s2:
                    return 0.0 # Penalización total por discrepancia de sujeto principal bidireccional
                        
            s1_words = set(w.lower() for w in s1.replace("(", "").replace(")", "").replace("/", " ").replace(",", " ").split() if len(w) > 3)
            s2_words = set(w.lower() for w in s2.replace("(", "").replace(")", "").replace("/", " ").replace(",", " ").split() if len(w) > 3)
            
            word_overlap = 0
            for w1 in s1_words:
                if w1 in STOP_WORDS:
                    continue
                for w2 in s2_words:
                    if w2 in STOP_WORDS:
                        continue
                    if w1 == w2 or (len(w1) > 4 and len(w2) > 4 and (w1 in w2 or w2 in w1)):
                        word_overlap += 1
                        break
                        
            ratio = SequenceMatcher(None, s1_lower, s2_lower).ratio()
            if word_overlap > 0:
                ratio += 0.08 * word_overlap
            return min(1.0, ratio)

        def filtrar_candidatos(elem, catalogo):
            palabras = [p.lower() for p in elem.replace("(", "").replace(")", "").replace("/", " ").replace(",", " ").split() if len(p) > 2]
            keywords = [p for p in palabras if p not in STOP_WORDS]
            if not keywords:
                return catalogo
            candidatos = []
            for item in catalogo:
                desc_lower = item["descripcion"].lower()
                for kw in keywords:
                    matched = False
                    if kw in desc_lower:
                        matched = True
                    elif len(kw) > 4:
                        root = kw[:-1] if kw.endswith('s') else kw
                        if root in desc_lower:
                            matched = True
                    if matched:
                        candidatos.append(item)
                        break
            return candidatos if candidatos else catalogo

        partidas_encontradas = []
        for res in resultados:
            code = res.get("sugerencia_partida_codigo", "")
            elem = res.get("elemento", "")
            cant = float(res.get("cantidad", 1.0))
            
            # Limpiar el formato del código sugerido
            code_clean = code.strip().replace(" ", "")
            if code_clean.startswith("E."):
                code_clean = "E-" + code_clean[2:]
            elif code_clean.startswith("C."):
                code_clean = "C-" + code_clean[2:]
            elif code_clean.startswith("L."):
                code_clean = "L-" + code_clean[2:]
            elif code_clean.startswith("F."):
                code_clean = "F-" + code_clean[2:]
                
            matched_item = None
            
            # 1. Intentar coincidencia exacta por código
            for item in catalogo:
                if item["codigo"] == code_clean:
                    matched_item = item.copy()
                    break
                    
            # 2. Si no, buscar la partida con mayor coincidencia de palabras y descripción
            if not matched_item:
                candidatos = filtrar_candidatos(elem, catalogo)
                
                # Optimizar filtrado para calcular similitud solo sobre el top 25 de solapamiento
                candidatos_con_score = []
                palabras_elem = set(w.lower() for w in elem.replace("(", "").replace(")", "").replace("/", " ").replace(",", " ").split() if len(w) > 2)
                keywords_elem = palabras_elem - STOP_WORDS
                
                for item in candidatos:
                    palabras_item = set(w.lower() for w in item["descripcion"].replace("(", "").replace(")", "").replace("/", " ").replace(",", " ").split() if len(w) > 2)
                    keywords_item = palabras_item - STOP_WORDS
                    overlap = len(keywords_elem.intersection(keywords_item))
                    if overlap > 0:
                        candidatos_con_score.append((overlap, item))
                        
                if candidatos_con_score:
                    candidatos_con_score.sort(key=lambda x: x[0], reverse=True)
                    candidatos_reducidos = [item for _, item in candidatos_con_score[:25]]
                else:
                    candidatos_reducidos = candidatos[:25]
                    
                mejor_item = None
                mejor_score = 0.0
                for item in candidatos_reducidos:
                    score = obtener_similitud(elem, item["descripcion"])
                    if score > mejor_score:
                        mejor_score = score
                        mejor_item = item
                        
                if mejor_item and mejor_score > 0.25:
                    matched_item = mejor_item.copy()
            
            if matched_item:
                p = matched_item.copy()
                p["cantidad"] = cant
                # Conservar la descripción detallada generada por la IA
                p["descripcion"] = elem
                # Calcular el precio real de la partida en la base de datos de manera puntual
                p["precio_usd"] = database.calcular_precio_partida(p["codigo"])
                partidas_encontradas.append(p)
                 
        return {"status": "success", "resultados": partidas_encontradas}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

class BomRequest(BaseModel):
    items: List[Dict[str, Any]]

@app.post("/api/bom")
def calcular_bom(req: BomRequest, user = Depends(require_pro)): # Protegido: Exige Pro
    conn = database.obtener_conexion()
    cursor = conn.cursor()
    
    bom = {}
    for item in req.items:
        cod = item.get("codigo")
        cant_partida = float(item.get("cantidad", 0))
        
        cursor.execute("""
            SELECT m.codigo, m.descripcion, m.unidad, pm.cantidad
            FROM Partida_Materiales pm
            JOIN Materiales m ON pm.material_id = m.id
            WHERE pm.partida_codigo = ?
        """, (cod,))
        materiales = cursor.fetchall()
        
        for m in materiales:
            mat_cod = m["codigo"]
            if mat_cod.startswith("MAT-"):
                continue
            
            cant_requerida = m["cantidad"] * cant_partida
            if mat_cod in bom:
                bom[mat_cod]["cantidad"] += cant_requerida
            else:
                bom[mat_cod] = {
                    "codigo": mat_cod,
                    "descripcion": m["descripcion"],
                    "unidad": m["unidad"],
                    "cantidad": cant_requerida
                }

    conn.close()
    return {"status": "success", "bom": list(bom.values())}

class PdfRequest(BaseModel):
    datos_cliente: Dict[str, Any]
    items: List[Dict[str, Any]]
    tasa_bcv: float
    incluir_imagen: bool
    datos_profesional: Optional[Dict[str, Any]] = None

@app.post("/api/presupuesto/pdf")
def generar_pdf_api(req: PdfRequest, user = Depends(require_auth)):
    # Los usuarios Pro tienen descargas ilimitadas. 
    # Los usuarios Free tienen un límite de 65 partidas.
    es_pro = (user.get("plan") == "pro" and user.get("status") == "active")
    if not es_pro and len(req.items) > 65:
        raise HTTPException(
            status_code=403,
            detail="Plan Free limitado a presupuestos de hasta 65 partidas para PDF. Actualice a Pro para presupuestos ilimitados."
        )
        
    nombre_archivo = f"presupuesto_saas_temp_{os.getpid()}.pdf"
    
    sub_usd = sum(item.get("cantidad", 0) * item.get("precio_usd", 0) for item in req.items)
    sub_ves = sub_usd * req.tasa_bcv
    
    exito = pdf_generator.generar_pdf_presupuesto(
        nombre_archivo, 
        req.datos_cliente, 
        req.items, 
        req.tasa_bcv, 
        sub_usd, 
        sub_ves,
        datos_profesional=req.datos_profesional
    )
    
    if exito and os.path.exists(nombre_archivo):
        with open(nombre_archivo, "rb") as f:
            pdf_data = f.read()
        os.remove(nombre_archivo)
        return Response(content=pdf_data, media_type="application/pdf")
    else:
        raise HTTPException(status_code=500, detail="No se pudo generar el PDF del presupuesto.")

class ApuPdfRequest(BaseModel):
    items: List[Dict[str, Any]]
    tasa_bcv: float
    datos_cliente: Dict[str, Any]
    datos_profesional: Optional[Dict[str, Any]] = None

@app.post("/api/presupuesto/apu-pdf")
def generar_apu_pdf_api(req: ApuPdfRequest, user = Depends(require_pro)): # Protegido: Exige Pro
    nombre_archivo = f"apu_saas_temp_{os.getpid()}.pdf"
    
    exito = pdf_apu.generar_pdf_apus(
        nombre_archivo,
        req.items,
        req.tasa_bcv,
        datos_profesional=req.datos_profesional
    )
    
    if exito and os.path.exists(nombre_archivo):
        with open(nombre_archivo, "rb") as f:
            pdf_data = f.read()
        os.remove(nombre_archivo)
        return Response(content=pdf_data, media_type="application/pdf")
    else:
        raise HTTPException(status_code=500, detail="No se pudo generar el PDF detallado de APUs.")

class MemoriaRequest(BaseModel):
    datos_cliente: Dict[str, Any]
    items: List[Dict[str, Any]]
    datos_profesional: Optional[Dict[str, Any]] = None

@app.post("/api/memoria")
def generar_memoria_api(req: MemoriaRequest, user = Depends(require_pro)): # Protegido: Exige Pro
    # Generar texto descriptivo con la IA
    datos_memoria = memoria_engine.generar_memoria(req.datos_cliente, req.items)
    
    if not datos_memoria:
        raise HTTPException(status_code=500, detail="No se pudo redactar la memoria descriptiva mediante IA.")
        
    nombre_archivo = f"memoria_saas_temp_{os.getpid()}.pdf"
    
    # Generar PDF de memoria descriptiva
    exito = pdf_memoria.generar_pdf_memoria(
        nombre_archivo, 
        datos_memoria, 
        req.datos_cliente,
        datos_profesional=req.datos_profesional
    )
    
    if exito and os.path.exists(nombre_archivo):
        with open(nombre_archivo, "rb") as f:
            pdf_data = f.read()
        os.remove(nombre_archivo)
        return Response(content=pdf_data, media_type="application/pdf")
    else:
        raise HTTPException(status_code=500, detail="No se pudo estructurar el PDF final de la memoria.")

class ChatRequest(BaseModel):
    mensaje: str
    historial: List[Dict[str, str]]
    partidas: List[Dict[str, Any]]

@app.post("/api/chat")
def procesar_chat(req: ChatRequest, user = Depends(require_pro)): # Protegido: Exige Pro
    respuesta_ia = chat_engine.procesar_mensaje(req.mensaje, req.historial, req.partidas)
    
    acciones_procesadas = []
    if "acciones" in respuesta_ia and isinstance(respuesta_ia["acciones"], list):
        for accion in respuesta_ia["acciones"]:
            if accion.get("tipo") == "añadir":
                sug = accion.get("codigo_sugerido", "")
                matches = database.buscar_partidas(sug)
                if matches:
                    p = matches[0]
                    p["cantidad"] = accion.get("cantidad", 1)
                    acciones_procesadas.append({
                        "tipo": "añadir",
                        "partida": p
                    })
                else:
                    matches_desc = database.buscar_partidas(accion.get("descripcion", ""))
                    if matches_desc:
                        p = matches_desc[0]
                        p["cantidad"] = accion.get("cantidad", 1)
                        acciones_procesadas.append({
                            "tipo": "añadir",
                            "partida": p
                        })
            else:
                acciones_procesadas.append(accion)
                
    return {
        "status": "success",
        "respuesta": respuesta_ia.get("respuesta", ""),
        "acciones": acciones_procesadas
    }

# =========================================================================
# ENDPOINTS DE SOPORTE, SUGERENCIAS Y ADMINISTRACIÓN (ADMIN DASHBOARD)
# =========================================================================

class SugerenciaRequest(BaseModel):
    tipo: str  # 'soporte' o 'sugerencia'
    mensaje: str

@app.post("/api/sugerencias")
def registrar_sugerencia_api(req: SugerenciaRequest, user = Depends(require_auth)):
    database.registrar_sugerencia(user["id"], req.tipo, req.mensaje)
    return {"status": "success", "message": "Reporte registrado correctamente."}

def require_admin(user = Depends(require_auth)):
    """Verifica si el usuario es administrador (email jrobotweb o admin)."""
    is_admin = (user["email"] in ["admin@jrobotweb.com", "admin@presupuestos.jrobotweb.com", "jrobotweb@gmail.com"])
    if not is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requieren privilegios de Administrador.")
    return user

@app.get("/api/admin/users")
def admin_obtener_usuarios(user = Depends(require_admin)):
    users = database.obtener_todos_usuarios()
    return {"status": "success", "users": users}

class UpdatePlanRequest(BaseModel):
    user_id: int
    plan: str
    status: str
    current_period_end: Optional[str] = None

@app.post("/api/admin/users/update-plan")
def admin_actualizar_plan(req: UpdatePlanRequest, user = Depends(require_admin)):
    database.actualizar_suscripcion_admin(req.user_id, req.plan, req.status, req.current_period_end)
    return {"status": "success", "message": "Plan de usuario actualizado correctamente."}

@app.get("/api/admin/sugerencias")
def admin_obtener_sugerencias(user = Depends(require_admin)):
    sugs = database.obtener_todas_sugerencias()
    return {"status": "success", "sugerencias": sugs}

# Montar archivos estáticos del frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
