import time
import os
import json
import urllib.request
import urllib.error
import concurrent.futures

USAR_API_REAL = True
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class MemoriaAI:
    def __init__(self):
        self.usar_real = USAR_API_REAL
        if self.usar_real and not GEMINI_API_KEY:
            print("Advertencia: USAR_API_REAL es true pero no hay GEMINI_API_KEY.")
            self.usar_real = False

    def generar_memoria(self, datos_cliente, partidas):
        if self.usar_real:
            try:
                return self._generar_con_gemini_batched(datos_cliente, partidas)
            except Exception as e:
                print(f"Error en API Gemini para memoria batched, cayendo a simulador: {e}")
                return self._generar_simulado(datos_cliente, partidas)
        else:
            return self._generar_simulado(datos_cliente, partidas)

    def _llamar_api_gemini(self, prompt, max_retries=3):
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
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        retry_delay = 1.5
        response_data = None
        
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                break
            except urllib.error.HTTPError as he:
                if (he.code == 429 or he.code >= 500) and attempt < max_retries - 1:
                    print(f"Error HTTP {he.code} en llamada de Memoria, intento {attempt+1}, reintentando en {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise he
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error de conexion en llamada de Memoria, intento {attempt+1}, reintentando...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise e
                
        texto_respuesta = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # Extracción robusta de JSON buscando las llaves externas
        start_idx = texto_respuesta.find('{')
        end_idx = texto_respuesta.rfind('}')
        if start_idx != -1 and end_idx != -1:
            texto_json = texto_respuesta[start_idx:end_idx+1]
        else:
            texto_json = texto_respuesta
            
        return json.loads(texto_json.strip())

    def _generar_intro(self, datos_cliente):
        prompt = f'''
Actúa como un Ingeniero Civil Senior experto en redacción técnica. Genera la carátula y la introducción para una "Memoria Descriptiva Técnica" del siguiente proyecto de edificación:
Cliente: {datos_cliente.get('nombre', 'N/A')}
Proyecto: {datos_cliente.get('proyecto', 'N/A')}
Ubicación: {datos_cliente.get('ubicacion', 'N/A')}

Debes redactar con un vocabulario de ingeniería civil impecable, tono formal y sin errores ortográficos.

Devuelve UNICAMENTE un objeto JSON válido con esta estructura exacta:
{{
  "caratula": {{
    "titulo": "Memoria Descriptiva Técnica",
    "subtitulo": "Memoria descriptiva de arquitectura, estructura e instalaciones"
  }},
  "introduccion": "Una introducción técnica detallada de 2 a 3 párrafos explicando de qué trata la obra, sus alcances y objetivos generales con terminología técnica."
}}
'''
        return self._llamar_api_gemini(prompt)

    def _generar_explicaciones_lote(self, lote_partidas):
        prompt = f'''
Actúa como un Ingeniero Civil Senior altamente calificado, experto en redacción técnica, normativas y procesos constructivos. Tu objetivo es redactar especificaciones técnicas y explicaciones minuciosas del proceso constructivo de cada una de las partidas que te suministramos a continuación.

Debes analizar, desglosar e inspeccionar de forma independiente PARTIDA POR PARTIDA, de manera sumamente específica. No resumas, no globalices nada, absolutamente nada. No unas ni agrupes el análisis de las partidas. Cada una debe tratarse de forma aislada y detallarse exhaustivamente.

Para cada partida individual, debes proveer una explicación técnica completa, amplia y rigurosa en la vida real. Cada descripción debe ser EXTENSA (de mínimo 8 a 15 líneas de texto técnico descriptivo por partida), detallando con precisión quirúrgica:
1. Procedimiento paso a paso de ejecución en obra (cómo se realiza el replanteo, preparación del sitio, vaciado, tendido, empalmes, etc.).
2. Dosificaciones y materiales específicos utilizados (ej. dosificación exacta del mortero, resistencia del concreto f'c, clase y dimensiones de bloques, calibres e indicaciones de cabillas o tuberías). Integra de forma fluida los materiales listados en 'materiales_de_obra'.
3. Equipos, herramientas especiales y maquinaria pesada utilizados (ej. mezcladora de concreto, vibrador de inmersión, andamios tubulares, herramientas menores, etc.). Integra de forma fluida los equipos listados en 'equipos_y_herramientas'.
4. El propósito estructural, arquitectónico o de instalaciones de dicha partida y su interconexión técnica con las demás fases de la obra.

IMPORTANTE: Está estrictamente prohibido usar descripciones resumidas o genéricas de 3 a 5 líneas. Tómate todo el tiempo y espacio necesarios para ser sumamente explicativo y generar textos robustos e impecables de alta ingeniería.

Lote de partidas a analizar individualmente:
{json.dumps(lote_partidas, indent=2, ensure_ascii=False)}

Devuelve UNICAMENTE un objeto JSON válido con la siguiente estructura exacta:
{{
  "partidas": [
    {{
      "codigo": "Código original de la partida",
      "nombre_original": "Descripción técnica original",
      "explicacion_infantil": "Tu explicación técnica, extensa, exhaustiva e individual (mínimo 8-15 líneas) sobre el proceso constructivo real de esta partida incorporando los materiales y equipos del APU."
    }}
  ]
}}
'''
        return self._llamar_api_gemini(prompt)

    def _generar_con_gemini_batched(self, datos_cliente, partidas):
        print(f"Iniciando generación de memoria descriptiva batched para {len(partidas)} partidas...")
        
        # Enriquecer cada partida con sus materiales y equipos de la base de datos (APU)
        import database
        partidas_enriquecidas = []
        for p in partidas:
            p_copy = p.copy()
            codigo = p.get("codigo", "")
            apu = database.obtener_detalles_apu(codigo)
            if apu:
                p_copy["materiales_de_obra"] = [m["descripcion"] for m in apu["materiales"]]
                p_copy["equipos_y_herramientas"] = [e["descripcion"] for e in apu["equipos"]]
            else:
                p_copy["materiales_de_obra"] = []
                p_copy["equipos_y_herramientas"] = []
            partidas_enriquecidas.append(p_copy)
            
        # Tamaño de lote
        tamano_lote = 5
        lotes = [partidas_enriquecidas[i:i + tamano_lote] for i in range(0, len(partidas_enriquecidas), tamano_lote)]
        
        # Ejecutar llamadas en paralelo usando ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # Enviar tarea de introducción
            futuro_intro = executor.submit(self._generar_intro, datos_cliente)
            
            # Enviar tareas de lotes de partidas
            futuros_lotes = [executor.submit(self._generar_explicaciones_lote, lote) for lote in lotes]
            
            # Obtener resultado de la introducción
            resultado_intro = futuro_intro.result()
            
            # Obtener resultados de cada lote y unirlos
            partidas_explicadas = []
            for futuro in futuros_lotes:
                res_lote = futuro.result()
                if "partidas" in res_lote:
                    partidas_explicadas.extend(res_lote["partidas"])
                    
        # Ensamblar JSON final
        return {
            "caratula": resultado_intro.get("caratula", {
                "titulo": "Memoria Descriptiva Técnica",
                "subtitulo": f"Proyecto estructural y arquitectónico de {datos_cliente.get('nombre', '')}"
            }),
            "introduccion": resultado_intro.get("introduccion", "Introducción detallada del proyecto."),
            "partidas": partidas_explicadas,
            "conclusion": "En conclusión, las metodologías constructivas y especificaciones técnicas descritas en este documento garantizan que las obras civiles se ejecutarán cumpliendo cabalmente con las normas de seguridad, calidad y estabilidad estructural vigentes."
        }

    def _generar_simulado(self, datos_cliente, partidas):
        time.sleep(2)
        
        partidas_simuladas = []
        for p in partidas:
            desc = p.get('descripcion', '')
            codigo = p.get('codigo', '')
            partidas_simuladas.append({
                "codigo": codigo,
                "nombre_original": desc,
                "explicacion_infantil": (
                    f"La partida de {desc} contempla la ejecución minuciosa de los trabajos técnicos indicados en los planos de construcción. "
                    f"Esto comprende el suministro, acarreo y colocación de todos los materiales e insumos necesarios asociados a la codificación {codigo}. "
                    f"Asimismo, se incluye la mano de obra calificada (maestro de obra y ayudantes), el uso de herramientas menores, y los equipos de seguridad "
                    f"requeridos para garantizar la correcta culminación de los trabajos técnicos siguiendo los estándares de calidad y tolerancias recomendadas."
                )
            })
            
        return {
            "caratula": {
                "titulo": "Memoria Descriptiva Técnica",
                "subtitulo": f"Proyecto de Edificación de {datos_cliente.get('nombre', '')}"
            },
            "introduccion": "La presente Memoria Descriptiva tiene como objeto detallar los parámetros técnicos, procesos constructivos y normativas aplicadas en la ejecución del proyecto. A continuación se presentan las partidas correspondientes a la obra.",
            "partidas": partidas_simuladas,
            "conclusion": "En conclusión, las metodologías descritas aseguran la integridad estructural y arquitectónica del proyecto, cumpliendo estrictamente con los estándares de calidad vigentes."
        }
