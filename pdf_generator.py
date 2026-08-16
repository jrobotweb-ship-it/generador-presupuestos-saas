import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from PIL import Image as PILImage

def generar_pdf_presupuesto(nombre_archivo, datos_cliente, items, tasa_bcv, total_usd, total_ves, ruta_imagen=None, bom_items=None, datos_profesional=None):
    logo_temp_path = None
    logo_reportlab_img = None
    if datos_profesional and datos_profesional.get("logo_base64"):
        try:
            import base64
            logo_data = datos_profesional.get("logo_base64")
            if "," in logo_data:
                logo_data = logo_data.split(",")[1]
            img_bytes = base64.b64decode(logo_data)
            logo_temp_path = os.path.join(os.path.dirname(nombre_archivo), f"temp_logo_pres_{os.getpid()}.png")
            with open(logo_temp_path, "wb") as f:
                f.write(img_bytes)
            logo_reportlab_img = Image(logo_temp_path, width=50, height=50)
        except Exception as le:
            print("Error decodificando el logo para presupuesto:", le)
    """
    Genera un documento PDF profesional con el presupuesto detallado.
    
    :param nombre_archivo: Ruta donde se guardará el PDF.
    :param datos_cliente: Dict con 'nombre', 'telefono', 'ubicacion', 'fecha', 'proyecto'.
    :param items: Lista de dicts con partidas (codigo, descripcion, unidad, cantidad, precio_usd).
    :param tasa_bcv: Valor numérico de la tasa de cambio BCV.
    :param total_usd: Total general en USD.
    :param total_ves: Total general en VES.
    :param ruta_imagen: Ruta local de la imagen/render del proyecto (opcional).
    :param bom_items: Dict con los materiales consolidados (Bill of Materials) opcional.
    :return: True si se generó con éxito, False en caso contrario.
    """
    try:
        # 1. Configuración del documento (Márgenes de 0.5 pulgadas para aprovechar espacio)
        doc = SimpleDocTemplate(
            nombre_archivo,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        story = []
        
        # 2. Estilos personalizados
        styles = getSampleStyleSheet()
        
        # Paleta de colores premium
        color_primario = colors.HexColor("#1A365D")  # Azul Naval Oscuro
        color_secundario = colors.HexColor("#2B6CB0")  # Azul Acero
        color_texto_oscuro = colors.HexColor("#2D3748")  # Gris Carbón
        color_linea = colors.HexColor("#E2E8F0")  # Gris Claro para líneas
        
        # Estilos de párrafo
        style_titulo = ParagraphStyle(
            name='TituloPresupuesto',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=color_primario,
            alignment=TA_LEFT,
            spaceAfter=15
        )
        
        style_subtitulo = ParagraphStyle(
            name='SubtituloPresupuesto',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            textColor=color_secundario,
            spaceAfter=5
        )
        
        style_cuerpo = ParagraphStyle(
            name='CuerpoPresupuesto',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=color_texto_oscuro
        )
        
        style_cuerpo_bold = ParagraphStyle(
            name='CuerpoPresupuestoBold',
            parent=style_cuerpo,
            fontName='Helvetica-Bold'
        )

        style_tabla_header = ParagraphStyle(
            name='TablaHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=TA_CENTER
        )
        
        style_tabla_celda = ParagraphStyle(
            name='TablaCelda',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=10.5,
            textColor=color_texto_oscuro
        )
        
        style_tabla_celda_centro = ParagraphStyle(
            name='TablaCeldaCentro',
            parent=style_tabla_celda,
            alignment=TA_CENTER
        )

        style_tabla_celda_derecha = ParagraphStyle(
            name='TablaCeldaDerecha',
            parent=style_tabla_celda,
            alignment=TA_RIGHT
        )
        
        style_tabla_celda_derecha_bold = ParagraphStyle(
            name='TablaCeldaDerechaBold',
            parent=style_tabla_celda_derecha,
            fontName='Helvetica-Bold'
        )

        # 3. Encabezado de la Empresa / Título
        # Crear un layout de tres columnas para el encabezado (Logo/Empresa, Título de Obra, Cotización)
        empresa_info = []
        if logo_reportlab_img:
            # Centrar y dimensionar el logo
            logo_table_wrapper = Table([[logo_reportlab_img]], colWidths=[60])
            logo_table_wrapper.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            empresa_info.append(logo_table_wrapper)
            empresa_info.append(Spacer(1, 4))
            
        empresa_nombre = datos_profesional.get('empresa', 'CONSTRUCCIONES JROBOTWEB') if datos_profesional else 'CONSTRUCCIONES JROBOTWEB'
        empresa_info.append(Paragraph(f"<b>{empresa_nombre.upper()}</b>", style_subtitulo))
        
        if datos_profesional and datos_profesional.get('profesional'):
            empresa_info.append(Paragraph(datos_profesional.get('profesional'), style_cuerpo))
            
        encabezado_izq = [
            Paragraph("PRESUPUESTO DE OBRA", style_titulo),
            Paragraph(f"<b>Proyecto:</b> {datos_cliente.get('proyecto', 'Remodelación / Construcción General')}", style_cuerpo),
            Paragraph(f"<b>Fecha de Emisión:</b> {datos_cliente.get('fecha', '')}", style_cuerpo),
        ]
        
        encabezado_der = [
            Paragraph("<b>DOCUMENTO DE COTIZACIÓN</b>", style_subtitulo),
            Paragraph("<b>Validez:</b> 15 días a partir de la fecha", style_cuerpo),
            Paragraph(f"<b>Tasa de Cambio BCV:</b> Bs. {tasa_bcv:.2f}", style_cuerpo_bold),
        ]
        
        tabla_encabezado_data = [
            [empresa_info, encabezado_izq, encabezado_der]
        ]
        
        tabla_encabezado = Table(tabla_encabezado_data, colWidths=[165, 225, 150])
        tabla_encabezado.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(tabla_encabezado)
        
        # Línea divisoria
        tabla_linea = Table([[""]], colWidths=[540], rowHeights=[2])
        tabla_linea.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1, color_primario),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(tabla_linea)
        story.append(Spacer(1, 10))
        
        # 4. Datos del Cliente y Ubicación
        datos_cliente_izq = [
            Paragraph("<b>DATOS DEL CLIENTE</b>", style_subtitulo),
            Paragraph(f"<b>Cliente / Razón Social:</b> {datos_cliente.get('nombre', 'N/D')}", style_cuerpo),
            Paragraph(f"<b>Teléfono / Contacto:</b> {datos_cliente.get('telefono', 'N/D')}", style_cuerpo),
        ]
        
        datos_cliente_der = [
            Paragraph("<b>UBICACIÓN DE LA OBRA</b>", style_subtitulo),
            Paragraph(f"<b>Dirección:</b> {datos_cliente.get('ubicacion', 'N/D')}", style_cuerpo),
        ]
        
        tabla_cliente_data = [
            [datos_cliente_izq, datos_cliente_der]
        ]
        
        tabla_cliente = Table(tabla_cliente_data, colWidths=[270, 270])
        tabla_cliente.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(tabla_cliente)
        
        # 5. Insertar Imagen/Render (si existe y es válida)
        if ruta_imagen and os.path.exists(ruta_imagen):
            try:
                # Leer dimensiones con PIL para escalar manteniendo relación de aspecto
                with PILImage.open(ruta_imagen) as img_pil:
                    ancho_orig, alto_orig = img_pil.size
                
                # Definir ancho objetivo (ej: 540 puntos, que cubre todo el ancho de página)
                ancho_pdf = 540
                alto_pdf = int((ancho_pdf * alto_orig) / ancho_orig)
                
                # Limitar altura máxima para que no tome toda la hoja
                if alto_pdf > 220:
                    alto_pdf = 220
                    ancho_pdf = int((alto_pdf * ancho_orig) / alto_orig)
                
                img_reportlab = Image(ruta_imagen, width=ancho_pdf, height=alto_pdf)
                img_reportlab.hAlign = 'CENTER'
                
                # Colocar la imagen en una cajita con borde sutil para que luzca muy premium
                tabla_img_wrapper = Table([[img_reportlab]], colWidths=[540])
                tabla_img_wrapper.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOX', (0,0), (-1,-1), 0.5, color_linea),
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ]))
                
                story.append(Paragraph("<b>REPRESENTACIÓN VISUAL DEL PROYECTO</b>", style_subtitulo))
                story.append(Spacer(1, 4))
                story.append(tabla_img_wrapper)
                story.append(Spacer(1, 15))
            except Exception as ex_img:
                print(f"No se pudo renderizar la imagen en el PDF: {ex_img}")
                
        # 6. Tabla de Partidas
        # Encabezados
        cabeceras = [
            Paragraph("Item", style_tabla_header),
            Paragraph("Descripción de la Partida", style_tabla_header),
            Paragraph("Unidad", style_tabla_header),
            Paragraph("Cant.", style_tabla_header),
            Paragraph("P. Unit. (USD)", style_tabla_header),
            Paragraph("Total (USD)", style_tabla_header),
            Paragraph("Total (VES)", style_tabla_header)
        ]
        
        tabla_partidas_data = [cabeceras]
        
        # Filas de datos
        for idx, item in enumerate(items):
            sub_usd = item["cantidad"] * item["precio_usd"]
            sub_ves = sub_usd * tasa_bcv
            
            # Formatear celdas con párrafos para soportar multilínea y estilos correctos
            fila = [
                Paragraph(item["codigo"], style_tabla_celda_centro),
                Paragraph(item["descripcion"], style_tabla_celda),
                Paragraph(item["unidad"], style_tabla_celda_centro),
                Paragraph(f"{item['cantidad']:.2f}", style_tabla_celda_centro),
                Paragraph(f"${item['precio_usd']:.2f}", style_tabla_celda_derecha),
                Paragraph(f"${sub_usd:.2f}", style_tabla_celda_derecha_bold),
                Paragraph(f"Bs. {sub_ves:.2f}", style_tabla_celda_derecha)
            ]
            tabla_partidas_data.append(fila)
            
        # Column widths: Total de 540 puntos de ancho
        # Item=75, Desc=205, Unidad=40, Cant=40, P.Unit=60, TotalUSD=60, TotalVES=60
        anchos_columnas = [75, 205, 40, 40, 60, 60, 60]
        
        tabla_partidas = Table(tabla_partidas_data, colWidths=anchos_columnas, repeatRows=1)
        
        # Estilos de la tabla
        estilo_tabla = TableStyle([
            # Encabezado
            ('BACKGROUND', (0,0), (-1,0), color_primario),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            # Cuadrícula
            ('GRID', (0,0), (-1,-1), 0.5, color_linea),
            ('VALIGN', (0,1), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,1), (-1,-1), 5),
            ('BOTTOMPADDING', (0,1), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ])
        
        # Filas alternas
        for i in range(1, len(tabla_partidas_data)):
            if i % 2 == 0:
                estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F7FAFC"))
                
        tabla_partidas.setStyle(estilo_tabla)
        story.append(tabla_partidas)
        story.append(Spacer(1, 15))
        
        # 7. Resumen de Totales Destacado
        totales_izq = [
            Paragraph("<b>CONDICIONES COMERCIALES</b>", style_subtitulo),
            Paragraph("• Los precios están expresados en Dólares Americanos (USD).", style_cuerpo),
            Paragraph("• Pagos en Bolívares (VES) serán calculados a la tasa oficial del BCV vigente al momento del pago.", style_cuerpo),
            Paragraph("• Esta cotización no incluye impuestos de ley a menos que se especifique lo contrario.", style_cuerpo),
        ]
        
        totales_der = [
            Table([
                [Paragraph("<b>SUBTOTAL (USD):</b>", style_tabla_celda_derecha), Paragraph(f"<b>${total_usd:,.2f}</b>", style_tabla_celda_derecha)],
                [Paragraph("<b>IVA (0%):</b>", style_tabla_celda_derecha), Paragraph("$0.00", style_tabla_celda_derecha)],
                [Paragraph("<font color='#1A365D'><b>TOTAL GENERAL (USD):</b></font>", style_tabla_celda_derecha), Paragraph(f"<font color='#1A365D'><b>${total_usd:,.2f}</b></font>", style_tabla_celda_derecha_bold)],
                [Paragraph("<font color='#2B6CB0'><b>TOTAL GENERAL (VES):</b></font>", style_tabla_celda_derecha), Paragraph(f"<font color='#2B6CB0'><b>Bs. {total_ves:,.2f}</b></font>", style_tabla_celda_derecha_bold)]
            ], colWidths=[130, 110])
        ]
        
        # Estilo para la tabla interna de totales (sin bordes)
        totales_der[0].setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEABOVE', (0,2), (1,2), 1, color_primario), # Línea sobre el total USD
        ]))
        
        tabla_totales_seccion = Table([[totales_izq, totales_der]], colWidths=[300, 240])
        tabla_totales_seccion.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 20),
        ]))
        story.append(tabla_totales_seccion)
        
        # 8. Firmas de Aprobación (Mantener juntas al final del documento)
        firma_cliente = [
            Spacer(1, 40),
            Table([[""]], colWidths=[180], rowHeights=[1]),
            Paragraph("Aceptado por el Cliente (Firma / Sello)", style_tabla_celda_centro),
            Paragraph("Nombre: ________________________", style_tabla_celda_centro),
            Paragraph("C.I. / R.I.F.: ___________________", style_tabla_celda_centro),
        ]
        
        firma_nom = datos_profesional.get("profesional", "Firma Autorizada (Emisor)") if datos_profesional else "Firma Autorizada (Emisor)"
        firma_sub = datos_profesional.get("empresa", "CONSTRUCCIONES JROBOTWEB") if datos_profesional else "CONSTRUCCIONES JROBOTWEB"
        # Sin CIV
            
        firma_empresa = [
            Spacer(1, 40),
            Table([[""]], colWidths=[180], rowHeights=[1]),
            Paragraph(f"<b>{firma_nom.upper()}</b>", style_tabla_celda_centro),
            Paragraph(firma_sub, style_tabla_celda_centro),
        ]
        
        # Añadir estilos a las líneas de firma
        firma_cliente[1].setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.5, color_texto_oscuro)]))
        firma_empresa[1].setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.5, color_texto_oscuro)]))
        
        tabla_firmas = Table([[firma_cliente, "", firma_empresa]], colWidths=[220, 100, 220])
        tabla_firmas.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Usamos KeepTogether para asegurar que las firmas no queden huérfanas en una página separada
        story.append(KeepTogether(tabla_firmas))
        
        # 9. Lista de Materiales (BoM) en Nueva Página (Si Aplica)
        if bom_items and len(bom_items) > 0:
            story.append(PageBreak())
            story.append(Paragraph("LISTA DE COMPRAS (BILL OF MATERIALS)", style_titulo))
            story.append(Paragraph("Resumen consolidado de materiales e insumos necesarios para la ejecución del proyecto.", style_cuerpo))
            story.append(Spacer(1, 15))

            cabeceras_bom = [
                Paragraph("Código", style_tabla_header),
                Paragraph("Descripción del Material", style_tabla_header),
                Paragraph("Und.", style_tabla_header),
                Paragraph("Total a Comprar", style_tabla_header)
            ]
            
            tabla_bom_data = [cabeceras_bom]
            
            for cod, datos in bom_items.items():
                fila_bom = [
                    Paragraph(cod, style_tabla_celda_centro),
                    Paragraph(datos["descripcion"], style_tabla_celda),
                    Paragraph(datos["unidad"], style_tabla_celda_centro),
                    Paragraph(f"{datos['cantidad']:.2f}", style_tabla_celda_centro)
                ]
                tabla_bom_data.append(fila_bom)
                
            anchos_bom = [100, 300, 60, 80]
            tabla_bom = Table(tabla_bom_data, colWidths=anchos_bom, repeatRows=1)
            
            estilo_bom = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), color_secundario),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('TOPPADDING', (0,0), (-1,0), 6),
                ('GRID', (0,0), (-1,-1), 0.5, color_linea),
                ('VALIGN', (0,1), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,1), (-1,-1), 5),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ])
            
            for i in range(1, len(tabla_bom_data)):
                if i % 2 == 0:
                    estilo_bom.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F7FAFC"))
                    
            tabla_bom.setStyle(estilo_bom)
            story.append(tabla_bom)

        # 10. Construir el PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error crítico al generar PDF: {e}")
        return False
    finally:
        if logo_temp_path and os.path.exists(logo_temp_path):
            try:
                os.remove(logo_temp_path)
            except Exception:
                pass

