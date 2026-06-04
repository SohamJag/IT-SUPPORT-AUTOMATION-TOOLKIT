import os
import csv
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Import other modules to collect data
from modules.system_info import get_system_info
from modules.disk_health import get_disk_health, generate_disk_chart
from modules.network_test import run_network_diagnostic
from modules.service_checker import get_services
from modules.event_log_analyzer import get_event_logs

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

def ensure_reports_dir():
    """Ensure the reports folder exists."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

def collect_full_diagnostics():
    """Run all scans and return consolidated system state data."""
    # Generate system info
    sys_info = get_system_info()
    
    # Generate disk info
    disk_info = get_disk_health()
    
    # Generate network info
    net_info = run_network_diagnostic()
    
    # Generate service info
    svc_info = get_services()
    
    # Generate event log info (last 10 critical/error logs)
    logs_info = get_event_logs(level_filter="warning", limit=15)
    
    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        "system": sys_info,
        "disk": disk_info,
        "network": net_info,
        "services": svc_info,
        "logs": logs_info
    }

def generate_csv_report(data, filename):
    """Write diagnostic data into a single consolidated CSV report."""
    ensure_reports_dir()
    file_path = os.path.join(REPORTS_DIR, filename)
    
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header block
        writer.writerow(["=== IT SUPPORT DIAGNOSTIC REPORT ==="])
        writer.writerow(["Generated At", data["timestamp"]])
        writer.writerow([])
        
        # System Info Section
        writer.writerow(["--- SYSTEM INFORMATION ---"])
        sys = data["system"]
        writer.writerow(["Hostname", sys["hostname"]])
        writer.writerow(["Username", sys["username"]])
        writer.writerow(["Operating System", sys["os"]])
        writer.writerow(["OS Build Details", sys["os_details"]])
        writer.writerow(["CPU Model", sys["cpu"]["model"]])
        writer.writerow(["Physical/Logical Cores", f"{sys['cpu']['cores_physical']} / {sys['cpu']['cores_logical']}"])
        writer.writerow(["Total RAM (GB)", sys["ram"]["total"]])
        writer.writerow(["Used RAM (GB)", sys["ram"]["used"]])
        writer.writerow(["RAM Usage Percent", f"{sys['ram']['percent']}%"])
        writer.writerow(["Primary MAC Address", sys["mac_address"]])
        writer.writerow(["Local IP Address", sys["local_ip"]])
        writer.writerow(["Public IP Address", sys["public_ip"]])
        writer.writerow([])
        
        # Disk Section
        writer.writerow(["--- DISK STATUS ---"])
        writer.writerow(["Device", "Mountpoint", "Total (GB)", "Used (GB)", "Free (GB)", "Usage %", "Health Status"])
        for drive in data["disk"]:
            writer.writerow([
                drive["device"], drive["mountpoint"], drive["total"], 
                drive["used"], drive["free"], f"{drive['percent']}%", drive["status"]
            ])
        writer.writerow([])
        
        # Network Section
        writer.writerow(["--- NETWORK CONNECTIVITY ---"])
        net = data["network"]
        writer.writerow(["Internet Status", net["internet"]["status"]])
        writer.writerow(["DNS Resolution", net["dns"]["status"]])
        writer.writerow(["Google Ping Test", net["ping"]["status"]])
        writer.writerow(["Default Gateway IP", net["gateway"]["ip"]])
        writer.writerow(["Gateway Ping Test", net["gateway"]["status"]])
        writer.writerow([])
        
        # Services Section
        writer.writerow(["--- SERVICES HEALTH ---"])
        writer.writerow(["Service Name", "Display Name", "Current Status"])
        for svc in data["services"]:
            writer.writerow([svc["name"], svc["display"], svc["status"]])
        writer.writerow([])
        
        # Event Logs Section
        writer.writerow(["--- SYSTEM EVENT LOGS ---"])
        writer.writerow(["Timestamp", "Severity", "Source", "Event ID", "Message Summary"])
        for log in data["logs"]:
            writer.writerow([
                log["timestamp"], log["level"], log["source"], 
                log["event_id"], log["message"]
            ])
            
    # Calculate a short summary
    critical_services = len([s for s in data["services"] if s["status"] != "Running"])
    critical_drives = len([d for d in data["disk"] if d["status"] == "Critical"])
    net_ok = "Connected" if data["network"]["internet"]["success"] else "Disconnected"
    summary = f"OS: {sys['os']}, Disk Alerts: {critical_drives}, Services Stopped: {critical_services}, Internet: {net_ok}"
    
    return file_path, summary

def generate_pdf_report(data, filename, static_dir):
    """Compile styled PDF report with custom tables, paragraphs, and disk usage charts."""
    ensure_reports_dir()
    file_path = os.path.join(REPORTS_DIR, filename)
    
    # 1. Generate the disk usage chart image first to embed it
    chart_filename = generate_disk_chart(data["disk"], static_dir)
    chart_path = os.path.join(static_dir, chart_filename) if chart_filename else None
    
    # 2. Setup PDF document layout
    doc = SimpleDocTemplate(
        file_path, 
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Create custom dark-mode styled paragraphs
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#10b981'), # Emerald Green
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#0f766e'), # Deep teal/green
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor('#1f2937'),
        leading=13
    )

    bold_body_style = ParagraphStyle(
        'BoldBodyText',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Header Title and metadata
    story.append(Paragraph("IT Support Diagnostic Report", title_style))
    story.append(Paragraph(f"<b>System Support Automation Agent</b> | Generated: {data['timestamp']}", meta_style))
    story.append(Spacer(1, 8))
    
    # --- SECTION 1: System Info ---
    story.append(Paragraph("1. System Information", h2_style))
    sys = data["system"]
    
    sys_table_data = [
        [Paragraph("Hostname", bold_body_style), Paragraph(sys["hostname"], body_style), Paragraph("Local IP Address", bold_body_style), Paragraph(sys["local_ip"], body_style)],
        [Paragraph("Username", bold_body_style), Paragraph(sys["username"], body_style), Paragraph("Public IP Address", bold_body_style), Paragraph(sys["public_ip"], body_style)],
        [Paragraph("Operating System", bold_body_style), Paragraph(sys["os"], body_style), Paragraph("MAC Address", bold_body_style), Paragraph(sys["mac_address"], body_style)],
        [Paragraph("CPU Model", bold_body_style), Paragraph(sys["cpu"]["model"], body_style), Paragraph("Logical Cores", bold_body_style), Paragraph(str(sys["cpu"]["cores_logical"]), body_style)],
        [Paragraph("Total Memory", bold_body_style), Paragraph(f"{sys['ram']['total']} GB", body_style), Paragraph("Memory Usage", bold_body_style), Paragraph(f"{sys['ram']['percent']}%", body_style)],
    ]
    
    t1 = Table(sys_table_data, colWidths=[100, 165, 100, 165])
    t1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f9fafb')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f9fafb')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))
    
    # --- SECTION 2: Disk Status ---
    story.append(Paragraph("2. Disk Health Status", h2_style))
    disk_table_data = [
        [Paragraph("<b>Drive</b>", body_style), Paragraph("<b>Mount</b>", body_style), Paragraph("<b>Total (GB)</b>", body_style), Paragraph("<b>Used (GB)</b>", body_style), Paragraph("<b>Free (GB)</b>", body_style), Paragraph("<b>Usage %</b>", body_style), Paragraph("<b>Status</b>", body_style)]
    ]
    for d in data["disk"]:
        status_para = Paragraph(f"<font color='red'><b>{d['status']}</b></font>" if d['status'] == 'Critical' else f"<b>{d['status']}</b>", body_style)
        disk_table_data.append([
            Paragraph(d["device"], body_style), Paragraph(d["mountpoint"], body_style),
            Paragraph(str(d["total"]), body_style), Paragraph(str(d["used"]), body_style),
            Paragraph(str(d["free"]), body_style), Paragraph(f"{d['percent']}%", body_style),
            status_para
        ])
    t2 = Table(disk_table_data, colWidths=[90, 70, 75, 75, 75, 65, 80])
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    story.append(t2)
    
    # Add embedded chart if exists
    if chart_path and os.path.exists(chart_path):
        story.append(Spacer(1, 10))
        # Resize chart image to fit nicely in report
        chart_img = Image(chart_path, width=280, height=210)
        chart_img.hAlign = 'CENTER'
        story.append(chart_img)
        
    story.append(Spacer(1, 10))
    
    # --- SECTION 3: Network Diagnostics ---
    story.append(Paragraph("3. Network Diagnostics", h2_style))
    net = data["network"]
    
    net_table_data = [
        [Paragraph("<b>Diagnostic Test</b>", body_style), Paragraph("<b>Result / Latency</b>", body_style), Paragraph("<b>Status</b>", body_style)],
        [Paragraph("Internet Connection", body_style), Paragraph(net["internet"]["status"], body_style), Paragraph("PASSED" if net["internet"]["success"] else "FAILED", bold_body_style)],
        [Paragraph("DNS Resolution", body_style), Paragraph(net["dns"]["status"], body_style), Paragraph("PASSED" if net["dns"]["success"] else "FAILED", bold_body_style)],
        [Paragraph("Ping Test (google.com)", body_style), Paragraph(net["ping"]["status"], body_style), Paragraph("PASSED" if net["ping"]["success"] else "FAILED", bold_body_style)],
        [Paragraph(f"Gateway Reachability ({net['gateway']['ip']})", body_style), Paragraph(net["gateway"]["status"], body_style), Paragraph("PASSED" if net["gateway"]["success"] else "FAILED", bold_body_style)]
    ]
    t3 = Table(net_table_data, colWidths=[180, 250, 100])
    t3.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 12))
    
    # --- SECTION 4: Services Health ---
    story.append(Paragraph("4. Essential Services Health", h2_style))
    svc_table_data = [
        [Paragraph("<b>Service Identifier</b>", body_style), Paragraph("<b>Display Name</b>", body_style), Paragraph("<b>Status</b>", body_style)]
    ]
    for s in data["services"]:
        status_para = Paragraph(f"<font color='green'><b>{s['status']}</b></font>" if s['status'] == 'Running' else f"<font color='grey'>{s['status']}</font>", body_style)
        svc_table_data.append([
            Paragraph(s["name"], body_style), Paragraph(s["display"], body_style), status_para
        ])
    t4 = Table(svc_table_data, colWidths=[140, 260, 130])
    t4.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t4)
    story.append(Spacer(1, 12))
    
    # --- SECTION 5: Event Logs (Compact/Wrap paragraphs) ---
    story.append(Paragraph("5. Critical & Warning Log Events", h2_style))
    log_table_data = [
        [Paragraph("<b>Timestamp</b>", body_style), Paragraph("<b>Level</b>", body_style), Paragraph("<b>Source</b>", body_style), Paragraph("<b>ID</b>", body_style), Paragraph("<b>Message Summary</b>", body_style)]
    ]
    for l in data["logs"][:8]: # Keep PDF report compact
        lvl_color = "red" if l["level"].lower() in ["error", "critical"] else "orange"
        level_para = Paragraph(f"<font color='{lvl_color}'><b>{l['level']}</b></font>", body_style)
        
        # Wrap long messages in paragraphs for auto-wrapping in tables
        msg_para = Paragraph(l["message"], ParagraphStyle('Msg', parent=body_style, fontSize=8.5, leading=10))
        
        log_table_data.append([
            Paragraph(l["timestamp"], body_style),
            level_para,
            Paragraph(l["source"], body_style),
            Paragraph(str(l["event_id"]), body_style),
            msg_para
        ])
    t5 = Table(log_table_data, colWidths=[110, 55, 95, 40, 230])
    t5.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t5)
    
    # Build Document
    doc.build(story)
    
    # Clean up chart file so static stays clean
    if chart_path and os.path.exists(chart_path):
        try:
            # We don't necessarily have to delete it if we want to show it in UI, but if it is transient, we can delete.
            # Let's keep it in static directory so the page can show it!
            pass
        except Exception:
            pass
            
    # Calculate brief summary
    critical_services = len([s for s in data["services"] if s["status"] != "Running"])
    critical_drives = len([d for d in data["disk"] if d["status"] == "Critical"])
    net_ok = "Connected" if data["network"]["internet"]["success"] else "Disconnected"
    summary = f"OS: {sys['os']}, Disk Alerts: {critical_drives}, Services Stopped: {critical_services}, Internet: {net_ok}"
    
    return file_path, summary
