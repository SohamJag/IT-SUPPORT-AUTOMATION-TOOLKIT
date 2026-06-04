import os
import time
import platform
from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for

# Import local modules
from modules.database import init_db, add_report, get_reports, delete_report
from modules.system_info import get_system_info
from modules.disk_health import get_disk_health, generate_disk_chart
from modules.network_test import run_network_diagnostic, get_default_gateway
from modules.service_checker import get_services, toggle_service
from modules.password_generator import generate_password, assess_strength
from modules.event_log_analyzer import get_event_logs, export_logs_to_csv
from modules.process_monitor import get_running_processes, kill_process
from modules.software_inventory import get_installed_software
from modules.report_generator import collect_full_diagnostics, generate_csv_report, generate_pdf_report

app = Flask(__name__)

# Ensure reports directory exists
REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# Initialize database on start
init_db()

# Context processor to inject global variables into templates (e.g. for sidebar)
@app.context_processor
def inject_global_vars():
    # Detect operating system details
    os_name = platform.system()
    os_release = platform.release()
    
    # Simple username retrieval
    username = os.environ.get("USER") or os.environ.get("USERNAME") or "System Engineer"
    
    return {
        "session_username": username,
        "session_os": f"{os_name} {os_release}"
    }

# ----------------------------------------------------
# Page Rendering Routes
# ----------------------------------------------------

@app.route('/')
def index():
    # Get basic details for dashboard
    system = get_system_info()
    
    # Calculate disk status summary
    disk_data = get_disk_health()
    warning_drives = [d for d in disk_data if d["status"] == "Critical"]
    disk_status = "Critical Space Alert!" if warning_drives else "Healthy"
    
    # Get services status counts
    services_list = get_services()
    services_total_count = len(services_list)
    services_running_count = len([s for s in services_list if s["status"] == "Running"])
    
    # Get quick network state (light check, no deep ping to avoid blocking load)
    network_summary = {
        "internet": {"status": "Connected" if system["public_ip"] != "Offline" else "Offline", "success": system["public_ip"] != "Offline"},
        "ping": {"latency": None},
        "gateway": {"ip": get_default_gateway()}
    }
    
    return render_template(
        'index.html',
        active_page='dashboard',
        system=system,
        disk_status=disk_status,
        services_total_count=services_total_count,
        services_running_count=services_running_count,
        network=network_summary
    )

@app.route('/system_info')
def system_info_route():
    info = get_system_info()
    gateway_ip = get_default_gateway()
    return render_template('system_info.html', active_page='system_info', info=info, gateway_ip=gateway_ip)

@app.route('/disk_health')
def disk_health_route():
    drives = get_disk_health()
    
    # Generate matplotlib chart
    static_dir = os.path.join(app.root_path, "static")
    chart_file = generate_disk_chart(drives, static_dir)
    
    warning_drives_count = len([d for d in drives if d["status"] == "Critical"])
    
    # Cache buster ensures browser fetches new image on reload instead of caching
    cache_buster = int(time.time())
    
    return render_template(
        'disk_health.html',
        active_page='disk_health',
        drives=drives,
        chart_file=chart_file,
        warning_drives_count=warning_drives_count,
        cache_buster=cache_buster
    )

@app.route('/network_test')
def network_test_route():
    # Provide a placeholder initial network dict. Run Diagnostics button will populate via Ajax.
    init_net = {
        "internet": {"status": "Ready", "success": True},
        "dns": {"status": "Ready", "success": True},
        "ping": {"status": "Ready", "success": True},
        "gateway": {"ip": get_default_gateway(), "status": "Ready", "success": True}
    }
    return render_template('network_test.html', active_page='network_test', network=init_net)

@app.route('/service_checker')
def service_checker_route():
    services = get_services()
    return render_template('service_checker.html', active_page='service_checker', services=services)

@app.route('/process_monitor')
def process_monitor_route():
    # Only fetch top 80 processes to prevent huge HTML payload
    processes = get_running_processes()[:80]
    return render_template('process_monitor.html', active_page='process_monitor', processes=processes)

@app.route('/software_inventory')
def software_inventory_route():
    software = get_installed_software()
    return render_template('software_inventory.html', active_page='software_inventory', software=software)

@app.route('/password_generator')
def password_generator_route():
    return render_template('password_generator.html', active_page='password_generator')

