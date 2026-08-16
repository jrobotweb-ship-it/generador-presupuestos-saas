import os
import json
import urllib.request
import urllib.error

USAR_API_REAL = True
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class ChatAI:
    def __init__(self):
        self.usar_real = USAR_API_REAL
        if self.usar_real and not GEMINI_API_KEY:
            print("Advertencia: USAR_VISION_API_REAL es true pero no hay GEMINI_API_KEY.")
            self.usar_real = False

    def procesar_mensaje(self, mensaje_usuario, historial, partidas_actuales):
        if self.usar_real:
            try:
                return self._procesar_con_gemini(mensaje_usuario, historial, partidas_actuales)
            except Exception as e:
                print(f"Error en API Gemini para chat, cayendo a simulador: {e}")
                return self._procesar_simulado(mensaje_usuario, historial, partidas_actuales)
        else:
            return self._procesar_simulado(mensaje_usuario, historial, partidas_actuales)

    def _procesar_con_gemini(self, mensaje_usuario, historial, partidas_actuales):
        prompt = f'''
Actúa como un Ingeniero Civil Senior experto en elaboración de presupuestos. Tu trabajo es interpretar las peticiones del usuario y modificar el presupuesto de obra actual.

Presupuesto actual (lista de partidas en JSON):
{json.dumps(partidas_actuales, indent=2, ensure_ascii=False)}

Historial del chat reciente:
{json.dumps(historial, indent=2, ensure_ascii=False)}

Nuevo mensaje del usuario: "{mensaje_usuario}"

Debes devolver UNICAMENTE un objeto JSON válido. El sistema fallará si incluyes formato Markdown como ```json o texto fuera del objeto.
Estructura exacta:
{{
  "respuesta": "Un mensaje amigable y profesional confirmando la acción (ej. 'He agregado 50 m2 de pintura a las paredes interiores.') o pidiendo más detalles.",
  "acciones": [
    {{
      "tipo": "añadir",
      "descripcion": "Descripción de la partida que se quiere añadir (muy breve)",
      "codigo_sugerido": "Sugerir código COVENIN aproximado (ej: E-412.111.000)",
      "cantidad": 50,
      "unidad": "m2"
    }},
    {{
      "tipo": "eliminar",
      "codigo": "Código exacto de la partida a eliminar"
    }},
    {{
      "tipo": "modificar",
      "codigo": "Código exacto de la partida a modificar",
      "nueva_cantidad": 100
    }}
  ]
}}
Si no hay acciones concretas a realizar, deja el arreglo "acciones" vacío.
'''

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            texto_respuesta = result['candidates'][0]['content']['parts'][0]['text']
            
            texto_respuesta = texto_respuesta.strip()
            if texto_respuesta.startswith("```json"): texto_respuesta = texto_respuesta[7:]
            if texto_respuesta.startswith("```"): texto_respuesta = texto_respuesta[3:]
            if texto_respuesta.endswith("```"): texto_respuesta = texto_respuesta[:-3]
                
            return json.loads(texto_respuesta)

    def _procesar_simulado(self, mensaje_usuario, historial, partidas_actuales):
        # Simulador local para cuando no hay API Key
        # Para propósitos de simulación, agregaremos una partida estática y borraremos otra si se solicita.
        acciones = []
        msg = mensaje_usuario.lower()
        if "pintura" in msg or "añadir" in msg or "agregar" in msg:
            acciones.append({
                "tipo": "añadir",
                "descripcion": "Pintura en interiores",
                "codigo_sugerido": "E-421.111.000",
                "cantidad": 100,
                "unidad": "m2"
            })
            respuesta = "Simulador: He agregado 100 m2 de pintura como solicitaste (Modo sin API Key)."
        elif "eliminar" in msg or "borrar" in msg:
            if partidas_actuales:
                acciones.append({
                    "tipo": "eliminar",
                    "codigo": partidas_actuales[0]['codigo']
                })
                respuesta = f"Simulador: He eliminado la primera partida ({partidas_actuales[0]['codigo']})."
            else:
                respuesta = "Simulador: No hay partidas para eliminar."
        else:
            respuesta = "Simulador: Entendido. (Recuerda configurar tu API Key para que pueda razonar como un verdadero Ingeniero)."
            
        return {
            "respuesta": respuesta,
            "acciones": acciones
        }