# Prueba rápida de generación de PDF si se ejecuta de forma aislada
if __name__ == "__main__":
    datos_prueba = {
        "nombre": "Juan Pérez",
        "telefono": "+58 412-1234567",
        "ubicacion": "Av. Francisco de Miranda, Caracas",
        "proyecto": "Remodelación de Cocina Moderna",
        "fecha": "26/06/2026"
    }
    items_prueba = [
        {"codigo": "E-311.110.150", "descripcion": "Excavación a mano para asiento de fundaciones, zanjas o trincheras", "unidad": "m³", "cantidad": 5.5, "precio_usd": 18.50},
        {"codigo": "C-512.200.100", "descripcion": "Concreto de f'c = 250 kgf/cm² a los 28 días para vigas y columnas", "unidad": "m³", "cantidad": 2.0, "precio_usd": 125.00},
        {"codigo": "M-411.100.120", "descripcion": "Construcción de paredes de bloques de arcilla de 15 cm de espesor", "unidad": "m²", "cantidad": 25.0, "precio_usd": 24.00}
    ]
    tasa = 36.50
    sub_usd = sum(i["cantidad"] * i["precio_usd"] for i in items_prueba)
    sub_ves = sub_usd * tasa
    
    print("Generando PDF de prueba...")
    exito = generar_pdf_presupuesto("presupuesto_prueba.pdf", datos_prueba, items_prueba, tasa, sub_usd, sub_ves)
    if exito:
        print("PDF de prueba generado con éxito como 'presupuesto_prueba.pdf'.")
    else:
        print("Error al generar el PDF de prueba.")

