import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import database

def generar_pdf_apus(nombre_archivo, items_presupuesto, tasa_bcv, datos_profesional=None):
    logo_temp_path = None
    if datos_profesional and datos_profesional.get("logo_base64"):
        try:
            import base64
            logo_data = datos_profesional.get("logo_base64")
            if "," in logo_data:
                logo_data = logo_data.split(",")[1]
            img_bytes = base64.b64decode(logo_data)
            logo_temp_path = os.path.join(os.path.dirname(nombre_archivo), f"temp_logo_apu_{os.getpid()}.png")
            with open(logo_temp_path, "wb") as f:
                f.write(img_bytes)
        except Exception as le:
            print("Error decodificando el logo para APUs:", le)
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
        
        # Paleta de colores corporativos premium (a juego con pdf_generator.py)
        color_navy = colors.HexColor("#1A365D")
        color_blue = colors.HexColor("#2B6CB0")
        color_dark = colors.HexColor("#2D3748")
        color_light_gray = colors.HexColor("#F7FAFC")
        color_border = colors.HexColor("#E2E8F0")
        
        # Estilos de textos
        style_header_title = ParagraphStyle(
            name='ApuHeaderTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=16,
            textColor=color_navy,
            alignment=TA_CENTER
        )
        
        style_meta_label = ParagraphStyle(
            name='ApuMetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=color_dark
        )
        
        style_meta_val = ParagraphStyle(
            name='ApuMetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=color_dark
        )
        
        style_sec_title = ParagraphStyle(
            name='ApuSecTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=TA_LEFT
        )
        
        style_th = ParagraphStyle(
            name='ApuTableTh',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=color_navy,
            alignment=TA_CENTER
        )
        
        style_td = ParagraphStyle(
            name='ApuTableTd',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=9.5,
            textColor=color_dark
        )
        
        style_td_center = ParagraphStyle(
            name='ApuTableTdCenter',
            parent=style_td,
            alignment=TA_CENTER
        )
        
        style_td_right = ParagraphStyle(
            name='ApuTableTdRight',
            parent=style_td,
            alignment=TA_RIGHT
        )
        
        style_total_label = ParagraphStyle(
            name='ApuTotalLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=color_navy,
            alignment=TA_RIGHT
        )
        
        style_total_val = ParagraphStyle(
            name='ApuTotalVal',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=color_dark,
            alignment=TA_RIGHT
        )

        for index, item in enumerate(items_presupuesto):
            codigo = item.get("codigo")
            detalles = database.obtener_detalles_apu(codigo)
            if not detalles:
                # Si no se encuentra en el catálogo estructurado, crear un mock en base al precio unitario actual
                descripcion = item.get("descripcion", "Partida de Obra")
                unidad = item.get("unidad", "und")
                precio_usd = float(item.get("precio_usd") or 0.0)
                detalles = {
                    "codigo": codigo,
                    "descripcion": descripcion,
                    "unidad": unidad,
                    "rendimiento": 1.0,
                    "materiales": [
                        {
                            "codigo": f"MAT-{codigo}",
                            "descripcion": f"Material global e insumos para {descripcion}",
                            "unidad": unidad,
                            "cantidad": 1.0,
                            "precio_usd": precio_usd
                        }
                    ],
                    "equipos": [],
                    "mano_obra": []
                }
            
            rendimiento = detalles["rendimiento"] or 1.0
            
            # --- PAGINA INDIVIDUAL PARA CADA APU ---
            page_elements = []
            
            # Encabezado de la página
            logo_img_copy = None
            if logo_temp_path and os.path.exists(logo_temp_path):
                logo_img_copy = Image(logo_temp_path, width=30, height=30)
                
            empresa_txt = datos_profesional.get("empresa", "CONSTRUCCIONES JROBOTWEB") if datos_profesional else "CONSTRUCCIONES JROBOTWEB"
            prof_txt = datos_profesional.get("profesional", "") if datos_profesional else ""
            # Sin CIV
                
            col_empresa = []
            if logo_img_copy:
                # Centrar logo en una tablita
                logo_wrapper = Table([[logo_img_copy]], colWidths=[40])
                logo_wrapper.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
                col_empresa.append(logo_wrapper)
                col_empresa.append(Spacer(1, 2))
            col_empresa.append(Paragraph(f"<b>{empresa_txt.upper()}</b>", ParagraphStyle('ApuEmpStyle', parent=styles['Normal'], fontSize=7.5, leading=8.5, textColor=color_navy)))
            if prof_txt:
                col_empresa.append(Paragraph(prof_txt, ParagraphStyle('ApuProfStyle', parent=styles['Normal'], fontSize=6.5, leading=7.5, textColor=color_dark)))
                
            col_titulo = [Paragraph("<b>ANÁLISIS DE PRECIOS UNITARIOS</b>", style_header_title)]
            col_fecha = [Paragraph("<b>Documento Técnico</b><br/>Especificaciones Técnicas", ParagraphStyle('ApuFecStyle', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=TA_RIGHT, textColor=color_dark))]
            
            header_table = Table([[col_empresa, col_titulo, col_fecha]], colWidths=[170, 250, 120])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), color_light_gray),
                ('BOX', (0,0), (-1,-1), 0.5, color_navy),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            page_elements.append(header_table)
            page_elements.append(Spacer(1, 8))
            
            # Tabla de metadatos (Código, Descripción, Unidad, Rendimiento)
            meta_data = [
                [
                    Paragraph("<b>Código:</b>", style_meta_label),
                    Paragraph(detalles["codigo"], style_meta_val),
                    Paragraph("<b>Unidad:</b>", style_meta_label),
                    Paragraph(detalles["unidad"], style_meta_val),
                ],
                [
                    Paragraph("<b>Partida:</b>", style_meta_label),
                    Paragraph(detalles["descripcion"], style_meta_val),
                    Paragraph("<b>Rendimiento:</b>", style_meta_label),
                    Paragraph(f"{rendimiento:.2f} / Día", style_meta_val),
                ]
            ]
            meta_table = Table(meta_data, colWidths=[60, 260, 80, 140])
            meta_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LINEBELOW', (0,-1), (-1,-1), 0.5, color_border),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
            ]))
            page_elements.append(meta_table)
            page_elements.append(Spacer(1, 10))
            
            # --- SECCIÓN 1: MATERIALES ---
            page_elements.append(Table([[Paragraph("1. MATERIALES", style_sec_title)]], colWidths=[540], style=[
                ('BACKGROUND', (0,0), (-1,-1), color_navy),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            
            mats_data = [[
                Paragraph("Código", style_th),
                Paragraph("Descripción del Material", style_th),
                Paragraph("Unidad", style_th),
                Paragraph("Cantidad", style_th),
                Paragraph("Precio U. ($)", style_th),
                Paragraph("Costo U. ($)", style_th),
            ]]
            
            tot_mats = 0.0
            if detalles["materiales"]:
                for m in detalles["materiales"]:
                    cant = m["cantidad"]
                    pu = m["precio_usd"]
                    costo = cant * pu
                    tot_mats += costo
                    mats_data.append([
                        Paragraph(m["codigo"], style_td),
                        Paragraph(m["descripcion"], style_td),
                        Paragraph(m["unidad"], style_td_center),
                        Paragraph(f"{cant:,.4f}", style_td_right),
                        Paragraph(f"${pu:,.2f}", style_td_right),
                        Paragraph(f"${costo:,.2f}", style_td_right),
                    ])
            else:
                mats_data.append([Paragraph("No registra materiales directos.", style_td), "", "", "", "", ""])
                
            mats_table = Table(mats_data, colWidths=[65, 235, 45, 65, 65, 65])
            mats_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, color_border),
                ('BACKGROUND', (0,0), (-1,0), color_light_gray),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('SPAN', (0,1), (5,1)) if not detalles["materiales"] else ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            page_elements.append(mats_table)
            
            # Subtotal Materiales
            sub_mats_table = Table([
                [Paragraph("TOTAL MATERIALES:", style_total_label), Paragraph(f"${tot_mats:,.2f}", style_total_val)]
            ], colWidths=[475, 65])
            sub_mats_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('LINEABOVE', (1,0), (1,0), 1, color_navy),
                ('TOPPADDING', (0,0), (-1,-1), 3),
            ]))
            page_elements.append(sub_mats_table)
            page_elements.append(Spacer(1, 8))
            
            # --- SECCIÓN 2: EQUIPOS ---
            page_elements.append(Table([[Paragraph("2. EQUIPOS Y HERRAMIENTAS", style_sec_title)]], colWidths=[540], style=[
                ('BACKGROUND', (0,0), (-1,-1), color_navy),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            
            eqs_data = [[
                Paragraph("Código", style_th),
                Paragraph("Descripción del Equipo", style_th),
                Paragraph("Cantidad", style_th),
                Paragraph("Tarifa ($/Día)", style_th),
                Paragraph("Factor Rend.", style_th),
                Paragraph("Costo U. ($)", style_th),
            ]]
            
            tot_eqs = 0.0
            if detalles["equipos"]:
                for e in detalles["equipos"]:
                    cant = e["cantidad"]
                    tarifa = e["tarifa_dia_usd"]
                    # Costo unitario = (Cantidad * Tarifa/Dia) / Rendimiento
                    costo = (cant * tarifa) / rendimiento
                    tot_eqs += costo
                    eqs_data.append([
                        Paragraph(e["codigo"], style_td),
                        Paragraph(e["descripcion"], style_td),
                        Paragraph(f"{cant:,.2f}", style_td_right),
                        Paragraph(f"${tarifa:,.2f}", style_td_right),
                        Paragraph(f"{1.0/rendimiento:,.4f}", style_td_right),
                        Paragraph(f"${costo:,.2f}", style_td_right),
                    ])
            else:
                eqs_data.append([Paragraph("No registra equipos de obra.", style_td), "", "", "", "", ""])
                
            eqs_table = Table(eqs_data, colWidths=[65, 235, 45, 65, 65, 65])
            eqs_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, color_border),
                ('BACKGROUND', (0,0), (-1,0), color_light_gray),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('SPAN', (0,1), (5,1)) if not detalles["equipos"] else ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            page_elements.append(eqs_table)
            
            # Subtotal Equipos
            sub_eqs_table = Table([
                [Paragraph("TOTAL EQUIPOS:", style_total_label), Paragraph(f"${tot_eqs:,.2f}", style_total_val)]
            ], colWidths=[475, 65])
            sub_eqs_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('LINEABOVE', (1,0), (1,0), 1, color_navy),
                ('TOPPADDING', (0,0), (-1,-1), 3),
            ]))
            page_elements.append(sub_eqs_table)
            page_elements.append(Spacer(1, 8))
            
            # --- SECCIÓN 3: MANO DE OBRA ---
            page_elements.append(Table([[Paragraph("3. MANO DE OBRA", style_sec_title)]], colWidths=[540], style=[
                ('BACKGROUND', (0,0), (-1,-1), color_navy),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            
            mo_data = [[
                Paragraph("Código", style_th),
                Paragraph("Cargo / Mano de Obra", style_th),
                Paragraph("Cantidad", style_th),
                Paragraph("Salario ($/Día)", style_th),
                Paragraph("Factor Rend.", style_th),
                Paragraph("Costo U. ($)", style_th),
            ]]
            
            tot_mo = 0.0
            if detalles["mano_obra"]:
                for mo in detalles["mano_obra"]:
                    cant = mo["cantidad"]
                    salario = mo["salario_dia_usd"]
                    # Costo unitario = (Cantidad * Salario/Dia) / Rendimiento
                    costo = (cant * salario) / rendimiento
                    tot_mo += costo
                    mo_data.append([
                        Paragraph(mo["codigo"], style_td),
                        Paragraph(mo["descripcion"], style_td),
                        Paragraph(f"{cant:,.2f}", style_td_right),
                        Paragraph(f"${salario:,.2f}", style_td_right),
                        Paragraph(f"{1.0/rendimiento:,.4f}", style_td_right),
                        Paragraph(f"${costo:,.2f}", style_td_right),
                    ])
            else:
                mo_data.append([Paragraph("No registra mano de obra directa.", style_td), "", "", "", "", ""])
                
            mo_table = Table(mo_data, colWidths=[65, 235, 45, 65, 65, 65])
            mo_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, color_border),
                ('BACKGROUND', (0,0), (-1,0), color_light_gray),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('SPAN', (0,1), (5,1)) if not detalles["mano_obra"] else ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            page_elements.append(mo_table)
            
            # Subtotal Mano de Obra
            sub_mo_table = Table([
                [Paragraph("TOTAL MANO DE OBRA:", style_total_label), Paragraph(f"${tot_mo:,.2f}", style_total_val)]
            ], colWidths=[475, 65])
            sub_mo_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('LINEABOVE', (1,0), (1,0), 1, color_navy),
                ('TOPPADDING', (0,0), (-1,-1), 3),
            ]))
            page_elements.append(sub_mo_table)
            page_elements.append(Spacer(1, 10))
            
            # --- CÁLCULO DE COSTOS DIRECTOS E INDIRECTOS ---
            costo_directo = tot_mats + tot_eqs + tot_mo
            gastos_admin = costo_directo * 0.15   # 15% Gastos Administrativos
            utilidad = (costo_directo + gastos_admin) * 0.10  # 10% Utilidad Industrial
            precio_unitario_usd = costo_directo + gastos_admin + utilidad
            precio_unitario_ves = precio_unitario_usd * tasa_bcv
            
            resumen_data = [
                [Paragraph("<b>COSTO DIRECTO UNITARIO:</b>", style_total_label), Paragraph(f"<b>${costo_directo:,.2f}</b>", style_total_val)],
                [Paragraph("Gastos Administrativos e Indirectos (15%):", style_total_label), Paragraph(f"${gastos_admin:,.2f}", style_total_val)],
                [Paragraph("Utilidad Industrial (10%):", style_total_label), Paragraph(f"${utilidad:,.2f}", style_total_val)],
                [Paragraph("<b>PRECIO UNITARIO TOTAL (USD):</b>", style_total_label), Paragraph(f"<b>${precio_unitario_usd:,.2f}</b>", style_total_val)],
                [Paragraph("<b>PRECIO UNITARIO TOTAL (VES):</b>", style_total_label), Paragraph(f"<b>Bs. {precio_unitario_ves:,.2f}</b>", style_total_val)]
            ]
            resumen_table = Table(resumen_data, colWidths=[430, 110])
            resumen_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, color_border),
                ('BACKGROUND', (0,0), (-1,0), color_light_gray),
                ('BACKGROUND', (0,3), (-1,4), colors.HexColor("#EBF8FF")), # Celeste claro para precio final
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
            ]))
            page_elements.append(resumen_table)
            
            # Añadir página al story
            story.extend(page_elements)
            
            # Si no es el último elemento, añadir salto de página
            if index < len(items_presupuesto) - 1:
                story.append(PageBreak())
                
        # Generar el documento
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error generando PDF de APUs: {e}")
        return False
    finally:
        if logo_temp_path and os.path.exists(logo_temp_path):
            try:
                os.remove(logo_temp_path)
            except Exception:
                pass
