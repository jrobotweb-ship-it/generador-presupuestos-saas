import hashlib
import hmac
import base64
import json
import time
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-for-presupuestos-saas-2026")

def hash_password(password: str) -> str:
    """Hashea una contraseña usando PBKDF2 con sal."""
    salt = os.urandom(16)
    db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + db_hash.hex()

def verify_password(password: str, hashed: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    try:
        salt_hex, hash_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(db_hash, expected_hash)
    except Exception:
        return False

def create_token(payload: dict, expires_in: int = 86400) -> str:
    """Crea un token firmado con HMAC y codificado en Base64 con expiración."""
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + expires_in
    
    payload_json = json.dumps(payload_copy).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8')
    
    # Firmar
    sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8')
    
    return f"{payload_b64}.{sig_b64}"

def verify_token(token: str) -> dict:
    """Verifica el token firmado y retorna el payload original si es válido."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        payload_b64, sig_b64 = parts
        
        # Validar firma
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8')
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        # Decodificar payload
        payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8'))
        payload = json.loads(payload_json.decode('utf-8'))
        
        # Verificar expiración
        if int(time.time()) > payload.get("exp", 0):
            return None
            
        return payload
    except Exception:
        return None
