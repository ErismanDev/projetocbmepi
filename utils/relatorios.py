from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import pandas as pd
import io
from datetime import datetime

def gerar_pdf_frequencia(dados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("Relatório de Frequência", title_style))
    
    # Data de geração
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    )
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 20))
    
    # Tabela
    data = [['Aluno', 'Total Aulas', 'Presenças', 'Faltas', 'Justificadas', 'Frequência (%)']]
    for aluno_id, info in dados.items():
        data.append([
            info['aluno'],
            str(info['total_aulas']),
            str(info['presencas']),
            str(info['faltas']),
            str(info['justificadas']),
            f"{info['frequencia']:.2f}%"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

def gerar_excel_frequencia(dados):
    df = pd.DataFrame.from_dict(dados, orient='index')
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Frequência')
        
        # Formatação
        workbook = writer.book
        worksheet = writer.sheets['Frequência']
        
        # Formato para porcentagem
        percent_format = workbook.add_format({'num_format': '0.00%'})
        worksheet.set_column('F:F', None, percent_format)
        
        # Formato para cabeçalho
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return output

def gerar_csv_frequencia(dados):
    df = pd.DataFrame.from_dict(dados, orient='index')
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8'))

def gerar_pdf_desempenho(dados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("Relatório de Desempenho", title_style))
    
    # Data de geração
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    )
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 20))
    
    # Tabela
    data = [['Aluno', 'Média', 'Frequência', 'Total Avaliações', 'Status']]
    for info in dados:
        data.append([
            info['aluno'],
            f"{info['media']:.1f}",
            f"{info['frequencia']:.1f}%",
            str(info['total_avaliacoes']),
            info['status']
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

def gerar_excel_desempenho(dados):
    df = pd.DataFrame(dados)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Desempenho')
        
        # Formatação
        workbook = writer.book
        worksheet = writer.sheets['Desempenho']
        
        # Formato para porcentagem
        percent_format = workbook.add_format({'num_format': '0.00%'})
        worksheet.set_column('C:C', None, percent_format)
        
        # Formato para cabeçalho
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return output

def gerar_csv_desempenho(dados):
    df = pd.DataFrame(dados)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8'))

def gerar_pdf_atividades(dados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("Relatório de Atividades", title_style))
    
    # Data de geração
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    )
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 20))
    
    # Tabela
    data = [['Título', 'Data', 'Turma', 'Categoria', 'Status', 'Participantes']]
    for info in dados:
        data.append([
            info['titulo'],
            info['data'],
            info['turma'],
            info['categoria'],
            info['status'],
            str(info['participantes'])
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

def gerar_excel_atividades(dados):
    df = pd.DataFrame(dados)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Atividades')
        
        # Formatação
        workbook = writer.book
        worksheet = writer.sheets['Atividades']
        
        # Formato para cabeçalho
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return output

def gerar_csv_atividades(dados):
    df = pd.DataFrame(dados)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8'))

def gerar_pdf_certificados(dados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("Relatório de Certificados", title_style))
    
    # Data de geração
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    )
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 20))
    
    # Tabela
    data = [['Código', 'Aluno', 'Turma', 'Data Emissão', 'Data Conclusão', 'Status']]
    for info in dados:
        data.append([
            info['codigo'],
            info['aluno'],
            info['turma'],
            info['data_emissao'],
            info['data_conclusao'],
            info['status']
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

def gerar_excel_certificados(dados):
    df = pd.DataFrame(dados)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Certificados')
        
        # Formatação
        workbook = writer.book
        worksheet = writer.sheets['Certificados']
        
        # Formato para cabeçalho
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return output

def gerar_csv_certificados(dados):
    df = pd.DataFrame(dados)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8')) 