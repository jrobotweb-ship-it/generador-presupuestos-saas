import os
import json
import time
import math
import base64
import urllib.request
import urllib.error

USAR_API_REAL = True
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class VisionAI:
    def __init__(self):
        self.usar_real = USAR_API_REAL
        if self.usar_real and not GEMINI_API_KEY:
            print("Advertencia: USAR_VISION_API_REAL es true pero no hay GEMINI_API_KEY.")
            self.usar_real = False

    def analizar_imagen(self, ruta_imagen, largo, ancho, alto, requerimientos_cliente=""):
        if self.usar_real:
            try:
                return self._analizar_con_gemini(ruta_imagen, largo, ancho, alto, requerimientos_cliente)
            except Exception as e:
                print(f"Error en API Gemini, cayendo a simulador: {e}")
                return self._analizar_simulado(ruta_imagen, largo, ancho, alto, requerimientos_cliente)
        else:
            return self._analizar_simulado(ruta_imagen, largo, ancho, alto, requerimientos_cliente)

    def _analizar_simulado(self, ruta_imagen, largo, ancho, alto, requerimientos_cliente=""):
        import unicodedata
        import re
        
        reqs = unicodedata.normalize('NFKD', requerimientos_cliente).encode('ASCII', 'ignore').decode('utf-8').lower()
        
        area_base = largo * ancho
        perimetro = 2 * (largo + ancho)
        
        num_banos = 1
        match_banos = re.search(r'(\d+)\s*baño', reqs)
        if match_banos:
            num_banos = int(match_banos.group(1))
            
        area_ceramica_bano = num_banos * 17.7
        num_columnas = max(4, math.ceil(area_base / 9.0))
        
        resultados = []
        
        # 1. Obras Preliminares (E-1)
        resultados.append({"elemento": "Limpieza de terreno a mano", "sugerencia_partida_codigo": "E-111.111.000", "cantidad": round(area_base * 1.2, 2), "unidad": "m2", "confianza": 0.99})
        resultados.append({"elemento": "Topografía y replanteo", "sugerencia_partida_codigo": "E-112.111.000", "cantidad": round(area_base * 1.2, 2), "unidad": "m2", "confianza": 0.99})
        if area_base > 50:
            resultados.append({"elemento": "Construcción de campamento", "sugerencia_partida_codigo": "E-113.111.000", "cantidad": 15.00, "unidad": "m2", "confianza": 0.95})
            
        # 2. Movimiento de Tierra (E-2)
        vol_excavacion = (num_columnas * 1.0 * 1.0 * 1.0) + (perimetro * 0.4 * 0.8)
        if area_base > 50 or "maquinaria" in reqs:
            resultados.append({"elemento": "Excavación con maquinaria", "sugerencia_partida_codigo": "E-211.111.000", "cantidad": round(vol_excavacion, 2), "unidad": "m3", "confianza": 0.98})
        else:
            resultados.append({"elemento": "Excavación manual", "sugerencia_partida_codigo": "E-311.110.150", "cantidad": round(vol_excavacion, 2), "unidad": "m3", "confianza": 0.95})
            
        vol_relleno = vol_excavacion * 0.30
        vol_bote = vol_excavacion * 1.20
        resultados.append({"elemento": "Relleno compactado", "sugerencia_partida_codigo": "E-213.111.000", "cantidad": round(vol_relleno, 2), "unidad": "m3", "confianza": 0.95})
        resultados.append({"elemento": "Carga y bote de material", "sugerencia_partida_codigo": "E-212.111.000", "cantidad": round(vol_bote, 2), "unidad": "m3", "confianza": 0.95})
        
        # 3. Estructuras (E-3)
        vol_fundaciones = num_columnas * 1.0 * 1.0 * 0.30
        vol_riostras = perimetro * 0.30 * 0.40
        resultados.append({"elemento": "Concreto fundaciones f'c=250", "sugerencia_partida_codigo": "E-322.019.000", "cantidad": round(vol_fundaciones + vol_riostras, 2), "unidad": "m3", "confianza": 0.98})
        
        vol_columnas = num_columnas * 0.30 * 0.30 * alto
        vol_vigas = perimetro * 0.25 * 0.30
        resultados.append({"elemento": "Concreto vigas y col. f'c=250", "sugerencia_partida_codigo": "C-512.200.100", "cantidad": round(vol_columnas + vol_vigas, 2), "unidad": "m3", "confianza": 0.98})
        
        kg_acero = (vol_fundaciones + vol_riostras + vol_columnas + vol_vigas) * 110
        resultados.append({"elemento": "Acero de refuerzo estructural", "sugerencia_partida_codigo": "E-331.019.000", "cantidad": round(kg_acero, 2), "unidad": "kg", "confianza": 0.99})
        
        area_encofrado = (num_columnas * 1.2 * alto) + (perimetro * 0.6)
        resultados.append({"elemento": "Encofrado de madera", "sugerencia_partida_codigo": "E-351.111.005", "cantidad": round(area_encofrado, 2), "unidad": "m2", "confianza": 0.95})
        
        area_techo = (largo + 0.40) * (ancho + 0.40)
        resultados.append({"elemento": "Malla Electrosoldada", "sugerencia_partida_codigo": "E-341.111.017", "cantidad": round(area_techo + area_base, 2), "unidad": "m2", "confianza": 0.95})
        
        if "nervada" in reqs:
            resultados.append({"elemento": "Concreto Losa Nervada f'c=250", "sugerencia_partida_codigo": "E-321.019.000", "cantidad": round(area_techo * 0.15, 2), "unidad": "m3", "confianza": 0.95})
        elif "metalica" in reqs or "metálica" in reqs:
            resultados.append({"elemento": "Estructura Metálica", "sugerencia_partida_codigo": "E-361.111.000", "cantidad": round(area_techo * 15, 2), "unidad": "kg", "confianza": 0.95})
        
        # 4. Arquitectura (E-4)
        area_paredes = perimetro * alto
        if "concreto" in reqs and "bloque" in reqs:
            resultados.append({"elemento": "Paredes de bloque concreto", "sugerencia_partida_codigo": "E-412.111.000", "cantidad": round(area_paredes, 2), "unidad": "m2", "confianza": 0.95})
        else:
            resultados.append({"elemento": "Paredes de bloque arcilla", "sugerencia_partida_codigo": "E-411.111.000", "cantidad": round(area_paredes, 2), "unidad": "m2", "confianza": 0.95})
            
        resultados.append({"elemento": "Revestimiento int. (Friso liso)", "sugerencia_partida_codigo": "E-421.111.000", "cantidad": round(area_paredes, 2), "unidad": "m2", "confianza": 0.98})
        resultados.append({"elemento": "Revestimiento ext. (Friso rústico)", "sugerencia_partida_codigo": "E-422.111.000", "cantidad": round(area_paredes, 2), "unidad": "m2", "confianza": 0.98})
        
        if "porcelanato" in reqs:
            resultados.append({"elemento": "Piso Porcelanato", "sugerencia_partida_codigo": "E-432.111.000", "cantidad": round(area_base, 2), "unidad": "m2", "confianza": 0.95})
        else:
            resultados.append({"elemento": "Piso Cerámica", "sugerencia_partida_codigo": "E-431.111.000", "cantidad": round(area_base, 2), "unidad": "m2", "confianza": 0.95})
            
        resultados.append({"elemento": "Ventanas panorámicas", "sugerencia_partida_codigo": "E-441.111.000", "cantidad": round(area_paredes * 0.15, 2), "unidad": "m2", "confianza": 0.90})
        
        if "nervada" not in reqs and "losa" not in reqs:
            resultados.append({"elemento": "Techo Acerolit / Zinc", "sugerencia_partida_codigo": "E-442.111.111", "cantidad": round(area_techo, 2), "unidad": "m2", "confianza": 0.90})
        else:
            resultados.append({"elemento": "Impermeabilización manto asfáltico", "sugerencia_partida_codigo": "E-443.111.000", "cantidad": round(area_techo, 2), "unidad": "m2", "confianza": 0.98})
            
        resultados.append({"elemento": "Pintura de caucho interiores", "sugerencia_partida_codigo": "E-451.111.000", "cantidad": round(area_paredes, 2), "unidad": "m2", "confianza": 0.98})
        
        # 5. Eléctricas (E-5)
        puntos_elec = max(4, round(area_base / 5))
        resultados.append({"elemento": "Tubería EMT 1/2 pulgada", "sugerencia_partida_codigo": "E-511.111.000", "cantidad": round(puntos_elec * 4, 2), "unidad": "m", "confianza": 0.95})
        resultados.append({"elemento": "Cableado TW #12", "sugerencia_partida_codigo": "E-512.111.000", "cantidad": round(puntos_elec * 12, 2), "unidad": "m", "confianza": 0.95})
        resultados.append({"elemento": "Puntos de Iluminación", "sugerencia_partida_codigo": "E-513.111.000", "cantidad": round(puntos_elec / 2), "unidad": "pto", "confianza": 0.95})
        resultados.append({"elemento": "Puntos de Tomacorriente", "sugerencia_partida_codigo": "E-514.111.000", "cantidad": round(puntos_elec / 2), "unidad": "pto", "confianza": 0.95})
        resultados.append({"elemento": "Tablero de distribución", "sugerencia_partida_codigo": "E-515.111.000", "cantidad": 1, "unidad": "und", "confianza": 0.99})
        resultados.append({"elemento": "Lámpara LED panel", "sugerencia_partida_codigo": "E-516.111.000", "cantidad": round(puntos_elec / 2), "unidad": "und", "confianza": 0.95})
        
        # 6. Sanitarias (E-6)
        resultados.append({"elemento": "Punto de aguas blancas 1/2\"", "sugerencia_partida_codigo": "E-611.111.111", "cantidad": num_banos * 3, "unidad": "pto", "confianza": 0.95})
        resultados.append({"elemento": "Punto de aguas servidas (poceta)", "sugerencia_partida_codigo": "E-621.111.112", "cantidad": num_banos, "unidad": "pto", "confianza": 0.95})
        resultados.append({"elemento": "Punto de aguas servidas 2\"", "sugerencia_partida_codigo": "E-621.111.111", "cantidad": num_banos * 2, "unidad": "pto", "confianza": 0.95})
        resultados.append({"elemento": "Inodoro (Poceta)", "sugerencia_partida_codigo": "E-631.111.111", "cantidad": num_banos, "unidad": "und", "confianza": 0.99})
        resultados.append({"elemento": "Lavamanos con pedestal", "sugerencia_partida_codigo": "E-632.111.111", "cantidad": num_banos, "unidad": "und", "confianza": 0.99})
        resultados.append({"elemento": "Ducha c/ grifería", "sugerencia_partida_codigo": "E-633.111.111", "cantidad": num_banos, "unidad": "und", "confianza": 0.99})
        resultados.append({"elemento": "Tanque de agua aéreo", "sugerencia_partida_codigo": "E-641.111.000", "cantidad": 1, "unidad": "und", "confianza": 0.95})
        
        # 7. Mecánicas (E-8)
        if "aire" in reqs or "acondicionado" in reqs or "split" in reqs or area_base > 20:
            num_splits = max(1, math.floor(area_base / 25))
            resultados.append({"elemento": "Aire Acondicionado Split 12000 BTU", "sugerencia_partida_codigo": "E-811.111.000", "cantidad": num_splits, "unidad": "und", "confianza": 0.95})
            resultados.append({"elemento": "Canalización tubería cobre", "sugerencia_partida_codigo": "E-812.111.000", "cantidad": num_splits * 5, "unidad": "m", "confianza": 0.95})
            resultados.append({"elemento": "Extractor de baño", "sugerencia_partida_codigo": "E-813.111.000", "cantidad": num_banos, "unidad": "und", "confianza": 0.95})
            
        # 8. ISO 9001
        resultados.append({"elemento": "Plan de Calidad en Obra (ISO 9001)", "sugerencia_partida_codigo": "I-9001.01.000", "cantidad": 1, "unidad": "glb", "confianza": 0.99})
        resultados.append({"elemento": "Auditoría de Control de Calidad", "sugerencia_partida_codigo": "I-9001.02.000", "cantidad": 1, "unidad": "glb", "confianza": 0.99})
        resultados.append({"elemento": "Supervisión de Seguridad (SSO)", "sugerencia_partida_codigo": "I-9001.03.000", "cantidad": 1, "unidad": "glb", "confianza": 0.99})
        
        return resultados

    def _analizar_con_gemini(self, ruta_imagen, largo, ancho, alto, requerimientos_cliente=""):
        # Leemos la imagen en base64
        with open(ruta_imagen, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        prompt = f'''
Actúa como un Ingeniero Civil Senior experto en Costos, Presupuestos y Cómputos Métricos, especializado en normas COVENIN de construcción de edificaciones en Venezuela. Tu objetivo es realizar un análisis visual exhaustivo del plano/render e imágenes proporcionadas y generar un presupuesto EXTREMADAMENTE DETALLADO, minucioso e integral de la obra, sin globalizar partidas. Debe abarcar todas las etapas necesarias para entregar la obra terminada y funcional.

Dimensiones proporcionadas: Largo {largo}m, Ancho {ancho}m, Alto {alto}m.
Requerimientos especiales del cliente: {requerimientos_cliente}

Debes desglosar minuciosamente y de forma obligatoria partidas detalladas para cada una de las siguientes etapas:
1. OBRAS PRELIMINARES: Instalaciones provisionales (depósito, oficina), deforestación, limpieza de terreno, replanteo de edificaciones y replanteo de zanjas.
2. MOVIMIENTO DE TIERRA: Excavaciones para zapatas a mano/máquina, excavación para vigas de riostra, carga a máquina/mano de escombros, bote y transporte de tierra sobrante, relleno compactado con material de préstamo (granzón) o material propio.
3. CONCRETO ARMADO (Infraestructura y Superestructura por separado): Concreto f'c=250 kg/cm2 (o el especificado) para zapatas, pedestales, vigas de riostra, columnas, vigas de carga, vigas de corona, losas macizas o losas nervadas, escaleras, dinteles y machones. Acero de refuerzo (cabillas de diferentes diámetros) en infraestructura, acero de refuerzo en superestructura. Encofrados de madera correspondientes para cada uno de estos elementos por separado (encofrado de zapatas, pedestales, columnas, vigas, losas). Malla electrosoldada para losas de piso.
4. ARQUITECTURA / ALBAÑILERÍA: Paredes de bloques de arcilla o concreto (e=15cm y e=10cm), frisado base (rústico), friso liso en interiores y friso liso con mortero impermeable en exteriores, empaste o pasta profesional en interiores.
5. ACABADOS Y REVESTIMIENTOS: Revestimiento de pisos con cerámica o porcelanato, rodapiés, revestimiento de paredes en baños/cocina con cerámica, pintura caucho/elastomérica en interiores y exteriores, pintura en esmalte para marcos y puertas de metal.
6. CARPINTERÍA Y HERRERÍA: Puertas de madera entamboradas y macizas, marcos de chapa metálica para puertas, ventanas de aluminio/vidrio (corredizas y panorámicas), rejas de protección y puertas de seguridad metálicas, cerraduras de pomo y de seguridad, bisagras.
7. INSTALACIONES ELÉCTRICAS: Salidas de iluminación (puntos de luz), tomacorrientes (110V y 220V especiales), apagadores, tuberías (EMT o PVC), cableado (calibres #12, #10 y acometida principal #6), tableros de distribución con sus breakers, y sistema de puesta a tierra.
8. INSTALACIONES SANITARIAS: Puntos de aguas blancas (PVC o termofusión), tuberías principales de aguas servidas (PVC 2" y 4"), piezas sanitarias (pocetas, lavamanos, duchas, fregaderos, bateas) con sus griferías y conexiones, tanque de agua plástico y bomba hidroneumática.
9. TRANSPORTE Y OTROS: Fletes, transporte de escombros, limpieza final de la obra.

Instrucción de granularidad y unidades críticas: 
- NO resumas ni agrupes partidas en conceptos globales (ej. no pongas "Instalaciones sanitarias" en una sola partida, desglosa los puntos, tuberías y cada pieza por separado. No pongas "Estructura de concreto" en una sola partida, sepáralo en zapatas, columnas, losas, encofrados respectivos y acero de refuerzo respectivo).
- Si sugieres partidas de estructura metálica o de acero (como escaleras metálicas exteriores tipo caracol, vigas de acero estructural, rejas de ventanas, etc.), ten en cuenta que en la norma COVENIN estas partidas se miden en kilogramos (kg). Por lo tanto, debes calcular y estimar el peso aproximado en kg (por ejemplo, una escalera tipo caracol exterior de acero de h=2.80m a 3.00m pesa típicamente entre 250 kg y 380 kg; barandas metálicas estimar a razón de 15 kg por metro lineal). Indica siempre la cantidad como el peso en kg y la unidad como 'kg' para que el costo del presupuesto se calcule de forma real y profesional.
- El presupuesto final debe tener entre 50 y 90 partidas detalladas de calidad profesional, con cómputos métricos calculados rigurosamente de acuerdo a las dimensiones y plano.

IMPORTANTE PARA LA INTEGRACION DEL SISTEMA: 
Devuelve UNICAMENTE un objeto JSON válido. El sistema fallará si incluyes formato Markdown como ```json o texto fuera del objeto.
Estructura exacta:
{{
  "hallazgos": "Breve resumen de lo que detectaste visualmente",
  "memoria_calculo": "Desglose matemático de áreas y volúmenes",
  "resultados": [
    {{
      "elemento": "Descripción Técnica de la Partida",
      "sugerencia_partida_codigo": "Código COVENIN sugerido (ej: E-311.111.000)",
      "cantidad": 12.5,
      "unidad": "m3",
      "confianza": 0.95
    }}
  ]
}}
'''
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_string
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        max_retries = 3
        retry_delay = 1.5
        response_data = None
        
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                break
            except urllib.error.HTTPError as he:
                if (he.code == 429 or he.code >= 500) and attempt < max_retries - 1:
                    print(f"Error HTTP {he.code} de Gemini en intento {attempt+1}, reintentando en {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise he
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error de conexion con Gemini en intento {attempt+1}, reintentando en {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise e
                
        text_response = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # Guardar la respuesta cruda para depuración
        scratch_dir = "C:/Users/Usuario/.gemini/antigravity/brain/ca39617d-4cc2-40f7-94b8-d510bdfaddd9/scratch"
        os.makedirs(scratch_dir, exist_ok=True)
        with open(os.path.join(scratch_dir, "gemini_response.json"), "w", encoding="utf-8") as f:
            f.write(text_response)
        
        # Limpiar posible markdown
        text_response = text_response.strip()
        if text_response.startswith('```json'):
            text_response = text_response[7:]
        elif text_response.startswith('`json'):
            text_response = text_response[5:]
        if text_response.startswith('```'):
            text_response = text_response[3:]
        if text_response.startswith('`'):
            text_response = text_response[1:]
        if text_response.endswith('```'):
            text_response = text_response[:-3]
        elif text_response.endswith('`'):
            text_response = text_response[:-1]
            
        json_parsed = json.loads(text_response.strip())
        
        return json_parsed.get("resultados", [])