def generar_pdf_memoria(nombre_archivo, datos_cliente, parametros):
    try:
        doc = SimpleDocTemplate(
            nombre_archivo,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        color_primario = colors.HexColor("#1A365D")
        color_secundario = colors.HexColor("#2B6CB0")
        color_texto_oscuro = colors.HexColor("#2D3748")
        
        style_titulo = ParagraphStyle(
            name='TituloMemoria',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=color_primario,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        style_subtitulo = ParagraphStyle(
            name='SubtituloMemoria',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=color_secundario,
            spaceAfter=10,
            spaceBefore=15
        )
        
        style_cuerpo = ParagraphStyle(
            name='CuerpoMemoria',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=color_texto_oscuro,
            spaceAfter=8
        )
        
        story.append(Paragraph("MEMORIA DESCRIPTIVA DEL PROYECTO", style_titulo))
        
        story.append(Paragraph("1. Datos Generales del Proyecto", style_subtitulo))
        story.append(Paragraph(f"<b>Cliente / Razón Social:</b> {datos_cliente.get('nombre', 'N/D')}", style_cuerpo))
        story.append(Paragraph(f"<b>Proyecto:</b> {datos_cliente.get('proyecto', 'N/D')}", style_cuerpo))
        story.append(Paragraph(f"<b>Ubicación:</b> {datos_cliente.get('ubicacion', 'N/D')}", style_cuerpo))
        story.append(Paragraph(f"<b>Fecha de Elaboración:</b> {datos_cliente.get('fecha', '')}", style_cuerpo))
        
        story.append(Paragraph("2. Parámetros Dimensionales", style_subtitulo))
        largo = parametros.get('largo', 0)
        ancho = parametros.get('ancho', 0)
        alto = parametros.get('alto', 0)
        story.append(Paragraph(f"<b>Largo:</b> {largo} m", style_cuerpo))
        story.append(Paragraph(f"<b>Ancho:</b> {ancho} m", style_cuerpo))
        story.append(Paragraph(f"<b>Alto:</b> {alto} m", style_cuerpo))
        area = float(largo or 0) * float(ancho or 0)
        story.append(Paragraph(f"<b>Área Estimada:</b> {area:.2f} m²", style_cuerpo))
        
        story.append(Paragraph("3. Requerimientos y Especificaciones del Cliente", style_subtitulo))
        reqs = parametros.get('requerimientos', '')
        if not reqs or not reqs.strip():
            reqs = 'Sin requerimientos especiales indicados.'
        story.append(Paragraph(reqs, style_cuerpo))
        
        story.append(Paragraph("4. Consideraciones del Sistema (IA)", style_subtitulo))
        story.append(Paragraph("El presente análisis de memoria descriptiva ha sido generado tomando como base las dimensiones aportadas y los requerimientos textuales del cliente, utilizando el motor de inferencia de partidas constructivas. Las cantidades de obra reflejadas en el presupuesto se derivan de las consideraciones volumétricas y de área aquí descritas, siguiendo los estándares y especificaciones técnicas de construcción vigentes.", style_cuerpo))
        
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar memoria: {e}")
        return False

