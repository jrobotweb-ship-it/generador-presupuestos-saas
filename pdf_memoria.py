import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

def generar_pdf_memoria(nombre_archivo, datos_memoria, datos_cliente, datos_profesional=None):
    logo_temp_path = None
    try:
        doc = SimpleDocTemplate(
            nombre_archivo,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        
        # Paleta de colores premium
        color_navy = colors.HexColor("#1A365D")
        color_blue = colors.HexColor("#2B6CB0")
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=color_navy,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=color_blue,
            alignment=TA_CENTER,
            spaceAfter=40
        )
        
        client_style = ParagraphStyle(
            'ClientStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=15,
            textColor=color_blue,
            spaceBefore=20,
            spaceAfter=10
        )
        
        partida_title_style = ParagraphStyle(
            'PartidaTitleStyle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor("#2C5282"),
            spaceBefore=15,
            spaceAfter=5
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=14
        )
        
        elements = []
        
        # --- PROCESAR LOGO DE LA EMPRESA ---
        logo_reportlab_img = None
        if datos_profesional and datos_profesional.get("logo_base64"):
            try:
                import base64
                logo_data = datos_profesional.get("logo_base64")
                if "," in logo_data:
                    logo_data = logo_data.split(",")[1]
                img_bytes = base64.b64decode(logo_data)
                logo_temp_path = os.path.join(os.path.dirname(nombre_archivo), f"temp_logo_mem_{os.getpid()}.png")
                with open(logo_temp_path, "wb") as f:
                    f.write(img_bytes)
                logo_reportlab_img = Image(logo_temp_path, width=80, height=80)
            except Exception as le:
                print("Error decodificando el logo para memoria:", le)
                
        # --- CARATULA ---
        elements.append(Spacer(1, 20))
        
        if logo_reportlab_img:
            # Centrar el logo usando una tabla de una celda
            logo_table = Table([[logo_reportlab_img]], colWidths=[100])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 20))
            
        logo_style = ParagraphStyle(
            'LogoStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.white,
            backColor=color_navy,
            alignment=TA_CENTER,
            spaceAfter=50,
            borderPadding=10
        )
        
        empresa_nombre = datos_profesional.get('empresa', 'CONSTRUCCIONES JROBOTWEB') if datos_profesional else 'CONSTRUCCIONES JROBOTWEB'
        elements.append(Paragraph(f"<b>{empresa_nombre.upper()}</b>", logo_style))
        elements.append(Spacer(1, 30))
        
        caratula = datos_memoria.get("caratula", {})
        elements.append(Paragraph(caratula.get("titulo", "Memoria Descriptiva Técnica"), title_style))
        elements.append(Paragraph(caratula.get("subtitulo", ""), subtitle_style))
        
        elements.append(Spacer(1, 50))
        elements.append(Paragraph(f"<b>CLIENTE:</b> {datos_cliente.get('nombre', '')}", client_style))
        elements.append(Paragraph(f"<b>PROYECTO:</b> {datos_cliente.get('proyecto', '')}", client_style))
        elements.append(Paragraph(f"<b>UBICACIÓN:</b> {datos_cliente.get('ubicacion', '')}", client_style))
        
        elements.append(PageBreak())
        
        # --- CONTENIDO ---
        elements.append(Paragraph("Introducción", heading_style))
        elements.append(Paragraph(datos_memoria.get("introduccion", ""), normal_style))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph("Especificaciones y Descripción Técnica de Partidas", heading_style))
        
        for partida in datos_memoria.get("partidas", []):
            p_elements = []
            p_elements.append(Paragraph(f"• {partida.get('nombre_original', 'Partida')}", partida_title_style))
            p_elements.append(Paragraph(f"<i>(Código: {partida.get('codigo', '')})</i>", ParagraphStyle('Code', parent=styles['Normal'], fontSize=8.5, textColor=colors.gray, spaceAfter=4)))
            
            explicacion = partida.get('explicacion_infantil', '')
            p_elements.append(Paragraph(explicacion, normal_style))
            
            elements.append(KeepTogether(p_elements))
            elements.append(Spacer(1, 6))
            
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Conclusión", heading_style))
        elements.append(Paragraph(datos_memoria.get("conclusion", ""), normal_style))
        
        # --- FIRMA DEL PROFESIONAL ---
        if datos_profesional and datos_profesional.get("profesional"):
            elements.append(Spacer(1, 45))
            firma_nom = datos_profesional.get("profesional", "")
            
            firma_table_data = [
                [""],
                [Paragraph("________________________________________", ParagraphStyle('Line', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.gray))],
                [Paragraph(f"<b>{firma_nom.upper()}</b>", ParagraphStyle('FirmaNom', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9.5, textColor=color_navy))],
                [Paragraph("Profesional Autorizado", ParagraphStyle('FirmaCiv', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8.5, textColor=colors.gray))]
            ]
            firma_table = Table(firma_table_data, colWidths=[280])
            firma_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            elements.append(KeepTogether(firma_table))
            
        doc.build(elements)
        return True
    except Exception as e:
        print(f"Error generando PDF Memoria: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpieza del logo temporal
        if logo_temp_path and os.path.exists(logo_temp_path):
            try:
                os.remove(logo_temp_path)
            except Exception:
                pass
