from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os

def generate_report(logs, stats, period='Daily'):
    os.makedirs('static', exist_ok=True)
    fname = f"static/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(fname, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    t1 = ParagraphStyle('t1', fontSize=22, textColor=colors.HexColor('#0a0a1a'),
                         alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=6)
    t2 = ParagraphStyle('t2', fontSize=10, textColor=colors.HexColor('#007744'),
                         alignment=TA_CENTER, fontName='Helvetica', spaceAfter=4)
    t3 = ParagraphStyle('t3', fontSize=8,  textColor=colors.grey,
                         alignment=TA_CENTER, fontName='Helvetica')
    th = ParagraphStyle('th', fontSize=13, fontName='Helvetica-Bold',
                         textColor=colors.HexColor('#0a0a1a'), spaceBefore=12, spaceAfter=8)

    story += [
        Paragraph("CyberShield — Security Report", t1),
        Paragraph(f"AI-Based Cyber Attack Detection | {period} Report", t2),
        Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", t3),
        HRFlowable(width="100%", thickness=2, color=colors.HexColor('#00aa55'), spaceAfter=14),
        Paragraph("Executive Summary", th),
    ]

    sum_data = [
        ['Metric','Value','Status'],
        ['Total Connections', str(stats.get('total',0)), 'Monitored'],
        ['Attacks Detected',  str(stats.get('attacks',0)), 'Alert' if stats.get('attacks',0)>0 else 'Safe'],
        ['High Risk Events',  str(stats.get('high_risk',0)), 'Critical' if stats.get('high_risk',0)>0 else 'None'],
        ['Normal Traffic',    str(stats.get('normal',0)), 'Clean'],
    ]
    t = Table(sum_data, colWidths=[8*cm,4*cm,5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0a0a1a')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#00ff88')),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f8f8f8'),colors.white]),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('FONTSIZE',(0,0),(-1,-1),9),('PADDING',(0,0),(-1,-1),8),
    ]))
    story += [t, Spacer(1,0.4*cm), Paragraph("Attack Breakdown", th)]

    by_type = stats.get('by_type',[])
    if by_type:
        td = [['Attack Type','Count']]
        for row in by_type:
            td.append([row['attack_type'].replace('_',' ').upper(), str(row['count'])])
        t2t = Table(td, colWidths=[10*cm, 7*cm])
        t2t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#fff5f5'),colors.white]),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dddddd')),
            ('FONTSIZE',(0,0),(-1,-1),9),('PADDING',(0,0),(-1,-1),7),
        ]))
        story.append(t2t)

    story += [Spacer(1,0.4*cm), Paragraph("Recent Logs (Last 15)", th)]
    if logs:
        ld = [['Time','Source IP','Attack','Risk','Score']]
        for l in logs[:15]:
            ld.append([str(l.get('timestamp',''))[-8:], str(l.get('src_ip','-')),
                       str(l.get('attack_type','-')).upper(), str(l.get('risk_level','-')),
                       str(l.get('risk_score','-'))])
        t3t = Table(ld, colWidths=[3*cm,4.5*cm,4.5*cm,2.5*cm,2.5*cm])
        t3t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16213e')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#e94560')),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f0ff'),colors.white]),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#cccccc')),
            ('FONTSIZE',(0,0),(-1,-1),8),('PADDING',(0,0),(-1,-1),5),
        ]))
        story.append(t3t)

    story += [Spacer(1,1*cm), HRFlowable(width="100%",thickness=1,color=colors.HexColor('#cccccc')),
              Paragraph("CyberShield | Rajarambapu Institute of Technology, Sangli | Confidential",
                        ParagraphStyle('f',fontSize=7,textColor=colors.grey,
                                       alignment=TA_CENTER,spaceBefore=8))]
    doc.build(story)
    return fname