@app.route('/event_log_analyzer')
def event_log_analyzer_route():
    # Initial load: last 50 warning/critical logs
    logs = get_event_logs(level_filter="warning", limit=50)
    return render_template('event_log_analyzer.html', active_page='event_log_analyzer', logs=logs)

@app.route('/reports')
def reports_route():
    # Get historical list from SQLite DB
    reports = get_reports()
    return render_template('reports.html', active_page='reports', reports=reports)

# ----------------------------------------------------
# REST API Endpoints
# ----------------------------------------------------

@app.route('/api/network_check', methods=['GET'])
def api_network_check():
    results = run_network_diagnostic()
    return jsonify(results)

@app.route('/api/generate_password', methods=['POST'])
def api_generate_password():
    data = request.json or {}
    length = data.get("length", 12)
    sym = data.get("symbols", True)
    num = data.get("numbers", True)
    upper = data.get("uppercase", True)
    lower = data.get("lowercase", True)
    
    password = generate_password(length, sym, num, upper, lower)
    strength, strength_class, strength_pct = assess_strength(password)
    
    return jsonify({
        "password": password,
        "strength": strength,
        "strength_class": strength_class,
        "strength_pct": strength_pct
    })

@app.route('/api/service/toggle', methods=['POST'])
def api_service_toggle():
    data = request.json or {}
    service_name = data.get("service_name")
    action = data.get("action")
    
    if not service_name or not action:
        return jsonify({"success": False, "message": "Missing parameters."}), 400
        
    success, message = toggle_service(service_name, action)
    return jsonify({"success": success, "message": message})

@app.route('/api/process/kill', methods=['POST'])
def api_process_kill():
    data = request.json or {}
    pid = data.get("pid")
    
    if pid is None:
        return jsonify({"success": False, "message": "Missing PID parameter."}), 400
        
    success, message = kill_process(pid)
    return jsonify({"success": success, "message": message})

@app.route('/api/event_logs/query', methods=['GET'])
def api_event_logs_query():
    level = request.args.get("level")
    search = request.args.get("search")
    
    logs = get_event_logs(level_filter=level, search_query=search, limit=100)
    return jsonify(logs)

@app.route('/api/event_logs/export', methods=['GET'])
def api_event_logs_export():
    level = request.args.get("level")
    search = request.args.get("search")
    
    logs = get_event_logs(level_filter=level, search_query=search, limit=500)
    csv_data = export_logs_to_csv(logs)
    
    # Return as an inline CSV download stream
    from io import BytesIO
    buffer = BytesIO()
    buffer.write(csv_data.encode('utf-8'))
    buffer.seek(0)
    
    filename = f"event_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="text/csv"
    )

@app.route('/api/generate_report', methods=['POST'])
def api_generate_report():
    data = request.json or {}
    fmt = data.get("format", "pdf").lower()
    
    # 1. Gather all system diagnostics
    diagnostics = collect_full_diagnostics()
    
    # Generate unique filenames
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if fmt == "csv":
            filename = f"support_report_{timestamp_str}.csv"
            file_path, summary = generate_csv_report(diagnostics, filename)
        else: # Default PDF
            filename = f"support_report_{timestamp_str}.pdf"
            static_dir = os.path.join(app.root_path, "static")
            file_path, summary = generate_pdf_report(diagnostics, filename, static_dir)
            
        # 2. Add to SQLite history log database
        report_id = add_report(
            report_name=filename,
            file_path=file_path,
            format_type=fmt.upper(),
            summary=summary
        )
        
        return jsonify({
            "success": True,
            "report_id": report_id,
            "filename": filename
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to build document. Error: {str(e)}"}), 500

@app.route('/reports/download/<int:report_id>', methods=['GET'])
def download_report_route(report_id):
    # Find report in archive database
    reports = get_reports()
    target_report = None
    for r in reports:
        if r["id"] == report_id:
            target_report = r
            break
            
    if not target_report or not os.path.exists(target_report["file_path"]):
        return "File Not Found: The requested report document does not exist on disk.", 404
        
    return send_file(
        target_report["file_path"],
        as_attachment=True,
        download_name=target_report["report_name"]
    )

@app.route('/reports/delete/<int:report_id>', methods=['GET'])
def delete_report_route(report_id):
    # Delete from DB and get file path
    file_path = delete_report(report_id)
    
    # Try deleting actual file on disk
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
            
    return redirect(url_for('reports_route'))

# Import datetime inside context for dynamic log titles
import datetime

if __name__ == '__main__':
    # Start flask app local server
    app.run(debug=True, host='127.0.0.1', port=5000)
